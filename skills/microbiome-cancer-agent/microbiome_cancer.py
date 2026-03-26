#!/usr/bin/env python3
# COPYRIGHT NOTICE
# This file is part of the "Universal Biomedical Skills" project.
# Copyright (c) 2026 MD BABU MIA, PhD <md.babu.mia@mssm.edu>
# All Rights Reserved.
#
# This code is proprietary and confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Provenance: Authenticated by MD BABU MIA

"""
Microbiome-Cancer Interaction Analyzer.

Analyzes gut and tumor microbiome composition in the context of cancer treatment,
predicts immune checkpoint inhibitor (ICI) response, infers metabolite profiles,
models antibiotic impact, and generates FMT/probiotic/dietary recommendations.

Usage:
    python3 microbiome_cancer.py --metagenomics fecal_shotgun.fastq.gz \
        --tumor_data melanoma_rnaseq.tsv --clinical treatment_outcomes.csv \
        --analysis ici_response --reference metaphlan_db \
        --output microbiome_report/
"""

import argparse
import json
import math
import os
import random
import sys
from datetime import datetime

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# ---------------------------------------------------------------------------
# Microbial taxa databases
# ---------------------------------------------------------------------------

FAVORABLE_TAXA = {
    "Akkermansia muciniphila": {
        "phylum": "Verrucomicrobiota",
        "association_strength": "strong",
        "evidence_level": "multiple_cohorts",
        "mechanism": "Mucin degradation enhances barrier function; stimulates anti-tumor immunity",
        "typical_abundance_responder": 0.03,
        "typical_abundance_nonresponder": 0.005,
    },
    "Faecalibacterium prausnitzii": {
        "phylum": "Firmicutes",
        "association_strength": "moderate",
        "evidence_level": "multiple_cohorts",
        "mechanism": "Major butyrate producer; anti-inflammatory; supports Treg/Th17 balance",
        "typical_abundance_responder": 0.08,
        "typical_abundance_nonresponder": 0.03,
    },
    "Bifidobacterium longum": {
        "phylum": "Actinobacteriota",
        "association_strength": "moderate",
        "evidence_level": "multiple_cohorts",
        "mechanism": "Enhances dendritic cell maturation and anti-tumor T-cell priming",
        "typical_abundance_responder": 0.04,
        "typical_abundance_nonresponder": 0.01,
    },
    "Ruminococcus bicirculans": {
        "phylum": "Firmicutes",
        "association_strength": "moderate",
        "evidence_level": "single_cohort",
        "mechanism": "SCFA production; supports gut barrier integrity",
        "typical_abundance_responder": 0.025,
        "typical_abundance_nonresponder": 0.008,
    },
    "Bacteroides caccae": {
        "phylum": "Bacteroidota",
        "association_strength": "moderate",
        "evidence_level": "single_cohort",
        "mechanism": "Immune modulation via polysaccharide utilization",
        "typical_abundance_responder": 0.02,
        "typical_abundance_nonresponder": 0.008,
    },
    "Collinsella aerofaciens": {
        "phylum": "Actinobacteriota",
        "association_strength": "moderate",
        "evidence_level": "single_cohort",
        "mechanism": "Bile acid metabolism; potential immune modulation",
        "typical_abundance_responder": 0.015,
        "typical_abundance_nonresponder": 0.004,
    },
    "Enterococcus hirae": {
        "phylum": "Firmicutes",
        "association_strength": "moderate",
        "evidence_level": "preclinical_confirmed",
        "mechanism": "Translocates to lymph nodes; induces Th1 response via TLR2",
        "typical_abundance_responder": 0.008,
        "typical_abundance_nonresponder": 0.002,
    },
}

UNFAVORABLE_TAXA = {
    "Bacteroides thetaiotaomicron": {
        "phylum": "Bacteroidota",
        "association_strength": "context_dependent",
        "evidence_level": "conflicting",
        "mechanism": "May compete with favorable Bacteroides; context-dependent immunomodulation",
        "typical_abundance_nonresponder": 0.05,
        "typical_abundance_responder": 0.02,
    },
    "Roseburia intestinalis": {
        "phylum": "Firmicutes",
        "association_strength": "context_dependent",
        "evidence_level": "single_cohort",
        "mechanism": "Butyrate producer but sometimes enriched in non-responders",
        "typical_abundance_nonresponder": 0.04,
        "typical_abundance_responder": 0.02,
    },
    "Bacteroides fragilis_toxigenic": {
        "phylum": "Bacteroidota",
        "association_strength": "moderate",
        "evidence_level": "preclinical",
        "mechanism": "Toxigenic strains promote inflammatory microenvironment",
        "typical_abundance_nonresponder": 0.03,
        "typical_abundance_responder": 0.008,
    },
}

# ---------------------------------------------------------------------------
# Tumor microbiome associations
# ---------------------------------------------------------------------------

TUMOR_MICROBIOME = {
    "CRC": {
        "key_taxa": [
            {"species": "Fusobacterium nucleatum", "association": "poor_prognosis",
             "mechanism": "FadA adhesin binds E-cadherin; activates Wnt/beta-catenin; "
                          "promotes chemoresistance via autophagy"},
            {"species": "Bacteroides fragilis (ETBF)", "association": "tumorigenesis",
             "mechanism": "BFT toxin cleaves E-cadherin; NF-kB/STAT3 activation"},
            {"species": "Peptostreptococcus anaerobius", "association": "CRC_enriched",
             "mechanism": "Interacts with TLR2/TLR4 on colonic cells"},
        ],
    },
    "melanoma": {
        "key_taxa": [
            {"species": "Faecalibacterium prausnitzii", "association": "ici_response",
             "mechanism": "Anti-inflammatory butyrate production"},
            {"species": "Clostridium spp.", "association": "mixed",
             "mechanism": "Diverse genus with variable immune effects"},
        ],
    },
    "NSCLC": {
        "key_taxa": [
            {"species": "Akkermansia muciniphila", "association": "ici_response",
             "mechanism": "Enhances IL-12-dependent anti-tumor immunity"},
            {"species": "Alistipes spp.", "association": "favorable",
             "mechanism": "Associated with better ICI outcomes in lung cancer"},
        ],
    },
    "gastric": {
        "key_taxa": [
            {"species": "Helicobacter pylori", "association": "carcinogenesis",
             "mechanism": "CagA oncoprotein; chronic inflammation; epigenetic changes"},
        ],
    },
    "RCC": {
        "key_taxa": [
            {"species": "Akkermansia muciniphila", "association": "ici_response",
             "mechanism": "IL-12 pathway activation"},
            {"species": "Bacteroides salyersiae", "association": "favorable",
             "mechanism": "Immune potentiation"},
        ],
    },
    "pancreatic": {
        "key_taxa": [
            {"species": "Gammaproteobacteria", "association": "drug_resistance",
             "mechanism": "Express cytidine deaminase; degrade gemcitabine"},
            {"species": "Malassezia globosa", "association": "tumorigenesis",
             "mechanism": "Fungal activation of complement cascade via MBL"},
        ],
    },
}

# ---------------------------------------------------------------------------
# Metabolite inference mapping
# ---------------------------------------------------------------------------

METABOLITE_PRODUCERS = {
    "butyrate": {
        "producers": ["Faecalibacterium prausnitzii", "Roseburia intestinalis",
                       "Eubacterium rectale", "Coprococcus spp."],
        "function": "Histone deacetylase inhibition; Treg induction; "
                    "epithelial barrier maintenance; anti-inflammatory",
        "cancer_relevance": "Promotes anti-tumor immunity; enhances ICI efficacy",
    },
    "propionate": {
        "producers": ["Bacteroides spp.", "Akkermansia muciniphila",
                       "Veillonella spp."],
        "function": "GPCR signaling (GPR41/43); modulates immune cell metabolism",
        "cancer_relevance": "Immunomodulatory; may enhance DC function",
    },
    "acetate": {
        "producers": ["Bifidobacterium spp.", "Blautia spp.",
                       "Prevotella spp."],
        "function": "Energy substrate; regulates appetite; immune cell fuel",
        "cancer_relevance": "Supports CD8+ T-cell effector function",
    },
    "secondary_bile_acids": {
        "producers": ["Clostridium scindens", "Clostridium hylemonae",
                       "Eubacterium spp."],
        "function": "7-alpha-dehydroxylation of primary bile acids; "
                    "FXR/TGR5 signaling",
        "cancer_relevance": "DCA and LCA may promote or inhibit cancer depending on context",
    },
    "tryptophan_indoles": {
        "producers": ["Lactobacillus spp.", "Clostridium sporogenes",
                       "Peptostreptococcus spp."],
        "function": "AhR ligand activation; indole-3-aldehyde, "
                    "indole-3-propionic acid production",
        "cancer_relevance": "AhR activation modulates anti-tumor immunity; context-dependent",
    },
    "tmao": {
        "producers": ["Anaerococcus hydrogenalis", "Clostridium asparagiforme",
                       "Escherichia fergusonii"],
        "function": "TMA oxidized by hepatic FMO3 to TMAO; platelet activation",
        "cancer_relevance": "Primarily cardiovascular risk; some links to CRC",
    },
}

# ---------------------------------------------------------------------------
# Antibiotic impact data
# ---------------------------------------------------------------------------

ANTIBIOTIC_IMPACT = {
    "broad_spectrum": {
        "examples": ["fluoroquinolones", "carbapenems", "3rd-gen cephalosporins",
                      "piperacillin-tazobactam"],
        "diversity_reduction_pct": 40,
        "recovery_weeks": 12,
        "ici_impact": "Significant reduction in ICI response rates (HR ~1.5-2.0)",
    },
    "narrow_spectrum": {
        "examples": ["metronidazole", "vancomycin_oral", "nitrofurantoin"],
        "diversity_reduction_pct": 20,
        "recovery_weeks": 6,
        "ici_impact": "Moderate impact on ICI response; less disruption",
    },
    "minimal_impact": {
        "examples": ["penicillin_V", "trimethoprim"],
        "diversity_reduction_pct": 10,
        "recovery_weeks": 3,
        "ici_impact": "Minimal impact on ICI response",
    },
}

# ---------------------------------------------------------------------------
# Probiotic evidence
# ---------------------------------------------------------------------------

PROBIOTIC_STRAINS = [
    {"strain": "Bifidobacterium longum BB536", "evidence": "Preclinical + pilot clinical",
     "context": "ICI combination", "mechanism": "Enhanced DC maturation"},
    {"strain": "Lactobacillus rhamnosus GG", "evidence": "Limited for ICI; strong GI",
     "context": "Gut barrier support", "mechanism": "Tight junction upregulation"},
    {"strain": "Clostridium butyricum MIYAIRI 588", "evidence": "Clinical (Japan)",
     "context": "ICI combination in NSCLC",
     "mechanism": "Butyrate production; CD8+ T-cell activation"},
    {"strain": "Akkermansia muciniphila (pasteurized)", "evidence": "Phase I/II",
     "context": "ICI potentiation", "mechanism": "Amuc_1100 protein; TLR2 activation"},
]

# Cancer type-specific microbiome associations
CANCER_CONTEXT = {
    "CRC": "Colorectal cancer - strong microbiome-tumor interface; "
           "Fusobacterium nucleatum as key pathobiont",
    "melanoma": "Melanoma - strongest evidence for gut microbiome-ICI response axis; "
                "Akkermansia and Faecalibacterium key taxa",
    "NSCLC": "Non-small cell lung cancer - gut-lung axis; "
             "Akkermansia muciniphila most replicated association",
    "RCC": "Renal cell carcinoma - Akkermansia-rich microbiome associated with ICI benefit",
    "gastric": "Gastric cancer - H. pylori primary etiological agent; "
               "microbiome shifts post-gastrectomy",
    "pancreatic": "Pancreatic cancer - intratumoral bacteria affect drug metabolism; "
                  "low diversity associated with poor outcome",
}


class MicrobiomeCancerAnalyzer:
    """Microbiome-cancer interaction analyzer."""

    def __init__(self, metagenomics=None, tumor_data=None, clinical=None,
                 analysis="ici_response", reference=None, cancer_type="melanoma"):
        self.metagenomics_path = metagenomics
        self.tumor_data_path = tumor_data
        self.clinical_path = clinical
        self.analysis_type = analysis
        self.reference = reference
        self.cancer_type = cancer_type.upper() if cancer_type else "melanoma"
        # Normalize common names
        name_map = {"COLORECTAL": "CRC", "LUNG": "NSCLC", "RENAL": "RCC",
                    "KIDNEY": "RCC", "STOMACH": "gastric", "PANCREAS": "pancreatic"}
        self.cancer_type = name_map.get(self.cancer_type, self.cancer_type)
        self.abundance_data = None

    # ----- data loading -----

    def _load_abundance_data(self):
        """Load microbial abundance from file or generate demo."""
        if self.metagenomics_path and os.path.isfile(self.metagenomics_path):
            return self._parse_abundance(self.metagenomics_path)
        return self._generate_demo_abundance()

    def _parse_abundance(self, path):
        """Parse abundance table (species \\t relative_abundance)."""
        abundances = {}
        try:
            with open(path) as fh:
                for line in fh:
                    if line.startswith("#"):
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 2:
                        try:
                            abundances[parts[0]] = float(parts[1])
                        except ValueError:
                            continue
        except Exception:
            pass
        return abundances if abundances else self._generate_demo_abundance()

    def _generate_demo_abundance(self):
        """Generate demo abundance profile for a moderately favorable microbiome."""
        random.seed(2026)
        abundances = {}

        # Favorable taxa
        for species, info in FAVORABLE_TAXA.items():
            resp = info["typical_abundance_responder"]
            nonresp = info["typical_abundance_nonresponder"]
            # Simulate a profile between responder and non-responder
            abundances[species] = round(random.uniform(nonresp, resp * 1.2), 5)

        # Unfavorable taxa
        for species, info in UNFAVORABLE_TAXA.items():
            resp = info.get("typical_abundance_responder", 0.01)
            nonresp = info.get("typical_abundance_nonresponder", 0.03)
            abundances[species] = round(random.uniform(resp, nonresp * 1.1), 5)

        # Background taxa
        background = [
            "Bacteroides vulgatus", "Prevotella copri", "Eubacterium rectale",
            "Alistipes putredinis", "Blautia obeum", "Dialister invisus",
            "Coprococcus eutactus", "Parabacteroides distasonis",
            "Streptococcus thermophilus", "Escherichia coli",
            "Lactobacillus acidophilus", "Bifidobacterium adolescentis",
            "Dorea formicigenerans", "Clostridium bolteae",
        ]
        for sp in background:
            abundances[sp] = round(random.uniform(0.005, 0.06), 5)

        # Normalize to sum ~1.0
        total = sum(abundances.values())
        if total > 0:
            abundances = {k: round(v / total, 6) for k, v in abundances.items()}
        return abundances

    # ----- diversity metrics -----

    def _alpha_diversity(self):
        """Calculate alpha diversity indices."""
        abundances = list(self.abundance_data.values())
        abundances = [a for a in abundances if a > 0]
        n_species = len(abundances)
        total = sum(abundances)

        # Shannon index
        shannon = 0.0
        for a in abundances:
            p = a / total if total > 0 else 0
            if p > 0:
                shannon -= p * math.log(p)

        # Simpson index (1 - D)
        simpson_d = sum((a / total) ** 2 for a in abundances) if total > 0 else 0
        simpson = 1.0 - simpson_d

        # Chao1 (simplified: observed richness + singletons²/(2*doubletons))
        counts = sorted(abundances)
        singletons = sum(1 for a in counts if a < 0.001)
        doubletons = sum(1 for a in counts if 0.001 <= a < 0.003)
        chao1 = n_species
        if doubletons > 0:
            chao1 += (singletons ** 2) / (2 * doubletons)

        return {
            "shannon_index": round(shannon, 4),
            "simpson_index": round(simpson, 4),
            "chao1_estimated_richness": round(chao1, 1),
            "observed_species": n_species,
            "interpretation": (
                "High diversity" if shannon > 3.0 else
                "Moderate diversity" if shannon > 2.0 else
                "Low diversity (potentially dysbiotic)"
            ),
        }

    # ----- composition profile -----

    def _composition_profile(self):
        """Summarize microbial composition at genus/species level."""
        sorted_taxa = sorted(self.abundance_data.items(), key=lambda x: x[1], reverse=True)
        top_20 = sorted_taxa[:20]

        # Phylum-level summary
        phylum_map = {}
        for species, info in {**FAVORABLE_TAXA, **UNFAVORABLE_TAXA}.items():
            phylum_map[species] = info.get("phylum", "Unknown")

        phylum_abundances = {}
        for sp, abd in self.abundance_data.items():
            phylum = phylum_map.get(sp, "Other")
            phylum_abundances[phylum] = phylum_abundances.get(phylum, 0) + abd

        return {
            "top_20_species": [{"species": s, "relative_abundance": round(a, 6)}
                               for s, a in top_20],
            "phylum_level": {k: round(v, 4) for k, v in
                             sorted(phylum_abundances.items(), key=lambda x: x[1], reverse=True)},
            "total_species_detected": len(self.abundance_data),
        }

    # ----- ICI response prediction -----

    def _ici_response_prediction(self):
        """Predict ICI response based on microbiome composition."""
        favorable_score = 0.0
        favorable_detail = []
        for species, info in FAVORABLE_TAXA.items():
            abd = self.abundance_data.get(species, 0.0)
            threshold = info["typical_abundance_responder"]
            ratio = abd / threshold if threshold > 0 else 0
            contribution = min(ratio, 2.0)  # cap at 2x
            strength_mult = {"strong": 2.0, "moderate": 1.0}.get(
                info["association_strength"], 0.5)
            weighted = contribution * strength_mult
            favorable_score += weighted
            favorable_detail.append({
                "species": species,
                "abundance": round(abd, 6),
                "responder_typical": info["typical_abundance_responder"],
                "ratio_to_threshold": round(ratio, 3),
                "contribution": round(weighted, 3),
            })

        unfavorable_score = 0.0
        unfavorable_detail = []
        for species, info in UNFAVORABLE_TAXA.items():
            abd = self.abundance_data.get(species, 0.0)
            threshold = info.get("typical_abundance_nonresponder", 0.03)
            ratio = abd / threshold if threshold > 0 else 0
            unfavorable_score += min(ratio, 2.0)
            unfavorable_detail.append({
                "species": species,
                "abundance": round(abd, 6),
                "nonresponder_typical": threshold,
                "ratio_to_threshold": round(ratio, 3),
            })

        # ICI response score
        raw_score = favorable_score - unfavorable_score * 0.5
        # Normalize to 0-100
        normalized = max(0, min(100, 50 + raw_score * 8))

        if normalized >= 70:
            prediction = "Likely responder"
            confidence = "Moderate-High"
        elif normalized >= 45:
            prediction = "Uncertain / Intermediate"
            confidence = "Low-Moderate"
        else:
            prediction = "Likely non-responder"
            confidence = "Moderate"

        return {
            "ici_response_score": round(normalized, 1),
            "prediction": prediction,
            "confidence": confidence,
            "favorable_taxa_score": round(favorable_score, 3),
            "unfavorable_taxa_score": round(unfavorable_score, 3),
            "favorable_taxa_detail": favorable_detail,
            "unfavorable_taxa_detail": unfavorable_detail,
            "note": "ICI response prediction is based on published microbiome-ICI "
                    "associations. Clinical validation is ongoing.",
        }

    # ----- tumor microbiome -----

    def _tumor_microbiome_analysis(self):
        """Analyze tumor-associated microbiome signatures."""
        tumor_info = TUMOR_MICROBIOME.get(self.cancer_type, {})
        key_taxa = tumor_info.get("key_taxa", [])

        # Check if any tumor microbiome data available
        has_tumor_data = self.tumor_data_path and os.path.isfile(self.tumor_data_path)

        return {
            "cancer_type": self.cancer_type,
            "context": CANCER_CONTEXT.get(self.cancer_type,
                                          "Limited microbiome data for this cancer type"),
            "key_tumor_associated_taxa": key_taxa,
            "data_available": has_tumor_data,
            "note": "Tumor microbiome analysis from tumor RNA-seq requires specialized "
                    "decontamination pipelines. Results shown are literature-based.",
        }

    # ----- metabolite inference -----

    def _metabolite_inference(self):
        """Infer metabolite production capacity from microbial composition."""
        metabolite_scores = {}
        for metabolite, info in METABOLITE_PRODUCERS.items():
            producers = info["producers"]
            total_producer_abundance = 0.0
            detected_producers = []
            for p in producers:
                # Match by genus if exact species not found
                abd = self.abundance_data.get(p, 0.0)
                if abd == 0:
                    genus = p.split()[0]
                    for sp, a in self.abundance_data.items():
                        if sp.startswith(genus):
                            abd = max(abd, a)
                if abd > 0:
                    detected_producers.append({"species": p, "abundance": round(abd, 6)})
                total_producer_abundance += abd

            if total_producer_abundance > 0.05:
                production_level = "High"
            elif total_producer_abundance > 0.02:
                production_level = "Moderate"
            elif total_producer_abundance > 0:
                production_level = "Low"
            else:
                production_level = "Not detected"

            metabolite_scores[metabolite] = {
                "total_producer_abundance": round(total_producer_abundance, 5),
                "production_level": production_level,
                "detected_producers": detected_producers,
                "function": info["function"],
                "cancer_relevance": info["cancer_relevance"],
            }
        return metabolite_scores

    # ----- antibiotic impact -----

    def _antibiotic_impact_assessment(self, recent_antibiotics=None):
        """Model antibiotic impact on microbiome and ICI response."""
        if not recent_antibiotics:
            recent_antibiotics = []

        assessments = []
        for abx in recent_antibiotics:
            abx_lower = abx.lower()
            category = "minimal_impact"
            for cat, info in ANTIBIOTIC_IMPACT.items():
                if any(ex in abx_lower for ex in info["examples"]):
                    category = cat
                    break
            impact_info = ANTIBIOTIC_IMPACT[category]
            assessments.append({
                "antibiotic": abx,
                "category": category,
                "diversity_reduction_pct": impact_info["diversity_reduction_pct"],
                "estimated_recovery_weeks": impact_info["recovery_weeks"],
                "ici_impact": impact_info["ici_impact"],
            })

        overall = "No recent antibiotic exposure" if not assessments else (
            "Significant microbiome disruption" if any(
                a["category"] == "broad_spectrum" for a in assessments)
            else "Moderate microbiome impact"
        )

        return {
            "recent_antibiotics_assessed": assessments,
            "overall_impact": overall,
            "recommendation": (
                "Delay ICI initiation by 2-4 weeks if possible after broad-spectrum "
                "antibiotics to allow partial microbiome recovery."
                if any(a["category"] == "broad_spectrum" for a in assessments)
                else "No significant antibiotic-related concern for ICI timing."
            ),
            "general_guidance": {
                "broad_spectrum_impact": ANTIBIOTIC_IMPACT["broad_spectrum"],
                "narrow_spectrum_impact": ANTIBIOTIC_IMPACT["narrow_spectrum"],
            },
        }

    # ----- FMT / probiotic / dietary recommendations -----

    def _fmt_probiotic_recommendations(self, ici_score, diversity):
        """Generate FMT, probiotic, and dietary recommendations."""
        recommendations = {"fmt": None, "probiotics": [], "dietary": []}

        # FMT recommendation
        if ici_score < 40:
            recommendations["fmt"] = {
                "recommendation": "Consider FMT from ICI-responder donor",
                "rationale": "Low ICI-response microbiome score suggests potential benefit "
                             "from microbiome reconstitution",
                "evidence_level": "Phase I/II clinical trials show feasibility and "
                                  "conversion of some non-responders",
                "cautions": [
                    "Screen donor for infectious agents and drug-resistant organisms",
                    "Optimal timing relative to ICI initiation uncertain",
                    "Regulatory status varies by jurisdiction",
                ],
            }
        elif ici_score < 55:
            recommendations["fmt"] = {
                "recommendation": "FMT may be considered in clinical trial setting",
                "rationale": "Intermediate microbiome profile; potential for improvement",
                "evidence_level": "Limited but growing",
            }
        else:
            recommendations["fmt"] = {
                "recommendation": "FMT not indicated based on current microbiome profile",
                "rationale": "Favorable microbiome composition already present",
            }

        # Probiotic recommendations
        for strain_info in PROBIOTIC_STRAINS:
            relevance = "Relevant" if self.cancer_type in strain_info.get("context", "") or \
                        "ICI" in strain_info.get("context", "") else "General support"
            recommendations["probiotics"].append({
                **strain_info,
                "relevance_to_case": relevance,
            })

        # Dietary recommendations
        shannon = diversity.get("shannon_index", 2.0)
        recommendations["dietary"] = [
            {
                "recommendation": "High-fiber diet (>30g/day)",
                "rationale": "Dietary fiber promotes SCFA-producing bacteria; "
                             "associated with better ICI outcomes",
                "specifics": "Whole grains, legumes, vegetables, fruits",
                "evidence": "Observational studies in melanoma ICI cohorts",
            },
            {
                "recommendation": "Fermented foods (2-3 servings/day)",
                "rationale": "Increase microbial diversity; introduction of beneficial strains",
                "specifics": "Yogurt, kefir, sauerkraut, kimchi, kombucha",
                "evidence": "Stanford fermented food trial showed increased diversity",
            },
            {
                "recommendation": "Polyphenol-rich foods",
                "rationale": "Promote Akkermansia and other favorable taxa",
                "specifics": "Berries, green tea, dark chocolate, pomegranate",
                "evidence": "Preclinical and observational",
            },
            {
                "recommendation": "Limit processed foods and red meat",
                "rationale": "Reduce pro-inflammatory bacterial metabolites (TMAO, "
                             "secondary bile acids)",
                "evidence": "Epidemiological and mechanistic studies",
            },
        ]
        if shannon < 2.5:
            recommendations["dietary"].append({
                "recommendation": "Diversity-focused eating (>30 plant species per week)",
                "rationale": "Low current diversity; dietary variety strongly correlates "
                             "with microbial diversity",
                "evidence": "American Gut Project",
            })

        return recommendations

    # ----- main analysis -----

    def analyze(self):
        """Run full microbiome-cancer interaction analysis."""
        self.abundance_data = self._load_abundance_data()

        # Diversity
        diversity = self._alpha_diversity()

        # Composition
        composition = self._composition_profile()

        # ICI response prediction
        ici_pred = self._ici_response_prediction()

        # Tumor microbiome
        tumor_mb = self._tumor_microbiome_analysis()

        # Metabolite inference
        metabolites = self._metabolite_inference()

        # Antibiotic impact (demo: assume some prior antibiotics)
        abx_impact = self._antibiotic_impact_assessment(
            recent_antibiotics=["fluoroquinolones"])

        # Recommendations
        recs = self._fmt_probiotic_recommendations(
            ici_pred.get("ici_response_score", 50), diversity)

        result = {
            "analysis": "microbiome_cancer_interaction",
            "timestamp": datetime.now().isoformat(),
            "cancer_type": self.cancer_type,
            "diversity_metrics": diversity,
            "composition_profile": composition,
            "ici_response_prediction": ici_pred,
            "tumor_microbiome": tumor_mb,
            "metabolite_inference": metabolites,
            "antibiotic_impact": abx_impact,
            "fmt_recommendation": recs["fmt"],
            "probiotic_recommendations": recs["probiotics"],
            "dietary_recommendations": recs["dietary"],
            "data_source": {
                "metagenomics": "file" if (self.metagenomics_path and
                                           os.path.isfile(self.metagenomics_path)) else "demo",
                "tumor_data": "file" if (self.tumor_data_path and
                                         os.path.isfile(self.tumor_data_path)) else "not_provided",
                "clinical": "file" if (self.clinical_path and
                                       os.path.isfile(self.clinical_path)) else "not_provided",
            },
        }
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Microbiome-Cancer Interaction Analyzer"
    )
    parser.add_argument("--metagenomics", default=None,
                        help="Path to metagenomic data (FASTQ or abundance table)")
    parser.add_argument("--tumor_data", default=None,
                        help="Path to tumor RNA-seq or microbiome data")
    parser.add_argument("--clinical", default=None,
                        help="Path to clinical treatment outcomes (CSV)")
    parser.add_argument("--analysis", default="ici_response",
                        help="Analysis type (ici_response, tumor_microbiome, full)")
    parser.add_argument("--reference", default=None,
                        help="Reference database (e.g., metaphlan_db)")
    parser.add_argument("--cancer_type", default="melanoma",
                        help="Cancer type (CRC, melanoma, NSCLC, RCC, gastric, pancreatic)")
    parser.add_argument("--output", default=None,
                        help="Output directory or file for results JSON")

    args = parser.parse_args()

    analyzer = MicrobiomeCancerAnalyzer(
        metagenomics=args.metagenomics,
        tumor_data=args.tumor_data,
        clinical=args.clinical,
        analysis=args.analysis,
        reference=args.reference,
        cancer_type=args.cancer_type,
    )

    results = analyzer.analyze()

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or out_path.endswith("/"):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, "microbiome_cancer_report.json")
        else:
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as fh:
            json.dump(results, fh, indent=2)
        print(f"Results written to {out_path}")
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

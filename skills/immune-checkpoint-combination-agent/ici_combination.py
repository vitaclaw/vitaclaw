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
Immune Checkpoint Inhibitor Combination Recommendations.

Profiles checkpoint expression, classifies tumor microenvironment (TME),
analyzes resistance mechanisms, and recommends evidence-based ICI
combination strategies with synergy scoring.
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Checkpoint genes and aliases
CHECKPOINT_GENES = {
    "PD-L1": {"gene_symbol": "CD274", "type": "ligand", "pathway": "PD-1/PD-L1"},
    "PD-L2": {"gene_symbol": "PDCD1LG2", "type": "ligand", "pathway": "PD-1/PD-L1"},
    "PD-1": {"gene_symbol": "PDCD1", "type": "receptor", "pathway": "PD-1/PD-L1"},
    "CTLA-4": {"gene_symbol": "CTLA4", "type": "receptor", "pathway": "CTLA-4/B7"},
    "LAG-3": {"gene_symbol": "LAG3", "type": "receptor", "pathway": "LAG-3/MHC-II"},
    "TIM-3": {"gene_symbol": "HAVCR2", "type": "receptor", "pathway": "TIM-3/Galectin-9"},
    "TIGIT": {"gene_symbol": "TIGIT", "type": "receptor", "pathway": "TIGIT/CD155"},
    "VISTA": {"gene_symbol": "VSIR", "type": "receptor", "pathway": "VISTA"},
    "B7-H3": {"gene_symbol": "CD276", "type": "ligand", "pathway": "B7-H3"},
    "B7-H4": {"gene_symbol": "VTCN1", "type": "ligand", "pathway": "B7-H4"},
    "BTLA": {"gene_symbol": "BTLA", "type": "receptor", "pathway": "BTLA/HVEM"},
    "IDO1": {"gene_symbol": "IDO1", "type": "enzyme", "pathway": "Tryptophan/IDO"},
}

# TME gene signatures
TME_SIGNATURES = {
    "cd8_t_cell": ["CD8A", "CD8B", "GZMA", "GZMB", "PRF1"],
    "ifn_gamma": ["IFNG", "CXCL9", "CXCL10", "CXCL11", "IDO1", "STAT1"],
    "exhaustion": ["PDCD1", "LAG3", "HAVCR2", "TIGIT", "CTLA4", "TOX"],
    "treg": ["FOXP3", "IL2RA", "CTLA4", "IKZF2"],
    "myeloid": ["CD68", "CD163", "CSF1R", "ARG1", "TGFB1"],
    "wnt_beta_catenin": ["CTNNB1", "APC", "AXIN2", "MYC", "CCND1"],
}

# ICI combination evidence database
ICI_COMBINATIONS = [
    {
        "name": "nivolumab + ipilimumab",
        "targets": ["PD-1", "CTLA-4"],
        "indications": ["melanoma", "RCC", "NSCLC", "MSI-H/dMMR", "HCC", "mesothelioma"],
        "evidence_level": "FDA_approved",
        "key_trials": ["CheckMate-067", "CheckMate-214", "CheckMate-9LA"],
        "toxicity": "High (Grade 3-4 irAE ~55% in melanoma)",
    },
    {
        "name": "relatlimab + nivolumab",
        "targets": ["LAG-3", "PD-1"],
        "indications": ["melanoma"],
        "evidence_level": "FDA_approved",
        "key_trials": ["RELATIVITY-047"],
        "toxicity": "Moderate (lower than nivo+ipi)",
    },
    {
        "name": "pembrolizumab + lenvatinib",
        "targets": ["PD-1", "VEGFR"],
        "indications": ["RCC", "endometrial", "HCC"],
        "evidence_level": "FDA_approved",
        "key_trials": ["KEYNOTE-581/CLEAR", "KEYNOTE-775"],
        "toxicity": "Moderate-High",
    },
    {
        "name": "atezolizumab + bevacizumab",
        "targets": ["PD-L1", "VEGF"],
        "indications": ["HCC", "RCC"],
        "evidence_level": "FDA_approved",
        "key_trials": ["IMbrave150"],
        "toxicity": "Moderate",
    },
    {
        "name": "anti-PD-L1 + chemotherapy",
        "targets": ["PD-L1", "chemotherapy"],
        "indications": ["NSCLC", "TNBC", "SCLC", "urothelial"],
        "evidence_level": "FDA_approved",
        "key_trials": ["KEYNOTE-189", "IMpower130", "IMpower133"],
        "toxicity": "Moderate (additive to chemo)",
    },
    {
        "name": "tiragolumab + atezolizumab",
        "targets": ["TIGIT", "PD-L1"],
        "indications": ["NSCLC"],
        "evidence_level": "Phase_III",
        "key_trials": ["SKYSCRAPER-01"],
        "toxicity": "Moderate",
    },
    {
        "name": "anti-PD-1 + anti-TIM-3",
        "targets": ["PD-1", "TIM-3"],
        "indications": ["various_solid_tumors"],
        "evidence_level": "Phase_II",
        "key_trials": ["Multiple early-phase"],
        "toxicity": "Under investigation",
    },
    {
        "name": "anti-PD-1 + IDO inhibitor",
        "targets": ["PD-1", "IDO1"],
        "indications": ["melanoma"],
        "evidence_level": "Phase_III_negative",
        "key_trials": ["ECHO-301 (negative)"],
        "toxicity": "Moderate",
    },
]

# Resistance mechanism genes
RESISTANCE_GENES = {
    "B2M": {"mechanism": "HLA class I loss", "type": "primary"},
    "JAK1": {"mechanism": "IFN-gamma signaling defect", "type": "primary"},
    "JAK2": {"mechanism": "IFN-gamma signaling defect", "type": "primary"},
    "CTNNB1": {"mechanism": "WNT/beta-catenin activation (T cell exclusion)", "type": "primary"},
    "PTEN": {"mechanism": "PI3K activation / immune exclusion", "type": "primary"},
    "STK11": {"mechanism": "LKB1 loss / cold TME", "type": "primary"},
    "HLA-A": {"mechanism": "HLA loss", "type": "acquired"},
    "HLA-B": {"mechanism": "HLA loss", "type": "acquired"},
    "HLA-C": {"mechanism": "HLA loss", "type": "acquired"},
    "IFNGR1": {"mechanism": "IFN-gamma receptor defect", "type": "acquired"},
    "IFNGR2": {"mechanism": "IFN-gamma receptor defect", "type": "acquired"},
}


class ICICombinationAnalyzer:
    """Immune checkpoint inhibitor combination recommendation engine."""

    def __init__(self, rnaseq_path=None, ihc_path=None, mutations_path=None,
                 tmb=None, msi="stable", tumor_type="melanoma",
                 prior_treatment=None):
        self.rnaseq_path = rnaseq_path
        self.ihc_path = ihc_path
        self.mutations_path = mutations_path
        self.tmb = tmb
        self.msi = msi.lower() if msi else "stable"
        self.tumor_type = tumor_type.lower()
        self.prior_treatment = prior_treatment
        self.expression_data = {}
        self.mutations = []

    def _load_expression(self):
        """Load RNAseq expression data or generate demo."""
        if self.rnaseq_path and os.path.isfile(self.rnaseq_path):
            data = {}
            with open(self.rnaseq_path, "r") as fh:
                header = fh.readline()
                for line in fh:
                    parts = line.strip().split("\t")
                    if len(parts) >= 2:
                        data[parts[0]] = float(parts[1])
            return data
        # Demo expression data (log2 TPM)
        return {
            "CD274": 6.5, "PDCD1LG2": 3.2, "PDCD1": 5.8,
            "CTLA4": 4.5, "LAG3": 5.2, "HAVCR2": 4.8,
            "TIGIT": 5.5, "VSIR": 3.0, "CD276": 7.2,
            "VTCN1": 2.5, "BTLA": 3.8, "IDO1": 6.0,
            "CD8A": 7.5, "CD8B": 6.8, "GZMA": 6.5,
            "GZMB": 7.0, "PRF1": 5.5, "IFNG": 5.0,
            "CXCL9": 6.2, "CXCL10": 6.8, "CXCL11": 4.5,
            "STAT1": 6.0, "TOX": 4.2,
            "FOXP3": 4.0, "IL2RA": 3.5, "IKZF2": 3.0,
            "CD68": 5.5, "CD163": 4.8, "CSF1R": 4.2,
            "ARG1": 3.0, "TGFB1": 5.0,
            "CTNNB1": 4.0, "APC": 5.5, "AXIN2": 3.5,
            "MYC": 5.0, "CCND1": 4.5,
        }

    def _load_ihc(self):
        """Load IHC PD-L1 data or generate demo."""
        if self.ihc_path and os.path.isfile(self.ihc_path):
            with open(self.ihc_path, "r") as fh:
                return json.load(fh)
        return {"pd_l1_tps": 60, "pd_l1_cps": 70, "assay": "22C3"}

    def _load_mutations(self):
        """Load mutations from MAF or generate demo."""
        if self.mutations_path and os.path.isfile(self.mutations_path):
            mutations = []
            with open(self.mutations_path, "r") as fh:
                header = fh.readline()
                for line in fh:
                    parts = line.strip().split("\t")
                    if parts:
                        mutations.append({"gene": parts[0],
                                          "variant": parts[1] if len(parts) > 1 else "",
                                          "type": parts[2] if len(parts) > 2 else "missense"})
            return mutations
        return [
            {"gene": "BRAF", "variant": "V600E", "type": "missense"},
            {"gene": "TP53", "variant": "R175H", "type": "missense"},
            {"gene": "CDKN2A", "variant": "deletion", "type": "deletion"},
        ]

    def _profile_checkpoints(self, expression):
        """Profile checkpoint expression levels from RNAseq."""
        profile = {}
        for cp_name, cp_info in CHECKPOINT_GENES.items():
            symbol = cp_info["gene_symbol"]
            expr_val = expression.get(symbol, 0.0)
            # Thresholds: high > 6, moderate 4-6, low < 4 (log2 TPM)
            if expr_val > 6.0:
                level = "high"
            elif expr_val > 4.0:
                level = "moderate"
            else:
                level = "low"
            profile[cp_name] = {
                "gene_symbol": symbol,
                "expression_log2tpm": round(expr_val, 2),
                "level": level,
                "type": cp_info["type"],
                "pathway": cp_info["pathway"],
            }
        return profile

    def _classify_tme(self, expression):
        """Classify tumor microenvironment as hot, excluded, or desert."""
        def _signature_score(genes):
            vals = [expression.get(g, 0.0) for g in genes]
            return sum(vals) / len(vals) if vals else 0.0

        cd8_score = _signature_score(TME_SIGNATURES["cd8_t_cell"])
        ifng_score = _signature_score(TME_SIGNATURES["ifn_gamma"])
        exhaustion_score = _signature_score(TME_SIGNATURES["exhaustion"])
        treg_score = _signature_score(TME_SIGNATURES["treg"])
        myeloid_score = _signature_score(TME_SIGNATURES["myeloid"])
        wnt_score = _signature_score(TME_SIGNATURES["wnt_beta_catenin"])

        # Classification logic
        immune_score = (cd8_score + ifng_score) / 2
        if immune_score > 5.5 and cd8_score > 5.0:
            if exhaustion_score > 4.5:
                classification = "immune_inflamed_exhausted"
                description = "Hot tumor with T cell exhaustion — ICI likely to benefit"
            else:
                classification = "immune_inflamed"
                description = "Hot tumor with active immune infiltrate — ICI likely to work"
        elif immune_score > 3.5:
            classification = "immune_excluded"
            description = "Immune cells at margin but not infiltrating — need combination"
        else:
            classification = "immune_desert"
            description = "Cold tumor with low immune infiltrate — need priming strategies"

        return {
            "classification": classification,
            "description": description,
            "scores": {
                "cd8_t_cell_score": round(cd8_score, 2),
                "ifn_gamma_score": round(ifng_score, 2),
                "exhaustion_score": round(exhaustion_score, 2),
                "treg_score": round(treg_score, 2),
                "myeloid_score": round(myeloid_score, 2),
                "wnt_beta_catenin_score": round(wnt_score, 2),
                "composite_immune_score": round(immune_score, 2),
            },
            "signature_genes": TME_SIGNATURES,
        }

    def _analyze_resistance(self, mutations, expression):
        """Analyze resistance mechanisms from mutations and expression."""
        primary = []
        acquired = []
        adaptive = []

        mutated_genes = {m["gene"] for m in mutations}

        for gene, info in RESISTANCE_GENES.items():
            if gene in mutated_genes:
                entry = {"gene": gene, "mechanism": info["mechanism"], "type": info["type"]}
                if info["type"] == "primary":
                    primary.append(entry)
                else:
                    acquired.append(entry)

        # Check for WNT activation
        wnt_genes = TME_SIGNATURES["wnt_beta_catenin"]
        wnt_score = sum(expression.get(g, 0.0) for g in wnt_genes) / len(wnt_genes)
        if wnt_score > 5.5 or "CTNNB1" in mutated_genes:
            primary.append({
                "gene": "CTNNB1/WNT",
                "mechanism": "WNT/beta-catenin activation — T cell exclusion",
                "type": "primary",
            })

        # Low TMB as resistance mechanism
        if self.tmb is not None and self.tmb < 5:
            primary.append({
                "gene": "TMB_low",
                "mechanism": f"Low TMB ({self.tmb} mut/Mb) — few neoantigens",
                "type": "primary",
            })

        # Adaptive resistance: checkpoint upregulation
        for cp_name in ["LAG-3", "TIM-3", "TIGIT", "VISTA"]:
            symbol = CHECKPOINT_GENES[cp_name]["gene_symbol"]
            expr = expression.get(symbol, 0.0)
            if expr > 5.5:
                adaptive.append({
                    "checkpoint": cp_name,
                    "expression": round(expr, 2),
                    "mechanism": f"Upregulation of alternative checkpoint {cp_name}",
                    "type": "adaptive",
                })

        return {
            "primary_resistance": primary,
            "acquired_resistance": acquired,
            "adaptive_resistance": adaptive,
            "total_mechanisms": len(primary) + len(acquired) + len(adaptive),
        }

    def _recommend_combinations(self, tme, checkpoint_profile, resistance):
        """Recommend ICI combinations based on TME, biomarkers, and resistance."""
        recommendations = []
        tme_class = tme["classification"]

        for combo in ICI_COMBINATIONS:
            score = 0
            reasons = []

            # Tumor type match
            tumor_match = (self.tumor_type in [ind.lower() for ind in combo["indications"]]
                           or "various_solid_tumors" in combo["indications"])
            if tumor_match:
                score += 3
                reasons.append(f"Indicated for {self.tumor_type}")

            # MSI-H match
            if self.msi in ("high", "msi-h", "msi_h", "dmmr") and "MSI-H/dMMR" in combo["indications"]:
                score += 3
                reasons.append("MSI-H/dMMR indication")

            # TME-based scoring
            if tme_class in ("immune_inflamed", "immune_inflamed_exhausted"):
                if "PD-1" in combo["targets"] or "PD-L1" in combo["targets"]:
                    score += 2
                    reasons.append("Inflamed TME — PD-1/PD-L1 blockade likely effective")
            elif tme_class == "immune_excluded":
                if "VEGFR" in combo["targets"] or "VEGF" in combo["targets"]:
                    score += 2
                    reasons.append("Excluded TME — anti-VEGF may improve infiltration")
                if "chemotherapy" in combo["targets"]:
                    score += 1
                    reasons.append("Chemo may prime immune response")
            elif tme_class == "immune_desert":
                if "CTLA-4" in combo["targets"]:
                    score += 2
                    reasons.append("Desert TME — CTLA-4 blockade may prime T cells")

            # Checkpoint expression matching
            for target in combo["targets"]:
                if target in checkpoint_profile:
                    level = checkpoint_profile[target]["level"]
                    if level == "high":
                        score += 1
                        reasons.append(f"High {target} expression")

            # Adaptive resistance targeting
            for ar in resistance.get("adaptive_resistance", []):
                cp = ar["checkpoint"]
                for target in combo["targets"]:
                    if cp.replace("-", "") in target.replace("-", ""):
                        score += 2
                        reasons.append(f"Targets upregulated {cp} (adaptive resistance)")

            # Prior treatment consideration
            if self.prior_treatment:
                prior = self.prior_treatment.lower()
                if any(t.lower() in prior for t in combo["targets"]):
                    score -= 2
                    reasons.append(f"Prior treatment with {self.prior_treatment} — consider alternatives")

            if score > 0 or tumor_match:
                recommendations.append({
                    "combination": combo["name"],
                    "targets": combo["targets"],
                    "score": score,
                    "reasons": reasons,
                    "evidence_level": combo["evidence_level"],
                    "key_trials": combo["key_trials"],
                    "toxicity": combo["toxicity"],
                })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

    def _compute_synergy_scores(self, recommendations, tme):
        """Compute rule-based synergy estimates for combinations."""
        for rec in recommendations:
            base = rec["score"]
            targets = rec["targets"]
            synergy = base
            if len(targets) >= 2:
                # Different pathway targets = synergy bonus
                pathways = set()
                for t in targets:
                    if t in CHECKPOINT_GENES:
                        pathways.add(CHECKPOINT_GENES[t]["pathway"])
                    else:
                        pathways.add(t)
                if len(pathways) >= 2:
                    synergy += 1
            rec["synergy_score"] = synergy
        return recommendations

    def _summarize_biomarkers(self, ihc_data, tme):
        """Summarize key biomarker status."""
        return {
            "pd_l1_tps": ihc_data.get("pd_l1_tps"),
            "pd_l1_cps": ihc_data.get("pd_l1_cps"),
            "ihc_assay": ihc_data.get("assay"),
            "tmb": self.tmb,
            "tmb_status": ("high" if self.tmb and self.tmb >= 10 else
                           "intermediate" if self.tmb and self.tmb >= 5 else "low"),
            "msi_status": self.msi,
            "tme_classification": tme["classification"],
        }

    def _summarize_evidence(self, recommendations):
        """Summarize evidence for top recommendations."""
        summary = []
        for rec in recommendations[:5]:
            summary.append({
                "combination": rec["combination"],
                "evidence_level": rec["evidence_level"],
                "key_trials": rec["key_trials"],
                "score": rec["score"],
            })
        return summary

    def analyze(self):
        """Run ICI combination analysis."""
        expression = self._load_expression()
        ihc_data = self._load_ihc()
        self.mutations = self._load_mutations()

        checkpoint_profile = self._profile_checkpoints(expression)
        tme = self._classify_tme(expression)
        resistance = self._analyze_resistance(self.mutations, expression)
        recommendations = self._recommend_combinations(tme, checkpoint_profile, resistance)
        recommendations = self._compute_synergy_scores(recommendations, tme)
        biomarker_summary = self._summarize_biomarkers(ihc_data, tme)
        evidence_summary = self._summarize_evidence(recommendations)

        results = {
            "analysis": "immune_checkpoint_combination_recommendations",
            "analysis_date": datetime.now().isoformat(),
            "tumor_type": self.tumor_type,
            "prior_treatment": self.prior_treatment,
            "checkpoint_profile": checkpoint_profile,
            "tme_classification": tme,
            "resistance_mechanisms": resistance,
            "recommended_combinations": recommendations,
            "synergy_scores": [{"combination": r["combination"],
                                "synergy_score": r["synergy_score"]} for r in recommendations],
            "evidence_summary": evidence_summary,
            "biomarker_summary": biomarker_summary,
        }
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Immune checkpoint inhibitor combination recommendations"
    )
    parser.add_argument("--rnaseq", default=None,
                        help="Tumor RNAseq expression (TSV: gene, TPM)")
    parser.add_argument("--ihc", default=None,
                        help="PD-L1 IHC data (JSON)")
    parser.add_argument("--mutations", default=None,
                        help="Tumor mutations (MAF)")
    parser.add_argument("--tmb", type=float, default=None,
                        help="Tumor mutational burden (mut/Mb)")
    parser.add_argument("--msi", default="stable",
                        help="MSI status (stable, high)")
    parser.add_argument("--tumor_type", default="melanoma",
                        help="Tumor type")
    parser.add_argument("--prior_treatment", default=None,
                        help="Prior ICI treatment")
    parser.add_argument("--output", default="ici_recommendations.json",
                        help="Output JSON file")
    args = parser.parse_args()

    analyzer = ICICombinationAnalyzer(
        rnaseq_path=args.rnaseq,
        ihc_path=args.ihc,
        mutations_path=args.mutations,
        tmb=args.tmb,
        msi=args.msi,
        tumor_type=args.tumor_type,
        prior_treatment=args.prior_treatment,
    )

    results = analyzer.analyze()

    output_path = args.output
    if output_path.endswith("/"):
        os.makedirs(output_path, exist_ok=True)
        output_path = os.path.join(output_path, "ici_combination_results.json")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"ICI combination analysis complete. Results: {output_path}")
    print(f"  Tumor type: {results['tumor_type']}")
    print(f"  TME classification: {results['tme_classification']['classification']}")
    print(f"  Resistance mechanisms: {results['resistance_mechanisms']['total_mechanisms']}")
    top = results["recommended_combinations"]
    if top:
        print(f"  Top recommendation: {top[0]['combination']} (score: {top[0]['score']})")
    print(f"  Total combinations evaluated: {len(top)}")


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

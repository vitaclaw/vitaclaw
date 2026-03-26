#!/usr/bin/env python3
"""Pharmacogenomics (PGx) Analyzer.

Translates patient genotypes into actionable drug recommendations using
CPIC / DPWG guideline tables, star-allele-to-phenotype mapping, and
drug-drug-gene interaction checking.
"""
# COPYRIGHT NOTICE
# This file is part of the "Universal Biomedical Skills" project.
# Copyright (c) 2026 MD BABU MIA, PhD <md.babu.mia@mssm.edu>
# All Rights Reserved.
#
# This code is proprietary and confidential.
# Unauthorized copying of this file, via any medium is strictly prohibited.
#
# Provenance: Authenticated by MD BABU MIA

import argparse
import json
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, "../.."))
sys.path.insert(0, _PROJECT_ROOT)

from skills._shared.biomedical_utils import build_result, write_output

# ---------------------------------------------------------------------------
# Star allele -> phenotype mapping
# ---------------------------------------------------------------------------

PHENOTYPE_MAP: dict[str, dict[str, str]] = {
    "CYP2D6": {
        "*1/*1": "normal_metabolizer",
        "*1/*2": "normal_metabolizer",
        "*2/*2": "normal_metabolizer",
        "*1/*4": "intermediate_metabolizer",
        "*1/*5": "intermediate_metabolizer",
        "*1/*10": "intermediate_metabolizer",
        "*4/*4": "poor_metabolizer",
        "*4/*5": "poor_metabolizer",
        "*5/*5": "poor_metabolizer",
        "*1/*1xN": "ultrarapid_metabolizer",
        "*1/*2xN": "ultrarapid_metabolizer",
        "*2/*2xN": "ultrarapid_metabolizer",
    },
    "CYP2C19": {
        "*1/*1": "normal_metabolizer",
        "*1/*2": "intermediate_metabolizer",
        "*1/*3": "intermediate_metabolizer",
        "*2/*2": "poor_metabolizer",
        "*2/*3": "poor_metabolizer",
        "*3/*3": "poor_metabolizer",
        "*1/*17": "rapid_metabolizer",
        "*17/*17": "ultrarapid_metabolizer",
    },
    "CYP2C9": {
        "*1/*1": "normal_metabolizer",
        "*1/*2": "intermediate_metabolizer",
        "*1/*3": "intermediate_metabolizer",
        "*2/*2": "poor_metabolizer",
        "*2/*3": "poor_metabolizer",
        "*3/*3": "poor_metabolizer",
    },
    "VKORC1": {
        "GG": "normal_sensitivity",
        "GA": "intermediate_sensitivity",
        "AG": "intermediate_sensitivity",
        "AA": "high_sensitivity",
    },
    "CYP3A5": {
        "*1/*1": "extensive_metabolizer",
        "*1/*3": "intermediate_metabolizer",
        "*3/*3": "poor_metabolizer",
    },
    "DPYD": {
        "*1/*1": "normal_metabolizer",
        "*1/*2A": "intermediate_metabolizer",
        "*2A/*2A": "poor_metabolizer",
        "*1/*13": "intermediate_metabolizer",
    },
    "UGT1A1": {
        "*1/*1": "normal_metabolizer",
        "*1/*28": "intermediate_metabolizer",
        "*28/*28": "poor_metabolizer",
    },
    "TPMT": {
        "*1/*1": "normal_metabolizer",
        "*1/*3A": "intermediate_metabolizer",
        "*1/*3C": "intermediate_metabolizer",
        "*3A/*3A": "poor_metabolizer",
        "*3C/*3C": "poor_metabolizer",
    },
    "NUDT15": {
        "*1/*1": "normal_metabolizer",
        "*1/*3": "intermediate_metabolizer",
        "*3/*3": "poor_metabolizer",
    },
    "HLA-B": {
        "negative_5701": "normal",
        "positive_5701": "carrier_HLA-B*57:01",
        "negative_1502": "normal",
        "positive_1502": "carrier_HLA-B*15:02",
    },
    "SLCO1B1": {
        "TT": "normal_function",
        "TC": "decreased_function",
        "CC": "poor_function",
    },
}

# ---------------------------------------------------------------------------
# CPIC gene-drug recommendation tables
# ---------------------------------------------------------------------------

# Each entry: phenotype -> {risk, recommendation, cpic_level}
CPIC_TABLE: dict[str, dict[str, dict]] = {
    # ---- CYP2D6 drugs ----
    "CYP2D6:codeine": {
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid codeine. Use non-tramadol, non-codeine analgesic (e.g. morphine, non-opioid).",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "caution",
            "recommendation": "Use codeine with caution at lowest effective dose. Monitor for inadequate analgesia.",
            "cpic_level": "A",
        },
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use codeine per standard dosing guidelines.",
            "cpic_level": "A",
        },
        "ultrarapid_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid codeine. Risk of life-threatening toxicity due to rapid morphine formation.",
            "cpic_level": "A",
        },
    },
    "CYP2D6:tramadol": {
        "poor_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Consider alternative analgesic. Tramadol may lack efficacy in poor metabolizers.",
            "cpic_level": "B",
        },
        "intermediate_metabolizer": {
            "risk": "caution",
            "recommendation": "Monitor for reduced efficacy. Consider alternative if pain control inadequate.",
            "cpic_level": "B",
        },
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use tramadol per standard dosing.",
            "cpic_level": "B",
        },
        "ultrarapid_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid tramadol. Risk of respiratory depression.",
            "cpic_level": "B",
        },
    },
    "CYP2D6:tamoxifen": {
        "poor_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Consider aromatase inhibitor (if post-menopausal) or increase tamoxifen dose to 40 mg/day.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "caution",
            "recommendation": "Consider aromatase inhibitor or higher tamoxifen dose. Monitor endoxifen levels.",
            "cpic_level": "A",
        },
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use tamoxifen at standard 20 mg/day dose.",
            "cpic_level": "A",
        },
        "ultrarapid_metabolizer": {
            "risk": "normal",
            "recommendation": "Use tamoxifen at standard dose.",
            "cpic_level": "A",
        },
    },
    # ---- CYP2C19 drugs ----
    "CYP2C19:clopidogrel": {
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Use alternative antiplatelet (prasugrel or ticagrelor).",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Consider alternative antiplatelet or clopidogrel at higher dose if alternatives contraindicated.",
            "cpic_level": "A",
        },
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use clopidogrel per standard dosing.",
            "cpic_level": "A",
        },
        "rapid_metabolizer": {
            "risk": "normal",
            "recommendation": "Use clopidogrel per standard dosing.",
            "cpic_level": "A",
        },
        "ultrarapid_metabolizer": {
            "risk": "normal",
            "recommendation": "Use clopidogrel per standard dosing.",
            "cpic_level": "A",
        },
    },
    "CYP2C19:omeprazole": {
        "poor_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce omeprazole dose by 50%. Increased plasma levels expected.",
            "cpic_level": "B",
        },
        "intermediate_metabolizer": {
            "risk": "normal",
            "recommendation": "Use standard dose. May have slightly increased efficacy.",
            "cpic_level": "B",
        },
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use omeprazole per standard dosing.",
            "cpic_level": "B",
        },
        "rapid_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Increase omeprazole dose by 50-100% for H. pylori eradication.",
            "cpic_level": "B",
        },
        "ultrarapid_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Increase omeprazole dose by 100% or use alternative PPI (rabeprazole).",
            "cpic_level": "B",
        },
    },
    "CYP2C19:escitalopram": {
        "poor_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Consider 50% dose reduction of escitalopram. Risk of QTc prolongation.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "normal",
            "recommendation": "Use standard dose. Monitoring recommended.",
            "cpic_level": "A",
        },
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use escitalopram per standard dosing.",
            "cpic_level": "A",
        },
        "ultrarapid_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Consider alternative SSRI (sertraline) or increase dose. May have reduced efficacy.",
            "cpic_level": "A",
        },
    },
    # ---- CYP2C9 + VKORC1 : warfarin ----
    "CYP2C9:warfarin": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Initiate warfarin per pharmacogenomic dosing algorithm (consider VKORC1).",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce warfarin dose by 20-40%. Use pharmacogenomic algorithm.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce warfarin dose by 40-60%. High bleeding risk. Frequent INR monitoring.",
            "cpic_level": "A",
        },
    },
    # ---- CYP3A5 : tacrolimus ----
    "CYP3A5:tacrolimus": {
        "extensive_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Increase starting dose by 1.5-2x standard. Rapid clearance expected.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Increase starting dose by 1.25-1.5x standard.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "normal",
            "recommendation": "Use standard tacrolimus dosing.",
            "cpic_level": "A",
        },
    },
    # ---- DPYD : fluoropyrimidines ----
    "DPYD:fluorouracil": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use 5-FU per standard dosing.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce 5-FU dose by 50%. Monitor for severe toxicity.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid 5-FU / capecitabine. Life-threatening toxicity risk.",
            "cpic_level": "A",
        },
    },
    "DPYD:capecitabine": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use capecitabine per standard dosing.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce capecitabine dose by 50%. Monitor for toxicity.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid capecitabine. Life-threatening toxicity risk.",
            "cpic_level": "A",
        },
    },
    # ---- UGT1A1 : irinotecan ----
    "UGT1A1:irinotecan": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use irinotecan per standard dosing.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "caution",
            "recommendation": "Use standard dose with close monitoring for neutropenia / diarrhea.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce irinotecan dose by 30%. High risk of severe neutropenia.",
            "cpic_level": "A",
        },
    },
    # ---- TPMT / NUDT15 : thiopurines ----
    "TPMT:azathioprine": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use azathioprine per standard dosing.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce azathioprine dose by 30-70%. Start low and titrate.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid azathioprine or reduce to 10% of standard dose with frequent CBC monitoring.",
            "cpic_level": "A",
        },
    },
    "TPMT:mercaptopurine": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use mercaptopurine per standard dosing.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce mercaptopurine dose by 30-70%.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid or reduce to 10% of standard dose. Risk of fatal myelosuppression.",
            "cpic_level": "A",
        },
    },
    "NUDT15:azathioprine": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use azathioprine per standard dosing.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce azathioprine dose by 25-50%.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid azathioprine. Severe leukopenia risk.",
            "cpic_level": "A",
        },
    },
    "NUDT15:mercaptopurine": {
        "normal_metabolizer": {
            "risk": "normal",
            "recommendation": "Use mercaptopurine per standard dosing.",
            "cpic_level": "A",
        },
        "intermediate_metabolizer": {
            "risk": "dose_adjustment",
            "recommendation": "Reduce mercaptopurine dose by 25-50%.",
            "cpic_level": "A",
        },
        "poor_metabolizer": {
            "risk": "contraindicated",
            "recommendation": "Avoid mercaptopurine. Severe leukopenia risk.",
            "cpic_level": "A",
        },
    },
    # ---- HLA-B alleles ----
    "HLA-B:abacavir": {
        "normal": {
            "risk": "normal",
            "recommendation": "Use abacavir per standard dosing.",
            "cpic_level": "A",
        },
        "carrier_HLA-B*57:01": {
            "risk": "contraindicated",
            "recommendation": "Do NOT use abacavir. High risk of hypersensitivity reaction.",
            "cpic_level": "A",
        },
    },
    "HLA-B:carbamazepine": {
        "normal": {
            "risk": "normal",
            "recommendation": "Use carbamazepine per standard dosing (if not of Southeast Asian descent, confirm HLA-B*15:02).",
            "cpic_level": "A",
        },
        "carrier_HLA-B*15:02": {
            "risk": "contraindicated",
            "recommendation": "Do NOT use carbamazepine. High risk of Stevens-Johnson syndrome / TEN.",
            "cpic_level": "A",
        },
    },
    # ---- SLCO1B1 : simvastatin ----
    "SLCO1B1:simvastatin": {
        "normal_function": {
            "risk": "normal",
            "recommendation": "Use simvastatin per standard dosing.",
            "cpic_level": "A",
        },
        "decreased_function": {
            "risk": "dose_adjustment",
            "recommendation": "Use simvastatin ≤20 mg/day or switch to pravastatin/rosuvastatin.",
            "cpic_level": "A",
        },
        "poor_function": {
            "risk": "contraindicated",
            "recommendation": "Avoid simvastatin. Use pravastatin or rosuvastatin instead. High myopathy risk.",
            "cpic_level": "A",
        },
    },
}

# ---------------------------------------------------------------------------
# Demo genotype data
# ---------------------------------------------------------------------------

DEMO_GENOTYPES: dict[str, str] = {
    "CYP2D6": "*1/*4",
    "CYP2C19": "*1/*2",
    "CYP2C9": "*1/*3",
    "VKORC1": "AG",
    "CYP3A5": "*3/*3",
    "DPYD": "*1/*1",
    "UGT1A1": "*1/*28",
    "TPMT": "*1/*1",
    "NUDT15": "*1/*1",
    "HLA-B_5701": "negative_5701",
    "HLA-B_1502": "negative_1502",
    "SLCO1B1": "TC",
}

DEMO_MEDICATIONS: list[str] = [
    "codeine", "clopidogrel", "warfarin", "tacrolimus",
    "simvastatin", "omeprazole", "tamoxifen",
]


# ---------------------------------------------------------------------------
# PGxAnalyzer
# ---------------------------------------------------------------------------

class PGxAnalyzer:
    """Pharmacogenomics analyzer – maps genotypes to drug recommendations."""

    def __init__(
        self,
        genotypes: dict[str, str],
        medications: list[str],
        guidelines: str = "cpic_dpwg",
        risk_scores: bool = False,
    ):
        self.genotypes = genotypes
        self.medications = [m.lower() for m in medications]
        self.guidelines = guidelines
        self.risk_scores = risk_scores

    # ----- phenotype resolution -----

    def _resolve_phenotypes(self) -> dict[str, dict]:
        """Map each genotype to its phenotype."""
        results = {}
        for gene, diplotype in self.genotypes.items():
            # Normalise HLA keys
            gene_key = gene.split("_")[0] if gene.startswith("HLA") else gene
            pheno_map = PHENOTYPE_MAP.get(gene_key, {})
            phenotype = pheno_map.get(diplotype, "unknown")
            results[gene] = {
                "diplotype": diplotype,
                "phenotype": phenotype,
                "gene": gene_key,
            }
        return results

    # ----- drug recommendations -----

    def _get_drug_recommendations(self, phenotypes: dict) -> list[dict]:
        """Look up CPIC recommendations for each medication."""
        recommendations = []
        for drug in self.medications:
            drug_recs = []
            for gene_key, pheno_info in phenotypes.items():
                gene = pheno_info["gene"]
                phenotype = pheno_info["phenotype"]
                lookup_key = f"{gene}:{drug}"
                table = CPIC_TABLE.get(lookup_key)
                if table is None:
                    continue
                rec = table.get(phenotype)
                if rec is None:
                    rec = table.get("normal_metabolizer") or table.get("normal") or table.get("normal_function")
                    if rec:
                        rec = {**rec, "note": f"No specific guidance for phenotype '{phenotype}'; defaulting to normal."}
                if rec:
                    drug_recs.append({
                        "gene": gene,
                        "diplotype": pheno_info["diplotype"],
                        "phenotype": phenotype,
                        **rec,
                    })

            if drug_recs:
                # Pick the most severe recommendation
                severity_order = {"contraindicated": 3, "dose_adjustment": 2, "caution": 1, "normal": 0}
                drug_recs.sort(key=lambda r: severity_order.get(r.get("risk", "normal"), 0), reverse=True)
                recommendations.append({
                    "drug": drug,
                    "overall_risk": drug_recs[0]["risk"],
                    "gene_details": drug_recs,
                })
            else:
                recommendations.append({
                    "drug": drug,
                    "overall_risk": "no_pgx_data",
                    "gene_details": [],
                    "note": "No pharmacogenomic data available for this drug with the tested genes.",
                })
        return recommendations

    # ----- drug-drug-gene interactions -----

    def _check_interactions(self, recommendations: list[dict]) -> list[dict]:
        """Check for drug-drug-gene interactions among prescribed medications."""
        interactions = []

        drug_set = set(self.medications)

        # Example interaction rules
        if "codeine" in drug_set and "tramadol" in drug_set:
            interactions.append({
                "drugs": ["codeine", "tramadol"],
                "type": "drug-drug",
                "severity": "high",
                "description": "Both are CYP2D6-metabolized opioids. Avoid concurrent use.",
            })

        if "omeprazole" in drug_set and "clopidogrel" in drug_set:
            interactions.append({
                "drugs": ["omeprazole", "clopidogrel"],
                "type": "drug-drug-gene",
                "gene": "CYP2C19",
                "severity": "moderate",
                "description": "Omeprazole inhibits CYP2C19, reducing clopidogrel activation. Consider pantoprazole.",
            })

        if "simvastatin" in drug_set and "tacrolimus" in drug_set:
            interactions.append({
                "drugs": ["simvastatin", "tacrolimus"],
                "type": "drug-drug",
                "severity": "moderate",
                "description": "Tacrolimus may increase simvastatin levels via CYP3A4 inhibition. Monitor for myopathy.",
            })

        return interactions

    # ----- risk summary -----

    def _compute_risk_summary(self, recommendations: list[dict], interactions: list[dict]) -> dict:
        """Compute overall risk summary."""
        risk_counts = {"contraindicated": 0, "dose_adjustment": 0, "caution": 0, "normal": 0, "no_pgx_data": 0}
        for rec in recommendations:
            risk = rec.get("overall_risk", "normal")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        high_risk_drugs = [r["drug"] for r in recommendations if r["overall_risk"] == "contraindicated"]
        adjustment_drugs = [r["drug"] for r in recommendations if r["overall_risk"] == "dose_adjustment"]

        overall = "normal"
        if risk_counts["contraindicated"] > 0:
            overall = "high"
        elif risk_counts["dose_adjustment"] > 0 or len(interactions) > 0:
            overall = "moderate"
        elif risk_counts["caution"] > 0:
            overall = "low"

        return {
            "overall_risk_level": overall,
            "risk_counts": risk_counts,
            "contraindicated_drugs": high_risk_drugs,
            "dose_adjustment_drugs": adjustment_drugs,
            "interaction_count": len(interactions),
        }

    # ----- main analysis -----

    def analyze(self) -> dict:
        """Run the full PGx analysis pipeline."""
        phenotypes = self._resolve_phenotypes()
        recommendations = self._get_drug_recommendations(phenotypes)
        interactions = self._check_interactions(recommendations)
        risk_summary = self._compute_risk_summary(recommendations, interactions)

        result = {
            "gene_results": {k: v for k, v in phenotypes.items()},
            "drug_recommendations": recommendations,
            "interactions": interactions,
            "risk_summary": risk_summary,
            "guidelines_used": self.guidelines,
        }

        # Evidence
        evidence = [
            "CPIC Guidelines (https://cpicpgx.org/guidelines/)",
            "DPWG Guidelines (https://www.knmp.nl/patientenzorg/medicatiebewaking/farmacogenetica)",
            "PharmGKB Annotations (https://www.pharmgkb.org/)",
        ]

        # Markdown summary
        md_lines = ["## Pharmacogenomics Report", ""]
        md_lines.append("### Gene Phenotypes")
        for gene, info in phenotypes.items():
            md_lines.append(f"- **{info['gene']}** {info['diplotype']}: {info['phenotype']}")
        md_lines.append("")
        md_lines.append("### Drug Recommendations")
        for rec in recommendations:
            icon = {"contraindicated": "!!!", "dose_adjustment": "!!", "caution": "!", "normal": "OK"}.get(rec["overall_risk"], "?")
            md_lines.append(f"- **{rec['drug']}** [{icon}] — {rec['overall_risk']}")
            for det in rec.get("gene_details", []):
                md_lines.append(f"  - {det['gene']} ({det['phenotype']}): {det.get('recommendation', '')}")
        if interactions:
            md_lines.append("")
            md_lines.append("### Drug Interactions")
            for ix in interactions:
                md_lines.append(f"- {' + '.join(ix['drugs'])} [{ix['severity']}]: {ix['description']}")
        md_lines.append("")
        md_lines.append(f"### Overall Risk: **{risk_summary['overall_risk_level'].upper()}**")
        if risk_summary["contraindicated_drugs"]:
            md_lines.append(f"- Contraindicated: {', '.join(risk_summary['contraindicated_drugs'])}")
        if risk_summary["dose_adjustment_drugs"]:
            md_lines.append(f"- Dose adjustment needed: {', '.join(risk_summary['dose_adjustment_drugs'])}")

        return build_result(
            status="success",
            result=result,
            evidence=evidence,
            metadata={"guidelines": self.guidelines, "genes_tested": len(phenotypes)},
            markdown="\n".join(md_lines),
        )


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_genotypes_from_vcf(filepath: str) -> dict[str, str]:
    """Extract pharmacogene star alleles from an annotated PGx VCF."""
    genotypes = {}
    with open(filepath, "r") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 8:
                continue
            info = parts[7]
            info_dict = {}
            for entry in info.split(";"):
                if "=" in entry:
                    k, v = entry.split("=", 1)
                    info_dict[k] = v
            gene = info_dict.get("GENE")
            diplotype = info_dict.get("DIPLOTYPE")
            if gene and diplotype:
                genotypes[gene] = diplotype
    return genotypes


def _load_medications(filepath: str) -> list[str]:
    """Load medication list from a JSON file."""
    with open(filepath, "r") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "medications" in data:
        return data["medications"]
    return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Pharmacogenomics Analyzer")
    parser.add_argument("--genotype", required=True, help="Path to annotated PGx VCF file")
    parser.add_argument("--medications", default=None, help="Path to medications JSON file")
    parser.add_argument("--guidelines", default="cpic_dpwg", choices=["cpic_dpwg", "cpic", "dpwg"], help="Guideline set")
    parser.add_argument("--risk_scores", action="store_true", help="Include composite risk scores")
    parser.add_argument("--output", default=None, help="Output JSON path")
    args = parser.parse_args()

    # Load genotypes
    if os.path.isfile(args.genotype):
        genotypes = _load_genotypes_from_vcf(args.genotype)
    else:
        print(f"[DEMO MODE] VCF '{args.genotype}' not found – using simulated patient.", file=sys.stderr)
        genotypes = dict(DEMO_GENOTYPES)

    # Load medications
    if args.medications and os.path.isfile(args.medications):
        medications = _load_medications(args.medications)
    else:
        if args.medications:
            print(f"[DEMO MODE] Medications file '{args.medications}' not found – using demo list.", file=sys.stderr)
        medications = list(DEMO_MEDICATIONS)

    analyzer = PGxAnalyzer(
        genotypes=genotypes,
        medications=medications,
        guidelines=args.guidelines,
        risk_scores=args.risk_scores,
    )
    result = analyzer.analyze()
    write_output(result, args.output)


if __name__ == "__main__":
    main()


__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

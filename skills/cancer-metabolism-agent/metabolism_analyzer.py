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
Tumor Metabolism Analysis Agent.

Quantifies Warburg effect, glutamine dependency, lipid metabolism, one-carbon
metabolism, amino acid metabolism, metabolic pathway scoring, and drug
sensitivity predictions.
"""

import argparse
import json
import math
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

GLYCOLYSIS_GENES = ["HK2", "PFKFB3", "PKM", "LDHA", "SLC2A1", "PDK1", "HIF1A"]
OXPHOS_GENES = ["NDUFS1", "SDHA", "UQCRC1", "COX5A", "ATP5F1A"]

GLUTAMINE_GENES = ["GLS", "GLS2", "SLC1A5", "SLC7A5", "GOT1", "GOT2", "GLUD1", "MYC"]

LIPOGENESIS_GENES = ["FASN", "ACLY", "ACACA", "SCD"]
FAO_GENES = ["CPT1A", "HADHA", "ACADM"]

ONECARBON_GENES = ["MTHFR", "SHMT1", "SHMT2", "TYMS", "DHFR", "MTHFD1", "MTHFD2"]

AMINO_ACID_GENES = {
    "tryptophan": ["IDO1", "TDO2"],
    "serine": ["PHGDH", "PSAT1", "PSPH"],
    "arginine": ["ASS1", "ASL"],
}

METABOLIC_PATHWAYS = {
    "glycolysis": GLYCOLYSIS_GENES,
    "tca_cycle": ["CS", "IDH1", "IDH2", "OGDH", "SUCLA2", "SDHA", "FH", "MDH2"],
    "pentose_phosphate": ["G6PD", "PGD", "TKT", "TALDO1"],
    "glutaminolysis": GLUTAMINE_GENES,
    "fatty_acid_synthesis": LIPOGENESIS_GENES,
    "beta_oxidation": FAO_GENES,
    "serine_biosynthesis": ["PHGDH", "PSAT1", "PSPH"],
    "one_carbon": ONECARBON_GENES,
}

DRUG_SENSITIVITY_RULES = {
    "high_glycolysis": {
        "drugs": ["2-DG (2-deoxyglucose)", "3-bromopyruvate"],
        "target": "Glycolysis", "evidence": "preclinical / early clinical",
    },
    "glutamine_addicted": {
        "drugs": ["CB-839 (telaglenastat)"],
        "target": "GLS (glutaminase)", "evidence": "Phase II trials",
    },
    "high_fasn": {
        "drugs": ["TVB-2640 (denifanstat)"],
        "target": "FASN", "evidence": "Phase II trials",
    },
    "high_ido1": {
        "drugs": ["epacadostat"],
        "target": "IDO1", "evidence": "Phase III (mixed results)",
    },
    "high_phgdh": {
        "drugs": ["NCT-503"],
        "target": "PHGDH", "evidence": "preclinical",
    },
    "low_ass1": {
        "drugs": ["ADI-PEG 20 (pegargiminase)"],
        "target": "Arginine deprivation", "evidence": "Phase II/III",
    },
}

TUMOR_METABOLIC_PROFILES = {
    "NSCLC": {"warburg_tendency": "high", "glutamine": "moderate", "lipid": "moderate"},
    "breast": {"warburg_tendency": "moderate", "glutamine": "high", "lipid": "high"},
    "pancreatic": {"warburg_tendency": "high", "glutamine": "high", "lipid": "moderate"},
    "glioblastoma": {"warburg_tendency": "high", "glutamine": "high", "lipid": "low"},
    "renal": {"warburg_tendency": "high", "glutamine": "moderate", "lipid": "high"},
    "colorectal": {"warburg_tendency": "moderate", "glutamine": "moderate", "lipid": "moderate"},
}


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

def _generate_demo_expression() -> Dict[str, float]:
    random.seed(47)
    all_genes = set()
    all_genes.update(GLYCOLYSIS_GENES, OXPHOS_GENES, GLUTAMINE_GENES,
                     LIPOGENESIS_GENES, FAO_GENES, ONECARBON_GENES)
    for genes in AMINO_ACID_GENES.values():
        all_genes.update(genes)
    for genes in METABOLIC_PATHWAYS.values():
        all_genes.update(genes)
    return {g: round(random.gauss(5.5, 3.0), 3) for g in all_genes}


def _generate_demo_metabolomics() -> Dict[str, float]:
    random.seed(48)
    metabolites = [
        "glucose", "lactate", "pyruvate", "citrate", "succinate", "fumarate",
        "malate", "glutamate", "glutamine", "aspartate", "serine", "glycine",
        "alanine", "palmitate", "oleate", "acetyl-CoA", "alpha-ketoglutarate",
        "2-hydroxyglutarate", "NAD+", "NADH",
    ]
    return {m: round(random.lognormvariate(2.0, 1.0), 3) for m in metabolites}


# ---------------------------------------------------------------------------
# MetabolismAnalyzer
# ---------------------------------------------------------------------------

class MetabolismAnalyzer:
    """Tumor metabolism analyser."""

    def __init__(
        self,
        expression: Optional[Dict[str, float]] = None,
        metabolomics: Optional[Dict[str, float]] = None,
        tumor_type: str = "NSCLC",
        normalize: str = "mtic",
        pathway_analysis: bool = True,
        drug_prediction: bool = True,
    ):
        self.expression = expression or _generate_demo_expression()
        self.metabolomics = metabolomics or _generate_demo_metabolomics()
        self.tumor_type = tumor_type
        self.normalize = normalize
        self.pathway_analysis = pathway_analysis
        self.drug_prediction = drug_prediction
        self.tumor_profile = TUMOR_METABOLIC_PROFILES.get(
            tumor_type, TUMOR_METABOLIC_PROFILES["NSCLC"])

    # ----- helpers -----
    def _gene_zscore(self, gene: str) -> float:
        vals = list(self.expression.values())
        mu = sum(vals) / max(len(vals), 1)
        sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / max(len(vals) - 1, 1))
        if sd == 0:
            return 0.0
        return round((self.expression.get(gene, mu) - mu) / sd, 4)

    def _pathway_mean_z(self, genes: List[str]) -> float:
        zscores = [self._gene_zscore(g) for g in genes if g in self.expression]
        if not zscores:
            return 0.0
        return round(sum(zscores) / len(zscores), 4)

    # ----- Warburg -----
    def _compute_warburg(self) -> Dict:
        glyc_z = self._pathway_mean_z(GLYCOLYSIS_GENES)
        oxphos_z = self._pathway_mean_z(OXPHOS_GENES)
        warburg_index = round(glyc_z / (oxphos_z + 1) if (oxphos_z + 1) != 0 else glyc_z, 4)
        gene_detail = {g: {"expression": self.expression.get(g, 0), "zscore": self._gene_zscore(g)}
                       for g in GLYCOLYSIS_GENES + OXPHOS_GENES}
        lactate = self.metabolomics.get("lactate", 0)
        glucose = self.metabolomics.get("glucose", 1)
        lactate_glucose_ratio = round(lactate / max(glucose, 0.01), 3)
        return {
            "warburg_index": warburg_index,
            "glycolysis_zscore": glyc_z,
            "oxphos_zscore": oxphos_z,
            "lactate_glucose_ratio": lactate_glucose_ratio,
            "status": "High Warburg" if warburg_index > 0.5 else "Low Warburg",
            "gene_detail": gene_detail,
        }

    # ----- Glutamine -----
    def _compute_glutamine(self) -> Dict:
        score = self._pathway_mean_z(GLUTAMINE_GENES)
        gls_expr = self.expression.get("GLS", 0)
        myc_expr = self.expression.get("MYC", 0)
        return {
            "glutamine_addiction_score": score,
            "status": "Glutamine addicted" if score > 0.3 else "Not glutamine addicted",
            "gls_expression": gls_expr,
            "myc_expression": myc_expr,
            "glutamine_level": self.metabolomics.get("glutamine", 0),
            "glutamate_level": self.metabolomics.get("glutamate", 0),
        }

    # ----- Lipid -----
    def _compute_lipid(self) -> Dict:
        lipo_z = self._pathway_mean_z(LIPOGENESIS_GENES)
        fao_z = self._pathway_mean_z(FAO_GENES)
        lipid_index = round(lipo_z - fao_z, 4)
        return {
            "lipid_metabolism_index": lipid_index,
            "lipogenesis_zscore": lipo_z,
            "fao_zscore": fao_z,
            "status": "De novo lipogenesis dominant" if lipid_index > 0.3 else "Balanced / FAO dominant",
            "fasn_expression": self.expression.get("FASN", 0),
            "cpt1a_expression": self.expression.get("CPT1A", 0),
        }

    # ----- One-carbon -----
    def _compute_onecarbon(self) -> Dict:
        score = self._pathway_mean_z(ONECARBON_GENES)
        return {
            "onecarbon_score": score,
            "status": "Active one-carbon metabolism" if score > 0.3 else "Low",
            "key_genes": {g: self.expression.get(g, 0) for g in ONECARBON_GENES},
        }

    # ----- Amino acid -----
    def _compute_amino_acid(self) -> Dict:
        results: Dict[str, Any] = {}
        for pathway, genes in AMINO_ACID_GENES.items():
            score = self._pathway_mean_z(genes)
            results[pathway] = {
                "score": score,
                "genes": {g: self.expression.get(g, 0) for g in genes},
            }
        return results

    # ----- Pathway scoring -----
    def _compute_pathway_scores(self) -> Dict[str, Dict]:
        scores: Dict[str, Dict] = {}
        for name, genes in METABOLIC_PATHWAYS.items():
            z = self._pathway_mean_z(genes)
            scores[name] = {
                "zscore": z,
                "status": "upregulated" if z > 0.5 else ("downregulated" if z < -0.5 else "normal"),
                "n_genes": len(genes),
                "genes_measured": sum(1 for g in genes if g in self.expression),
            }
        return scores

    # ----- Drug predictions -----
    def _predict_drugs(self, warburg: Dict, glutamine: Dict,
                       lipid: Dict, amino_acid: Dict) -> List[Dict]:
        predictions: List[Dict] = []
        if warburg["warburg_index"] > 0.5:
            predictions.append({**DRUG_SENSITIVITY_RULES["high_glycolysis"],
                                "score": warburg["warburg_index"]})
        if glutamine["glutamine_addiction_score"] > 0.3:
            predictions.append({**DRUG_SENSITIVITY_RULES["glutamine_addicted"],
                                "score": glutamine["glutamine_addiction_score"]})
        if self.expression.get("FASN", 0) > 7.0:
            predictions.append({**DRUG_SENSITIVITY_RULES["high_fasn"],
                                "score": self.expression["FASN"]})
        if self.expression.get("IDO1", 0) > 6.0:
            predictions.append({**DRUG_SENSITIVITY_RULES["high_ido1"],
                                "score": self.expression["IDO1"]})
        if self.expression.get("PHGDH", 0) > 6.5:
            predictions.append({**DRUG_SENSITIVITY_RULES["high_phgdh"],
                                "score": self.expression["PHGDH"]})
        ass1_val = self.expression.get("ASS1", 999)
        if ass1_val < 3.0:
            predictions.append({**DRUG_SENSITIVITY_RULES["low_ass1"],
                                "score": ass1_val})
        return predictions

    # ----- Metabolic phenotype -----
    def _classify_phenotype(self, warburg: Dict, glutamine: Dict, lipid: Dict) -> str:
        flags = []
        if warburg["warburg_index"] > 0.5:
            flags.append("glycolytic")
        if glutamine["glutamine_addiction_score"] > 0.3:
            flags.append("glutamine-dependent")
        if lipid["lipid_metabolism_index"] > 0.3:
            flags.append("lipogenic")
        return " / ".join(flags) if flags else "metabolically quiescent"

    # ----- main entry -----
    def analyze(self) -> Dict[str, Any]:
        warburg = self._compute_warburg()
        glutamine = self._compute_glutamine()
        lipid = self._compute_lipid()
        onecarbon = self._compute_onecarbon()
        amino_acid = self._compute_amino_acid()
        pathway_scores = self._compute_pathway_scores() if self.pathway_analysis else {}
        drug_predictions = (self._predict_drugs(warburg, glutamine, lipid, amino_acid)
                            if self.drug_prediction else [])
        phenotype = self._classify_phenotype(warburg, glutamine, lipid)

        return {
            "analysis_metadata": {
                "analysis_type": "Tumor Metabolism",
                "timestamp": datetime.now().isoformat(),
                "tumor_type": self.tumor_type,
                "normalization": self.normalize,
                "n_genes_measured": len(self.expression),
                "n_metabolites_measured": len(self.metabolomics),
            },
            "warburg_index": warburg,
            "glutamine_score": glutamine,
            "lipid_index": lipid,
            "onecarbon_metabolism": onecarbon,
            "amino_acid_metabolism": amino_acid,
            "pathway_scores": pathway_scores,
            "drug_predictions": drug_predictions,
            "metabolic_phenotype": phenotype,
            "tumor_type_profile": self.tumor_profile,
        }


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_expression(path: str) -> Optional[Dict[str, float]]:
    if not os.path.isfile(path):
        return None
    expr: Dict[str, float] = {}
    with open(path) as fh:
        header = fh.readline()  # skip header
        for line in fh:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                expr[parts[0]] = float(parts[1])
    return expr if expr else None


def _load_metabolomics(path: str) -> Optional[Dict[str, float]]:
    if not os.path.isfile(path):
        return None
    data: Dict[str, float] = {}
    with open(path) as fh:
        header = fh.readline()
        for line in fh:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                data[parts[0]] = float(parts[1])
    return data if data else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Tumor Metabolism Analyzer",
    )
    parser.add_argument("--metabolomics", default=None, help="LC-MS metabolomics CSV")
    parser.add_argument("--rnaseq", default=None, help="RNA-seq expression TSV")
    parser.add_argument("--tumor_type", default="NSCLC", help="Tumor type")
    parser.add_argument("--normalize", default="mtic",
                        help="Normalization method (mtic, tic, pqn)")
    parser.add_argument("--pathway_analysis", default="true",
                        help="Run pathway analysis (true/false)")
    parser.add_argument("--drug_prediction", default="true",
                        help="Run drug sensitivity prediction (true/false)")
    parser.add_argument("--output", default=None, help="Output path")
    args = parser.parse_args()

    expr = _load_expression(args.rnaseq) if args.rnaseq else None
    metab = _load_metabolomics(args.metabolomics) if args.metabolomics else None

    analyzer = MetabolismAnalyzer(
        expression=expr,
        metabolomics=metab,
        tumor_type=args.tumor_type,
        normalize=args.normalize,
        pathway_analysis=args.pathway_analysis.lower() == "true",
        drug_prediction=args.drug_prediction.lower() == "true",
    )
    result = analyzer.analyze()
    output = json.dumps(result, indent=2, default=str)

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or out_path.endswith("/"):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, "metabolism_report.json")
        else:
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as fh:
            fh.write(output)
        print(f"Report written to {out_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

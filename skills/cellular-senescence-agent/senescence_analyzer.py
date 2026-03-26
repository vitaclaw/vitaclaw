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
Cellular Senescence Analyzer.

Evaluates cellular senescence signatures from bulk or single-cell RNA-seq data,
profiles SASP components, classifies senescence type, estimates tissue biological
age, and predicts senolytic drug efficacy.

Usage:
    python3 senescence_analyzer.py --rnaseq tissue_expression.tsv \
        --singlecell tissue_scrnaseq.h5ad \
        --signatures fridman_sasp,reactome_senescence \
        --senolytic_prediction true --tissue liver \
        --output senescence_report/
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
# Gene signature databases
# ---------------------------------------------------------------------------

FRIDMAN_UP = [
    "CDKN1A", "CDKN2A", "MDM2", "SERPINE1", "IGFBP7", "THBS1", "GDF15",
    "CREG1", "CITED2", "DHRS2", "CDKN1C", "TGFB1I1", "HLA-E", "CDKN2B",
    "CCL2", "IGFBP3",
]

FRIDMAN_DOWN = [
    "CCNA2", "CCNB1", "CCNB2", "CDC20", "CDCA8", "CENPA", "KIF23",
    "LMNB1", "PLK1", "TOP2A",
]

REACTOME_SENESCENCE = [
    "CDKN1A", "CDKN2A", "CDKN2B", "TP53", "RB1", "E2F1", "CCND1",
    "CDK4", "CDK6", "TGFB1", "SMAD3", "IL6", "IL8", "MYC", "HMGA1",
    "HMGA2", "H2AFX", "ATM", "ATR", "CHEK1", "CHEK2", "MDM2",
]

SENMAYO_SUBSET = [
    "CDKN1A", "CDKN2A", "IL6", "CXCL8", "SERPINE1", "IGFBP3", "IGFBP7",
    "MMP1", "MMP3", "MMP9", "GDF15", "VEGFA", "CCL2", "CXCL1", "AREG",
    "HGF", "TIMP1", "TIMP2", "TGFB1", "TNF", "IL1A", "IL1B", "FN1",
    "PLAUR", "PLAU", "STC1", "IGFBP2", "IGFBP4", "IGFBP5", "MMP10",
]

# ---------------------------------------------------------------------------
# SASP component categories
# ---------------------------------------------------------------------------

SASP_COMPONENTS = {
    "cytokines": ["IL6", "CXCL8", "IL1A", "IL1B", "TNF", "CCL2", "CXCL1", "CCL3"],
    "growth_factors": ["VEGFA", "HGF", "PDGFB", "AREG"],
    "proteases": ["MMP1", "MMP3", "MMP9", "MMP10", "TIMP1", "TIMP2"],
    "other": ["SERPINE1", "CSF2", "STC1", "IGFBP2", "IGFBP3", "IGFBP4", "IGFBP5", "IGFBP7"],
}

# ---------------------------------------------------------------------------
# Senescence type marker panels
# ---------------------------------------------------------------------------

SENESCENCE_TYPE_MARKERS = {
    "replicative": {
        "positive": ["CDKN2A", "CDKN2B", "LMNB1_low", "TERT_low"],
        "description": "Telomere-driven replicative senescence",
    },
    "oncogene_induced": {
        "positive": ["CDKN2A", "CDKN1A", "H2AFX", "IL6", "CXCL8", "SERPINE1"],
        "description": "Oncogene-induced senescence (OIS), typically RAS/BRAF driven",
    },
    "therapy_induced": {
        "positive": ["CDKN1A", "TP53", "MDM2", "GDF15", "SERPINE1"],
        "description": "Therapy-induced senescence (TIS) following chemo/radiation",
    },
    "dna_damage": {
        "positive": ["ATM", "ATR", "CHEK1", "CHEK2", "H2AFX", "CDKN1A"],
        "description": "DNA damage-induced senescence",
    },
    "stress_induced": {
        "positive": ["CDKN1A", "SERPINE1", "HMGA1", "GDF15", "IGFBP7"],
        "description": "Stress-induced premature senescence (SIPS)",
    },
}

# ---------------------------------------------------------------------------
# Senolytic drug database
# ---------------------------------------------------------------------------

SENOLYTIC_DRUGS = [
    {
        "name": "Navitoclax (ABT-263)",
        "target": "BCL-2/BCL-XL/BCL-W inhibitor",
        "mechanism": "BH3 mimetic inducing apoptosis in senescent cells with elevated BCL-2 family",
        "markers_for_efficacy": ["BCL2", "BCL2L1", "BCL2L2"],
        "best_for": ["replicative", "therapy_induced"],
        "caution": "Thrombocytopenia risk due to BCL-XL inhibition in platelets",
    },
    {
        "name": "Dasatinib + Quercetin (D+Q)",
        "target": "Broad senolytic targeting SCAPs",
        "mechanism": "Dasatinib inhibits SRC kinases; Quercetin inhibits PI3K/serpins",
        "markers_for_efficacy": ["SERPINE1", "CDKN1A", "BCL2L1", "EFNB1"],
        "best_for": ["replicative", "stress_induced", "oncogene_induced"],
        "caution": "Most studied clinical senolytic combination",
    },
    {
        "name": "Fisetin",
        "target": "Flavonoid senolytic",
        "mechanism": "Inhibits PI3K/AKT/mTOR and NF-kB pathways in senescent cells",
        "markers_for_efficacy": ["CDKN1A", "SERPINE1", "IL6"],
        "best_for": ["replicative", "stress_induced"],
        "caution": "Generally well-tolerated; clinical trials ongoing",
    },
    {
        "name": "FOXO4-DRI",
        "target": "p53 releaser from FOXO4 sequestration",
        "mechanism": "Disrupts FOXO4-p53 interaction, releasing p53 to induce apoptosis",
        "markers_for_efficacy": ["TP53", "FOXO4"],
        "best_for": ["dna_damage", "therapy_induced"],
        "caution": "Peptide-based; delivery challenges for systemic use",
    },
    {
        "name": "UBX0101",
        "target": "MDM2/p53 interaction inhibitor",
        "mechanism": "Blocks MDM2-mediated p53 degradation in senescent cells",
        "markers_for_efficacy": ["MDM2", "TP53", "CDKN1A"],
        "best_for": ["therapy_induced", "dna_damage"],
        "caution": "Primarily studied in osteoarthritis joints (intra-articular)",
    },
    {
        "name": "Cardiac glycosides (Ouabain/Digoxin)",
        "target": "Na+/K+ ATPase inhibitor",
        "mechanism": "Exploit altered ion homeostasis in senescent cells",
        "markers_for_efficacy": ["ATP1A1", "BCL2"],
        "best_for": ["oncogene_induced", "therapy_induced"],
        "caution": "Pipeline; narrow therapeutic window",
    },
    {
        "name": "HSP90 inhibitors (17-DMAG/Geldanamycin)",
        "target": "HSP90 chaperone inhibitor",
        "mechanism": "Destabilize anti-apoptotic proteins in senescent cells",
        "markers_for_efficacy": ["HSP90AA1", "AKT1", "BCL2"],
        "best_for": ["oncogene_induced", "stress_induced"],
        "caution": "Pipeline; hepatotoxicity concerns",
    },
]

# ---------------------------------------------------------------------------
# Tissue-specific reference ranges for biological age estimation
# ---------------------------------------------------------------------------

TISSUE_SENESCENCE_REF = {
    "liver":   {"young_score": 0.1, "aged_score": 0.7, "age_range": (20, 80)},
    "skin":    {"young_score": 0.15, "aged_score": 0.75, "age_range": (20, 80)},
    "lung":    {"young_score": 0.12, "aged_score": 0.65, "age_range": (20, 80)},
    "kidney":  {"young_score": 0.10, "aged_score": 0.60, "age_range": (20, 80)},
    "brain":   {"young_score": 0.08, "aged_score": 0.55, "age_range": (20, 80)},
    "adipose": {"young_score": 0.18, "aged_score": 0.80, "age_range": (20, 80)},
}


class SenescenceAnalyzer:
    """Cellular senescence signature analyzer."""

    def __init__(self, rnaseq=None, singlecell=None, signatures=None,
                 senolytic_prediction=True, tissue="liver"):
        self.rnaseq_path = rnaseq
        self.singlecell_path = singlecell
        self.requested_signatures = (signatures or "fridman_sasp,reactome_senescence").split(",")
        self.senolytic_prediction = senolytic_prediction
        self.tissue = tissue.lower()
        self.expression_data = None

    # ----- data loading -----

    def _load_expression(self):
        """Load expression from TSV or generate demo data."""
        if self.rnaseq_path and os.path.isfile(self.rnaseq_path):
            return self._parse_tsv(self.rnaseq_path)
        return self._generate_demo_expression()

    def _parse_tsv(self, path):
        """Parse tab-delimited expression file (gene \\t value)."""
        expr = {}
        try:
            with open(path) as fh:
                header = fh.readline()
                for line in fh:
                    parts = line.strip().split("\t")
                    if len(parts) >= 2:
                        try:
                            expr[parts[0].upper()] = float(parts[1])
                        except ValueError:
                            continue
        except Exception:
            pass
        return expr

    def _generate_demo_expression(self):
        """Generate demo expression data simulating a moderately senescent tissue."""
        random.seed(2026)
        all_genes = set(FRIDMAN_UP + FRIDMAN_DOWN + REACTOME_SENESCENCE + SENMAYO_SUBSET)
        for cat_genes in SASP_COMPONENTS.values():
            all_genes.update(cat_genes)
        for stype in SENESCENCE_TYPE_MARKERS.values():
            for g in stype["positive"]:
                if not g.endswith("_low"):
                    all_genes.add(g)
        for drug in SENOLYTIC_DRUGS:
            all_genes.update(drug["markers_for_efficacy"])

        expr = {}
        # Senescence-upregulated genes: moderate-high expression
        for g in FRIDMAN_UP:
            expr[g] = round(random.gauss(8.0, 1.5), 3)
        # Proliferation genes (Fridman DOWN): low expression in senescent cells
        for g in FRIDMAN_DOWN:
            expr[g] = round(random.gauss(3.0, 1.0), 3)
        # Fill rest with moderate expression
        for g in all_genes:
            if g not in expr:
                expr[g] = round(random.gauss(5.5, 2.0), 3)
        # Ensure some SASP genes are elevated
        for g in ["IL6", "CXCL8", "CCL2", "MMP3", "SERPINE1"]:
            expr[g] = round(random.gauss(9.0, 1.2), 3)
        # Ensure BCL2 is high (for senolytic prediction)
        expr["BCL2"] = round(random.gauss(7.5, 1.0), 3)
        expr["BCL2L1"] = round(random.gauss(7.0, 1.0), 3)
        return expr

    # ----- scoring -----

    def _z_score(self, values):
        """Compute z-scores for a list of values."""
        if not values:
            return []
        mu = sum(values) / len(values)
        var = sum((v - mu) ** 2 for v in values) / max(len(values), 1)
        sd = math.sqrt(var) if var > 0 else 1.0
        return [(v - mu) / sd for v in values]

    def _compute_signature_score(self, sig_name):
        """Compute senescence score for a given signature."""
        expr = self.expression_data
        if sig_name == "fridman_sasp" or sig_name == "fridman":
            up_vals = [expr.get(g, 0.0) for g in FRIDMAN_UP]
            down_vals = [expr.get(g, 0.0) for g in FRIDMAN_DOWN]
            z_up = self._z_score(up_vals)
            z_down = self._z_score(down_vals)
            score = (sum(z_up) / max(len(z_up), 1)) - (sum(z_down) / max(len(z_down), 1))
            return {
                "signature": "Fridman UP/DOWN",
                "score": round(score, 4),
                "up_genes_mean_expr": round(sum(up_vals) / max(len(up_vals), 1), 3),
                "down_genes_mean_expr": round(sum(down_vals) / max(len(down_vals), 1), 3),
                "n_up_genes": len(FRIDMAN_UP),
                "n_down_genes": len(FRIDMAN_DOWN),
            }
        elif sig_name == "reactome_senescence" or sig_name == "reactome":
            vals = [expr.get(g, 0.0) for g in REACTOME_SENESCENCE]
            z_vals = self._z_score(vals)
            score = sum(z_vals) / max(len(z_vals), 1)
            return {
                "signature": "Reactome Cellular Senescence",
                "score": round(score, 4),
                "mean_expression": round(sum(vals) / max(len(vals), 1), 3),
                "n_genes": len(REACTOME_SENESCENCE),
            }
        elif sig_name == "senmayo":
            vals = [expr.get(g, 0.0) for g in SENMAYO_SUBSET]
            z_vals = self._z_score(vals)
            score = sum(z_vals) / max(len(z_vals), 1)
            return {
                "signature": "SenMayo (30-gene subset)",
                "score": round(score, 4),
                "mean_expression": round(sum(vals) / max(len(vals), 1), 3),
                "n_genes": len(SENMAYO_SUBSET),
            }
        return {"signature": sig_name, "score": None, "note": "Unknown signature"}

    def _compute_combined_senescence_score(self):
        """Combine available signature scores into a single 0-1 normalized score."""
        scores = []
        for sig in self.requested_signatures:
            result = self._compute_signature_score(sig.strip())
            if result.get("score") is not None:
                scores.append(result["score"])
        if not scores:
            return 0.5
        raw = sum(scores) / len(scores)
        # Sigmoid normalization to [0, 1]
        normalized = 1.0 / (1.0 + math.exp(-raw))
        return round(normalized, 4)

    # ----- SASP profiling -----

    def _sasp_profile(self):
        """Profile SASP components from expression data."""
        expr = self.expression_data
        profile = {}
        all_sasp_vals = []
        for category, genes in SASP_COMPONENTS.items():
            gene_data = []
            for g in genes:
                val = expr.get(g, 0.0)
                gene_data.append({"gene": g, "expression": round(val, 3)})
                all_sasp_vals.append(val)
            profile[category] = gene_data

        sasp_mean = sum(all_sasp_vals) / max(len(all_sasp_vals), 1)
        return {
            "components": profile,
            "sasp_score": round(sasp_mean, 4),
            "total_sasp_genes": len(all_sasp_vals),
            "interpretation": (
                "High SASP activity" if sasp_mean > 7.0 else
                "Moderate SASP activity" if sasp_mean > 5.0 else
                "Low SASP activity"
            ),
        }

    # ----- senescence type classification -----

    def _classify_senescence_type(self):
        """Classify the predominant senescence type based on marker expression."""
        expr = self.expression_data
        type_scores = {}
        for stype, info in SENESCENCE_TYPE_MARKERS.items():
            positive_genes = [g for g in info["positive"] if not g.endswith("_low")]
            low_genes = [g.replace("_low", "") for g in info["positive"] if g.endswith("_low")]
            pos_score = sum(expr.get(g, 0.0) for g in positive_genes) / max(len(positive_genes), 1)
            low_penalty = sum(max(0, expr.get(g, 0.0) - 4.0) for g in low_genes)
            type_scores[stype] = round(pos_score - low_penalty, 4)

        ranked = sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
        primary = ranked[0]
        return {
            "primary_type": primary[0],
            "primary_description": SENESCENCE_TYPE_MARKERS[primary[0]]["description"],
            "primary_score": primary[1],
            "all_type_scores": {k: v for k, v in ranked},
        }

    # ----- single-cell mode (conceptual) -----

    def _single_cell_analysis(self):
        """Conceptual single-cell senescence scoring."""
        if self.singlecell_path and os.path.isfile(self.singlecell_path):
            return {
                "status": "scRNA-seq file detected",
                "note": "Full single-cell analysis requires scanpy. "
                        "Providing conceptual analysis with demo data.",
            }
        # Demo single-cell results
        random.seed(777)
        n_cells = random.randint(3000, 8000)
        pct_senescent = round(random.uniform(5.0, 25.0), 1)
        return {
            "total_cells": n_cells,
            "senescent_cells": int(n_cells * pct_senescent / 100),
            "percent_senescent": pct_senescent,
            "cell_type_breakdown": {
                "fibroblasts": {"total": int(n_cells * 0.30),
                                "pct_senescent": round(random.uniform(10, 35), 1)},
                "epithelial": {"total": int(n_cells * 0.25),
                               "pct_senescent": round(random.uniform(3, 15), 1)},
                "endothelial": {"total": int(n_cells * 0.15),
                                "pct_senescent": round(random.uniform(5, 20), 1)},
                "immune": {"total": int(n_cells * 0.20),
                           "pct_senescent": round(random.uniform(2, 10), 1)},
                "other": {"total": int(n_cells * 0.10),
                          "pct_senescent": round(random.uniform(1, 8), 1)},
            },
            "data_source": "demo" if not (self.singlecell_path and
                                          os.path.isfile(self.singlecell_path)) else "file",
        }

    # ----- tissue aging clock -----

    def _tissue_aging_estimate(self, senescence_score):
        """Map senescence score to estimated biological age."""
        ref = TISSUE_SENESCENCE_REF.get(self.tissue, TISSUE_SENESCENCE_REF["liver"])
        young_s = ref["young_score"]
        aged_s = ref["aged_score"]
        age_lo, age_hi = ref["age_range"]

        if aged_s == young_s:
            frac = 0.5
        else:
            frac = max(0.0, min(1.0, (senescence_score - young_s) / (aged_s - young_s)))
        bio_age = age_lo + frac * (age_hi - age_lo)

        return {
            "tissue": self.tissue,
            "senescence_score_used": senescence_score,
            "estimated_biological_age": round(bio_age, 1),
            "reference_range": {"young": young_s, "aged": aged_s},
            "note": "Biological age estimate is approximate; based on tissue-specific senescence reference.",
        }

    # ----- senolytic drug prediction -----

    def _predict_senolytics(self, senescence_type):
        """Predict senolytic drug efficacy based on expression and senescence type."""
        expr = self.expression_data
        recommendations = []
        for drug in SENOLYTIC_DRUGS:
            marker_expr = {g: round(expr.get(g, 0.0), 3) for g in drug["markers_for_efficacy"]}
            avg_marker = sum(marker_expr.values()) / max(len(marker_expr), 1)
            type_match = senescence_type in drug["best_for"]
            efficacy_score = avg_marker * (1.3 if type_match else 0.8)
            if efficacy_score > 8.0:
                predicted_efficacy = "High"
            elif efficacy_score > 5.0:
                predicted_efficacy = "Moderate"
            else:
                predicted_efficacy = "Low"
            recommendations.append({
                "drug": drug["name"],
                "target": drug["target"],
                "mechanism": drug["mechanism"],
                "marker_expression": marker_expr,
                "type_match": type_match,
                "predicted_efficacy": predicted_efficacy,
                "efficacy_score": round(efficacy_score, 3),
                "caution": drug["caution"],
            })
        recommendations.sort(key=lambda x: x["efficacy_score"], reverse=True)
        return recommendations

    # ----- main analysis -----

    def analyze(self):
        """Run full senescence analysis."""
        self.expression_data = self._load_expression()

        # Signature scores
        signature_results = []
        for sig in self.requested_signatures:
            signature_results.append(self._compute_signature_score(sig.strip()))
        combined_score = self._compute_combined_senescence_score()

        # SASP profile
        sasp = self._sasp_profile()

        # Senescence type
        sen_type = self._classify_senescence_type()

        # Single-cell
        sc_summary = self._single_cell_analysis()

        # Tissue aging
        aging = self._tissue_aging_estimate(combined_score)

        # Senolytics
        senolytic_recs = None
        if self.senolytic_prediction:
            senolytic_recs = self._predict_senolytics(sen_type["primary_type"])

        result = {
            "analysis": "cellular_senescence",
            "timestamp": datetime.now().isoformat(),
            "tissue": self.tissue,
            "senescence_score": combined_score,
            "signature_scores": signature_results,
            "sasp_profile": sasp,
            "senescence_type": sen_type,
            "tissue_aging_estimate": aging,
            "single_cell_summary": sc_summary,
            "senolytic_recommendations": senolytic_recs,
            "data_source": {
                "rnaseq": "file" if (self.rnaseq_path and
                                     os.path.isfile(self.rnaseq_path)) else "demo",
                "singlecell": "file" if (self.singlecell_path and
                                         os.path.isfile(self.singlecell_path)) else "demo",
            },
        }
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Cellular Senescence Analyzer"
    )
    parser.add_argument("--rnaseq", default=None,
                        help="Path to bulk RNA-seq expression TSV (gene \\t value)")
    parser.add_argument("--singlecell", default=None,
                        help="Path to single-cell RNA-seq data (h5ad)")
    parser.add_argument("--signatures",
                        default="fridman_sasp,reactome_senescence",
                        help="Comma-separated senescence signatures to score")
    parser.add_argument("--senolytic_prediction", default="true",
                        help="Enable senolytic drug prediction (true/false)")
    parser.add_argument("--tissue", default="liver",
                        help="Tissue type (liver, skin, lung, kidney, brain, adipose)")
    parser.add_argument("--output", default=None,
                        help="Output directory or file for results JSON")

    args = parser.parse_args()

    senolytic_flag = args.senolytic_prediction.lower() in ("true", "1", "yes")

    analyzer = SenescenceAnalyzer(
        rnaseq=args.rnaseq,
        singlecell=args.singlecell,
        signatures=args.signatures,
        senolytic_prediction=senolytic_flag,
        tissue=args.tissue,
    )

    results = analyzer.analyze()

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or out_path.endswith("/"):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, "senescence_report.json")
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

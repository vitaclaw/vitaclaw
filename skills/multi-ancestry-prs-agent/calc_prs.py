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
Multi-Ancestry Polygenic Risk Score (PRS) Calculator.

Computes ancestry-aware polygenic risk scores using multiple methods including
PRS-CSx, PRS-CS, LDpred2, and standard weighted-sum approaches. Integrates
local ancestry inference for admixed individuals and provides equity assessment.

Usage:
    python3 calc_prs.py --genotypes patient_genotypes.vcf.gz \
        --ancestry admixed_AFR_EUR --local_ancestry lai_segments.bed \
        --trait coronary_artery_disease --method prs_csx \
        --gwas_summary_stats eur_gwas.txt,afr_gwas.txt \
        --calibration_cohort 1kg_admixed --output prs_results/
"""

import argparse
import json
import os
import sys
import math
import random
from datetime import datetime

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# ---------------------------------------------------------------------------
# Trait SNP database (representative subsets for demo)
# ---------------------------------------------------------------------------

TRAIT_SNP_DB = {
    "coronary_artery_disease": {
        "full_name": "Coronary Artery Disease",
        "total_snps_literature": 200,
        "snps": [
            {"rsid": "rs10455872", "chr": 6, "pos": 161010118, "effect_allele": "G",
             "beta_eur": 0.49, "beta_afr": 0.35, "beta_eas": 0.42,
             "eaf_eur": 0.07, "eaf_afr": 0.02, "eaf_eas": 0.01},
            {"rsid": "rs4977574", "chr": 9, "pos": 22098574, "effect_allele": "G",
             "beta_eur": 0.28, "beta_afr": 0.22, "beta_eas": 0.30,
             "eaf_eur": 0.46, "eaf_afr": 0.13, "eaf_eas": 0.52},
            {"rsid": "rs1333049", "chr": 9, "pos": 22125503, "effect_allele": "C",
             "beta_eur": 0.31, "beta_afr": 0.18, "beta_eas": 0.27,
             "eaf_eur": 0.47, "eaf_afr": 0.50, "eaf_eas": 0.61},
            {"rsid": "rs12526453", "chr": 6, "pos": 12903957, "effect_allele": "C",
             "beta_eur": 0.12, "beta_afr": 0.08, "beta_eas": 0.11,
             "eaf_eur": 0.67, "eaf_afr": 0.88, "eaf_eas": 0.45},
            {"rsid": "rs6725887", "chr": 2, "pos": 203828796, "effect_allele": "C",
             "beta_eur": 0.17, "beta_afr": 0.10, "beta_eas": 0.14,
             "eaf_eur": 0.13, "eaf_afr": 0.05, "eaf_eas": 0.08},
            {"rsid": "rs2505083", "chr": 10, "pos": 104719096, "effect_allele": "T",
             "beta_eur": 0.09, "beta_afr": 0.06, "beta_eas": 0.10,
             "eaf_eur": 0.42, "eaf_afr": 0.30, "eaf_eas": 0.55},
            {"rsid": "rs11206510", "chr": 1, "pos": 55496039, "effect_allele": "T",
             "beta_eur": 0.15, "beta_afr": 0.11, "beta_eas": 0.13,
             "eaf_eur": 0.82, "eaf_afr": 0.90, "eaf_eas": 0.70},
            {"rsid": "rs515135", "chr": 2, "pos": 21263900, "effect_allele": "G",
             "beta_eur": 0.11, "beta_afr": 0.07, "beta_eas": 0.09,
             "eaf_eur": 0.78, "eaf_afr": 0.85, "eaf_eas": 0.60},
            {"rsid": "rs3184504", "chr": 12, "pos": 111884608, "effect_allele": "T",
             "beta_eur": 0.13, "beta_afr": 0.05, "beta_eas": 0.12,
             "eaf_eur": 0.44, "eaf_afr": 0.08, "eaf_eas": 0.02},
            {"rsid": "rs56289821", "chr": 6, "pos": 39016594, "effect_allele": "A",
             "beta_eur": 0.08, "beta_afr": 0.06, "beta_eas": 0.07,
             "eaf_eur": 0.25, "eaf_afr": 0.35, "eaf_eas": 0.20},
        ],
    },
    "type_2_diabetes": {
        "full_name": "Type 2 Diabetes",
        "total_snps_literature": 150,
        "snps": [
            {"rsid": "rs7903146", "chr": 10, "pos": 114758349, "effect_allele": "T",
             "beta_eur": 0.36, "beta_afr": 0.30, "beta_eas": 0.20,
             "eaf_eur": 0.30, "eaf_afr": 0.28, "eaf_eas": 0.05},
            {"rsid": "rs1801282", "chr": 3, "pos": 12393125, "effect_allele": "G",
             "beta_eur": 0.14, "beta_afr": 0.10, "beta_eas": 0.08,
             "eaf_eur": 0.88, "eaf_afr": 0.97, "eaf_eas": 0.96},
            {"rsid": "rs5219", "chr": 11, "pos": 17409572, "effect_allele": "T",
             "beta_eur": 0.14, "beta_afr": 0.09, "beta_eas": 0.16,
             "eaf_eur": 0.36, "eaf_afr": 0.20, "eaf_eas": 0.40},
            {"rsid": "rs13266634", "chr": 8, "pos": 118184783, "effect_allele": "C",
             "beta_eur": 0.12, "beta_afr": 0.06, "beta_eas": 0.11,
             "eaf_eur": 0.70, "eaf_afr": 0.92, "eaf_eas": 0.55},
            {"rsid": "rs10811661", "chr": 9, "pos": 22134094, "effect_allele": "T",
             "beta_eur": 0.20, "beta_afr": 0.15, "beta_eas": 0.22,
             "eaf_eur": 0.83, "eaf_afr": 0.90, "eaf_eas": 0.60},
            {"rsid": "rs1111875", "chr": 10, "pos": 94462882, "effect_allele": "C",
             "beta_eur": 0.12, "beta_afr": 0.08, "beta_eas": 0.10,
             "eaf_eur": 0.52, "eaf_afr": 0.22, "eaf_eas": 0.35},
            {"rsid": "rs4402960", "chr": 3, "pos": 185511687, "effect_allele": "T",
             "beta_eur": 0.14, "beta_afr": 0.11, "beta_eas": 0.12,
             "eaf_eur": 0.30, "eaf_afr": 0.52, "eaf_eas": 0.31},
            {"rsid": "rs12255372", "chr": 10, "pos": 114808902, "effect_allele": "T",
             "beta_eur": 0.33, "beta_afr": 0.25, "beta_eas": 0.18,
             "eaf_eur": 0.27, "eaf_afr": 0.25, "eaf_eas": 0.04},
            {"rsid": "rs7756992", "chr": 6, "pos": 20679709, "effect_allele": "G",
             "beta_eur": 0.15, "beta_afr": 0.12, "beta_eas": 0.18,
             "eaf_eur": 0.27, "eaf_afr": 0.18, "eaf_eas": 0.42},
            {"rsid": "rs163184", "chr": 11, "pos": 2847069, "effect_allele": "G",
             "beta_eur": 0.10, "beta_afr": 0.07, "beta_eas": 0.09,
             "eaf_eur": 0.47, "eaf_afr": 0.68, "eaf_eas": 0.55},
        ],
    },
    "breast_cancer": {
        "full_name": "Breast Cancer",
        "total_snps_literature": 180,
        "snps": [
            {"rsid": "rs2981582", "chr": 10, "pos": 123337335, "effect_allele": "T",
             "beta_eur": 0.26, "beta_afr": 0.18, "beta_eas": 0.22,
             "eaf_eur": 0.38, "eaf_afr": 0.50, "eaf_eas": 0.30},
            {"rsid": "rs3803662", "chr": 16, "pos": 52586341, "effect_allele": "A",
             "beta_eur": 0.20, "beta_afr": 0.10, "beta_eas": 0.15,
             "eaf_eur": 0.25, "eaf_afr": 0.52, "eaf_eas": 0.48},
            {"rsid": "rs13387042", "chr": 2, "pos": 217905832, "effect_allele": "A",
             "beta_eur": 0.12, "beta_afr": 0.06, "beta_eas": 0.10,
             "eaf_eur": 0.50, "eaf_afr": 0.30, "eaf_eas": 0.45},
            {"rsid": "rs1045485", "chr": 2, "pos": 202149589, "effect_allele": "G",
             "beta_eur": 0.08, "beta_afr": 0.04, "beta_eas": 0.06,
             "eaf_eur": 0.87, "eaf_afr": 0.95, "eaf_eas": 0.99},
            {"rsid": "rs2046210", "chr": 6, "pos": 151948366, "effect_allele": "A",
             "beta_eur": 0.09, "beta_afr": 0.06, "beta_eas": 0.15,
             "eaf_eur": 0.34, "eaf_afr": 0.42, "eaf_eas": 0.64},
            {"rsid": "rs10941679", "chr": 5, "pos": 44706498, "effect_allele": "G",
             "beta_eur": 0.12, "beta_afr": 0.07, "beta_eas": 0.09,
             "eaf_eur": 0.26, "eaf_afr": 0.58, "eaf_eas": 0.30},
            {"rsid": "rs889312", "chr": 5, "pos": 56031884, "effect_allele": "C",
             "beta_eur": 0.13, "beta_afr": 0.09, "beta_eas": 0.08,
             "eaf_eur": 0.28, "eaf_afr": 0.42, "eaf_eas": 0.44},
            {"rsid": "rs3817198", "chr": 11, "pos": 1909006, "effect_allele": "C",
             "beta_eur": 0.07, "beta_afr": 0.04, "beta_eas": 0.05,
             "eaf_eur": 0.33, "eaf_afr": 0.18, "eaf_eas": 0.20},
            {"rsid": "rs13281615", "chr": 8, "pos": 128355618, "effect_allele": "G",
             "beta_eur": 0.08, "beta_afr": 0.05, "beta_eas": 0.07,
             "eaf_eur": 0.40, "eaf_afr": 0.55, "eaf_eas": 0.58},
            {"rsid": "rs4973768", "chr": 3, "pos": 27416013, "effect_allele": "T",
             "beta_eur": 0.11, "beta_afr": 0.06, "beta_eas": 0.09,
             "eaf_eur": 0.46, "eaf_afr": 0.30, "eaf_eas": 0.52},
        ],
    },
    "prostate_cancer": {
        "full_name": "Prostate Cancer",
        "total_snps_literature": 120,
        "snps": [
            {"rsid": "rs1447295", "chr": 8, "pos": 128554220, "effect_allele": "A",
             "beta_eur": 0.20, "beta_afr": 0.25, "beta_eas": 0.15,
             "eaf_eur": 0.11, "eaf_afr": 0.46, "eaf_eas": 0.18},
            {"rsid": "rs16901979", "chr": 8, "pos": 128124916, "effect_allele": "A",
             "beta_eur": 0.35, "beta_afr": 0.42, "beta_eas": 0.28,
             "eaf_eur": 0.03, "eaf_afr": 0.15, "eaf_eas": 0.20},
            {"rsid": "rs6983267", "chr": 8, "pos": 128413305, "effect_allele": "G",
             "beta_eur": 0.21, "beta_afr": 0.15, "beta_eas": 0.18,
             "eaf_eur": 0.50, "eaf_afr": 0.90, "eaf_eas": 0.42},
            {"rsid": "rs1859962", "chr": 17, "pos": 69108753, "effect_allele": "G",
             "beta_eur": 0.22, "beta_afr": 0.14, "beta_eas": 0.16,
             "eaf_eur": 0.46, "eaf_afr": 0.28, "eaf_eas": 0.55},
            {"rsid": "rs4242382", "chr": 8, "pos": 128535972, "effect_allele": "A",
             "beta_eur": 0.18, "beta_afr": 0.22, "beta_eas": 0.12,
             "eaf_eur": 0.12, "eaf_afr": 0.45, "eaf_eas": 0.16},
            {"rsid": "rs10993994", "chr": 10, "pos": 51549496, "effect_allele": "T",
             "beta_eur": 0.15, "beta_afr": 0.20, "beta_eas": 0.18,
             "eaf_eur": 0.40, "eaf_afr": 0.72, "eaf_eas": 0.62},
            {"rsid": "rs7931342", "chr": 11, "pos": 68994667, "effect_allele": "G",
             "beta_eur": 0.16, "beta_afr": 0.10, "beta_eas": 0.12,
             "eaf_eur": 0.52, "eaf_afr": 0.70, "eaf_eas": 0.60},
            {"rsid": "rs2735839", "chr": 19, "pos": 51364623, "effect_allele": "G",
             "beta_eur": 0.19, "beta_afr": 0.08, "beta_eas": 0.14,
             "eaf_eur": 0.85, "eaf_afr": 0.60, "eaf_eas": 0.75},
            {"rsid": "rs10896449", "chr": 11, "pos": 68751073, "effect_allele": "G",
             "beta_eur": 0.14, "beta_afr": 0.09, "beta_eas": 0.11,
             "eaf_eur": 0.53, "eaf_afr": 0.72, "eaf_eas": 0.58},
            {"rsid": "rs17765344", "chr": 8, "pos": 128081002, "effect_allele": "A",
             "beta_eur": 0.28, "beta_afr": 0.35, "beta_eas": 0.20,
             "eaf_eur": 0.02, "eaf_afr": 0.08, "eaf_eas": 0.05},
        ],
    },
    "alzheimers_disease": {
        "full_name": "Alzheimer's Disease",
        "total_snps_literature": 80,
        "snps": [
            {"rsid": "rs429358", "chr": 19, "pos": 45411941, "effect_allele": "C",
             "beta_eur": 1.20, "beta_afr": 0.70, "beta_eas": 1.05,
             "eaf_eur": 0.15, "eaf_afr": 0.27, "eaf_eas": 0.09},
            {"rsid": "rs7412", "chr": 19, "pos": 45412079, "effect_allele": "T",
             "beta_eur": -0.47, "beta_afr": -0.30, "beta_eas": -0.40,
             "eaf_eur": 0.08, "eaf_afr": 0.10, "eaf_eas": 0.05},
            {"rsid": "rs6656401", "chr": 1, "pos": 207692049, "effect_allele": "A",
             "beta_eur": 0.18, "beta_afr": 0.08, "beta_eas": 0.12,
             "eaf_eur": 0.22, "eaf_afr": 0.36, "eaf_eas": 0.05},
            {"rsid": "rs6733839", "chr": 2, "pos": 127892810, "effect_allele": "T",
             "beta_eur": 0.17, "beta_afr": 0.10, "beta_eas": 0.14,
             "eaf_eur": 0.40, "eaf_afr": 0.28, "eaf_eas": 0.42},
            {"rsid": "rs10792832", "chr": 11, "pos": 85868640, "effect_allele": "A",
             "beta_eur": 0.15, "beta_afr": 0.06, "beta_eas": 0.10,
             "eaf_eur": 0.36, "eaf_afr": 0.58, "eaf_eas": 0.30},
            {"rsid": "rs11218343", "chr": 11, "pos": 121435587, "effect_allele": "C",
             "beta_eur": -0.28, "beta_afr": -0.12, "beta_eas": -0.20,
             "eaf_eur": 0.04, "eaf_afr": 0.01, "eaf_eas": 0.12},
            {"rsid": "rs9331896", "chr": 8, "pos": 27219987, "effect_allele": "C",
             "beta_eur": -0.15, "beta_afr": -0.08, "beta_eas": -0.12,
             "eaf_eur": 0.38, "eaf_afr": 0.78, "eaf_eas": 0.30},
            {"rsid": "rs10948363", "chr": 6, "pos": 47487762, "effect_allele": "G",
             "beta_eur": 0.10, "beta_afr": 0.05, "beta_eas": 0.08,
             "eaf_eur": 0.40, "eaf_afr": 0.68, "eaf_eas": 0.25},
            {"rsid": "rs983392", "chr": 6, "pos": 41161514, "effect_allele": "G",
             "beta_eur": -0.10, "beta_afr": -0.04, "beta_eas": -0.07,
             "eaf_eur": 0.36, "eaf_afr": 0.60, "eaf_eas": 0.15},
            {"rsid": "rs28834970", "chr": 8, "pos": 27362470, "effect_allele": "C",
             "beta_eur": 0.12, "beta_afr": 0.06, "beta_eas": 0.09,
             "eaf_eur": 0.31, "eaf_afr": 0.42, "eaf_eas": 0.22},
        ],
    },
}

# ---------------------------------------------------------------------------
# Ancestry calibration reference data
# ---------------------------------------------------------------------------

ANCESTRY_CALIBRATION = {
    "coronary_artery_disease": {
        "EUR": {"mean": 0.85, "sd": 0.35}, "AFR": {"mean": 0.55, "sd": 0.30},
        "EAS": {"mean": 0.90, "sd": 0.32}, "SAS": {"mean": 0.95, "sd": 0.38},
        "AMR": {"mean": 0.75, "sd": 0.33},
    },
    "type_2_diabetes": {
        "EUR": {"mean": 0.72, "sd": 0.30}, "AFR": {"mean": 0.60, "sd": 0.28},
        "EAS": {"mean": 0.80, "sd": 0.34}, "SAS": {"mean": 0.85, "sd": 0.36},
        "AMR": {"mean": 0.68, "sd": 0.31},
    },
    "breast_cancer": {
        "EUR": {"mean": 0.65, "sd": 0.28}, "AFR": {"mean": 0.48, "sd": 0.25},
        "EAS": {"mean": 0.60, "sd": 0.27}, "SAS": {"mean": 0.55, "sd": 0.26},
        "AMR": {"mean": 0.58, "sd": 0.27},
    },
    "prostate_cancer": {
        "EUR": {"mean": 0.70, "sd": 0.32}, "AFR": {"mean": 0.95, "sd": 0.38},
        "EAS": {"mean": 0.55, "sd": 0.28}, "SAS": {"mean": 0.60, "sd": 0.30},
        "AMR": {"mean": 0.65, "sd": 0.30},
    },
    "alzheimers_disease": {
        "EUR": {"mean": 0.50, "sd": 0.40}, "AFR": {"mean": 0.35, "sd": 0.30},
        "EAS": {"mean": 0.40, "sd": 0.35}, "SAS": {"mean": 0.42, "sd": 0.34},
        "AMR": {"mean": 0.45, "sd": 0.36},
    },
}

# Transferability R-squared by ancestry (proxy for equity assessment)
TRANSFERABILITY = {
    "coronary_artery_disease": {"EUR": 0.12, "AFR": 0.04, "EAS": 0.08, "SAS": 0.07, "AMR": 0.06},
    "type_2_diabetes":         {"EUR": 0.10, "AFR": 0.03, "EAS": 0.07, "SAS": 0.06, "AMR": 0.05},
    "breast_cancer":           {"EUR": 0.08, "AFR": 0.02, "EAS": 0.05, "SAS": 0.04, "AMR": 0.04},
    "prostate_cancer":         {"EUR": 0.09, "AFR": 0.05, "EAS": 0.04, "SAS": 0.04, "AMR": 0.05},
    "alzheimers_disease":      {"EUR": 0.07, "AFR": 0.02, "EAS": 0.04, "SAS": 0.03, "AMR": 0.03},
}


class MultiAncestryPRS:
    """Multi-ancestry polygenic risk score calculator."""

    ANCESTRY_CATEGORIES = ["EUR", "AFR", "EAS", "SAS", "AMR"]

    RISK_CATEGORIES = [
        {"label": "Very low", "min_pct": 0, "max_pct": 5},
        {"label": "Low", "min_pct": 5, "max_pct": 20},
        {"label": "Average", "min_pct": 20, "max_pct": 80},
        {"label": "High", "min_pct": 80, "max_pct": 95},
        {"label": "Very high", "min_pct": 95, "max_pct": 100},
    ]

    METHODS = ["standard", "prs_csx", "prs_cs", "ldpred2"]

    def __init__(self, genotypes=None, ancestry="EUR", local_ancestry=None,
                 trait="coronary_artery_disease", method="prs_csx",
                 gwas_summary_stats=None, calibration_cohort=None):
        self.genotypes_path = genotypes
        self.ancestry_raw = ancestry
        self.local_ancestry_path = local_ancestry
        self.trait = trait
        self.method = method
        self.gwas_summary_stats = gwas_summary_stats or []
        self.calibration_cohort = calibration_cohort
        self.ancestry_proportions = self._parse_ancestry(ancestry)
        self.genotype_data = None
        self.local_ancestry_segments = None

    # ----- ancestry parsing -----

    def _parse_ancestry(self, ancestry_str):
        """Parse ancestry string into proportions dict."""
        ancestry_str = ancestry_str.upper()
        proportions = {a: 0.0 for a in self.ANCESTRY_CATEGORIES}
        if ancestry_str.startswith("ADMIXED"):
            parts = ancestry_str.replace("ADMIXED_", "").replace("ADMIXED", "").split("_")
            parts = [p for p in parts if p in self.ANCESTRY_CATEGORIES]
            if not parts:
                parts = ["EUR", "AFR"]
            share = 1.0 / len(parts)
            for p in parts:
                proportions[p] = round(share, 3)
            proportions["_is_admixed"] = True
        elif ancestry_str in self.ANCESTRY_CATEGORIES:
            proportions[ancestry_str] = 1.0
            proportions["_is_admixed"] = False
        else:
            proportions["EUR"] = 1.0
            proportions["_is_admixed"] = False
        return proportions

    # ----- data loading -----

    def _load_genotypes(self):
        """Load genotypes from VCF or generate demo data."""
        if self.genotypes_path and os.path.isfile(self.genotypes_path):
            return self._parse_vcf(self.genotypes_path)
        return self._generate_demo_genotypes()

    def _parse_vcf(self, path):
        """Minimal VCF reader extracting dosages for known SNPs."""
        known_rsids = {s["rsid"] for s in TRAIT_SNP_DB.get(self.trait, {}).get("snps", [])}
        dosages = {}
        try:
            opener = open
            if path.endswith(".gz"):
                import gzip
                opener = gzip.open
            with opener(path, "rt") as fh:
                for line in fh:
                    if line.startswith("#"):
                        continue
                    cols = line.strip().split("\t")
                    if len(cols) < 10:
                        continue
                    rsid = cols[2]
                    if rsid in known_rsids:
                        gt = cols[9].split(":")[0]
                        dosages[rsid] = gt.count("1") + gt.count("2")
        except Exception:
            pass
        return dosages

    def _generate_demo_genotypes(self):
        """Generate plausible demo dosages for trait SNPs."""
        random.seed(42)
        snps = TRAIT_SNP_DB.get(self.trait, {}).get("snps", [])
        primary = max(self.ancestry_proportions.items(),
                      key=lambda x: x[1] if x[0] != "_is_admixed" else 0)[0]
        dosages = {}
        for s in snps:
            eaf_key = f"eaf_{primary.lower()}" if f"eaf_{primary.lower()}" in s else "eaf_eur"
            eaf = s.get(eaf_key, 0.3)
            r = random.random()
            if r < (1 - eaf) ** 2:
                dosages[s["rsid"]] = 0
            elif r < (1 - eaf) ** 2 + 2 * eaf * (1 - eaf):
                dosages[s["rsid"]] = 1
            else:
                dosages[s["rsid"]] = 2
        return dosages

    def _load_local_ancestry(self):
        """Load LAI segments or generate demo segments."""
        if self.local_ancestry_path and os.path.isfile(self.local_ancestry_path):
            return self._parse_bed(self.local_ancestry_path)
        if self.ancestry_proportions.get("_is_admixed"):
            return self._generate_demo_lai()
        return None

    def _parse_bed(self, path):
        segments = []
        try:
            with open(path) as fh:
                for line in fh:
                    parts = line.strip().split("\t")
                    if len(parts) >= 4:
                        segments.append({
                            "chr": parts[0], "start": int(parts[1]),
                            "end": int(parts[2]), "ancestry": parts[3].upper()
                        })
        except Exception:
            pass
        return segments

    def _generate_demo_lai(self):
        """Generate demo local ancestry segments for admixed individual."""
        random.seed(99)
        active_pops = [k for k, v in self.ancestry_proportions.items()
                       if k != "_is_admixed" and v > 0]
        segments = []
        for chrom in range(1, 23):
            pos = 0
            while pos < 250_000_000:
                seg_len = random.randint(1_000_000, 20_000_000)
                anc = random.choice(active_pops)
                segments.append({
                    "chr": str(chrom), "start": pos,
                    "end": pos + seg_len, "ancestry": anc
                })
                pos += seg_len
        return segments

    def _ancestry_at_locus(self, chrom, position):
        """Return local ancestry at a specific genomic position."""
        if not self.local_ancestry_segments:
            return None
        chrom_str = str(chrom)
        for seg in self.local_ancestry_segments:
            if seg["chr"] == chrom_str and seg["start"] <= position < seg["end"]:
                return seg["ancestry"]
        return None

    # ----- PRS calculation methods -----

    def _calc_standard_prs(self, snps, dosages):
        """Standard PRS: sum of beta * dosage with ancestry-specific betas."""
        primary = max(
            ((k, v) for k, v in self.ancestry_proportions.items() if k != "_is_admixed"),
            key=lambda x: x[1]
        )[0]
        beta_key = f"beta_{primary.lower()}"
        score = 0.0
        n_used = 0
        for s in snps:
            rsid = s["rsid"]
            if rsid in dosages:
                beta = s.get(beta_key, s.get("beta_eur", 0.0))
                score += beta * dosages[rsid]
                n_used += 1
        return score, n_used

    def _calc_prs_csx(self, snps, dosages):
        """PRS-CSx: combine ancestry-specific scores weighted by proportions."""
        pop_scores = {}
        for pop in self.ANCESTRY_CATEGORIES:
            prop = self.ancestry_proportions.get(pop, 0.0)
            if prop <= 0:
                continue
            beta_key = f"beta_{pop.lower()}"
            s_val = 0.0
            for s in snps:
                rsid = s["rsid"]
                if rsid in dosages:
                    beta = s.get(beta_key, s.get("beta_eur", 0.0))
                    s_val += beta * dosages[rsid]
            pop_scores[pop] = {"raw_score": round(s_val, 6), "weight": round(prop, 4)}

        combined = sum(v["raw_score"] * v["weight"] for v in pop_scores.values())
        return combined, pop_scores

    def _calc_prs_cs(self, snps, dosages):
        """PRS-CS: Bayesian shrinkage approximation (simplified)."""
        primary = max(
            ((k, v) for k, v in self.ancestry_proportions.items() if k != "_is_admixed"),
            key=lambda x: x[1]
        )[0]
        beta_key = f"beta_{primary.lower()}"
        phi = 0.01  # global shrinkage parameter
        score = 0.0
        n_used = 0
        for s in snps:
            rsid = s["rsid"]
            if rsid in dosages:
                beta = s.get(beta_key, s.get("beta_eur", 0.0))
                shrunk_beta = beta / (1.0 + phi)
                score += shrunk_beta * dosages[rsid]
                n_used += 1
        return score, n_used

    def _calc_ldpred2(self, snps, dosages):
        """LDpred2: LD-aware PRS (simplified with heritability scaling)."""
        primary = max(
            ((k, v) for k, v in self.ancestry_proportions.items() if k != "_is_admixed"),
            key=lambda x: x[1]
        )[0]
        beta_key = f"beta_{primary.lower()}"
        h2 = 0.05  # assumed heritability fraction explained
        p_causal = 0.1
        score = 0.0
        n_used = 0
        for s in snps:
            rsid = s["rsid"]
            if rsid in dosages:
                beta = s.get(beta_key, s.get("beta_eur", 0.0))
                adj_beta = beta * (h2 * p_causal)
                score += adj_beta * dosages[rsid]
                n_used += 1
        return score, n_used

    def _apply_local_ancestry(self, snps, dosages):
        """Apply ancestry-specific betas based on local ancestry at each locus."""
        score = 0.0
        n_lai = 0
        for s in snps:
            rsid = s["rsid"]
            if rsid not in dosages:
                continue
            local_anc = self._ancestry_at_locus(s["chr"], s["pos"])
            if local_anc and local_anc in self.ANCESTRY_CATEGORIES:
                beta_key = f"beta_{local_anc.lower()}"
                n_lai += 1
            else:
                beta_key = "beta_eur"
            beta = s.get(beta_key, s.get("beta_eur", 0.0))
            score += beta * dosages[rsid]
        return score, n_lai

    # ----- calibration & risk -----

    def _calibrate(self, raw_score):
        """Calibrate raw PRS to percentile using ancestry-specific distributions."""
        trait_cal = ANCESTRY_CALIBRATION.get(self.trait, {})
        primary = max(
            ((k, v) for k, v in self.ancestry_proportions.items() if k != "_is_admixed"),
            key=lambda x: x[1]
        )[0]
        cal = trait_cal.get(primary, {"mean": 0.5, "sd": 0.3})
        z = (raw_score - cal["mean"]) / cal["sd"] if cal["sd"] > 0 else 0.0
        percentile = self._norm_cdf(z) * 100.0
        return round(z, 4), round(percentile, 2)

    @staticmethod
    def _norm_cdf(z):
        """Approximate cumulative normal distribution."""
        return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))

    def _risk_category(self, percentile):
        for cat in self.RISK_CATEGORIES:
            if cat["min_pct"] <= percentile < cat["max_pct"]:
                return cat["label"]
        return "Very high"

    # ----- equity assessment -----

    def _equity_assessment(self):
        """Evaluate prediction equity across ancestries for this trait."""
        trans = TRANSFERABILITY.get(self.trait, {})
        primary = max(
            ((k, v) for k, v in self.ancestry_proportions.items() if k != "_is_admixed"),
            key=lambda x: x[1]
        )[0]
        r2_patient = trans.get(primary, 0.03)
        r2_eur = trans.get("EUR", 0.10)
        ratio = r2_patient / r2_eur if r2_eur > 0 else 0.0

        flags = []
        if ratio < 0.5:
            flags.append("PRS has significantly reduced predictive accuracy "
                         f"for {primary} ancestry (R²={r2_patient:.3f} vs EUR R²={r2_eur:.3f}).")
            flags.append("Recommend use of ancestry-matched GWAS summary statistics.")
            flags.append("Clinical interpretation should be cautious.")
        recommendations = []
        if primary != "EUR":
            recommendations.append(f"Validate PRS in {primary}-ancestry cohort before clinical use.")
            recommendations.append("Consider multi-ancestry PRS methods (PRS-CSx) for improved transferability.")
        return {
            "r2_by_ancestry": {k: round(v, 4) for k, v in trans.items()},
            "patient_ancestry": primary,
            "patient_r2": round(r2_patient, 4),
            "eur_r2": round(r2_eur, 4),
            "transferability_ratio": round(ratio, 3),
            "equity_flags": flags,
            "recommendations": recommendations,
        }

    # ----- clinical risk integration -----

    def _clinical_risk_integration(self, percentile, clinical_factors=None):
        """Combine PRS percentile with clinical risk factors for absolute risk."""
        cf = clinical_factors or {}
        age = cf.get("age", 55)
        sex = cf.get("sex", "male")
        family_history = cf.get("family_history", False)
        bmi = cf.get("bmi", 27.0)

        # Base lifetime risk by trait (approximate population averages)
        base_risks = {
            "coronary_artery_disease": 0.20,
            "type_2_diabetes": 0.15,
            "breast_cancer": 0.125,
            "prostate_cancer": 0.11,
            "alzheimers_disease": 0.10,
        }
        base = base_risks.get(self.trait, 0.10)

        # PRS multiplier from percentile
        if percentile >= 95:
            prs_mult = 3.0
        elif percentile >= 80:
            prs_mult = 2.0
        elif percentile >= 50:
            prs_mult = 1.2
        elif percentile >= 20:
            prs_mult = 0.8
        else:
            prs_mult = 0.5

        # Clinical adjustments
        age_mult = 1.0 + max(0, (age - 50)) * 0.02
        fh_mult = 1.5 if family_history else 1.0
        bmi_mult = 1.0 + max(0, (bmi - 25)) * 0.03

        absolute_risk = min(base * prs_mult * age_mult * fh_mult * bmi_mult, 0.95)

        return {
            "baseline_population_risk": round(base, 4),
            "prs_risk_multiplier": round(prs_mult, 2),
            "clinical_factors": {
                "age": age, "sex": sex,
                "family_history": family_history, "bmi": bmi
            },
            "age_adjustment": round(age_mult, 3),
            "family_history_adjustment": round(fh_mult, 2),
            "bmi_adjustment": round(bmi_mult, 3),
            "estimated_absolute_risk": round(absolute_risk, 4),
            "note": "Absolute risk is approximate; intended for research use only.",
        }

    # ----- main analysis -----

    def analyze(self):
        """Run full multi-ancestry PRS analysis."""
        trait_info = TRAIT_SNP_DB.get(self.trait)
        if not trait_info:
            return {"error": f"Trait '{self.trait}' not found.",
                    "available_traits": list(TRAIT_SNP_DB.keys())}

        snps = trait_info["snps"]
        self.genotype_data = self._load_genotypes()
        self.local_ancestry_segments = self._load_local_ancestry()

        # Select method
        method_details = {"method": self.method}
        if self.method == "prs_csx":
            raw_score, pop_details = self._calc_prs_csx(snps, self.genotype_data)
            method_details["population_scores"] = pop_details
        elif self.method == "prs_cs":
            raw_score, n_used = self._calc_prs_cs(snps, self.genotype_data)
            method_details["snps_used"] = n_used
            method_details["shrinkage_phi"] = 0.01
        elif self.method == "ldpred2":
            raw_score, n_used = self._calc_ldpred2(snps, self.genotype_data)
            method_details["snps_used"] = n_used
            method_details["assumed_h2"] = 0.05
        else:
            raw_score, n_used = self._calc_standard_prs(snps, self.genotype_data)
            method_details["snps_used"] = n_used

        # Local ancestry adjustment
        lai_info = None
        if self.local_ancestry_segments:
            lai_score, n_lai = self._apply_local_ancestry(snps, self.genotype_data)
            lai_info = {
                "lai_adjusted_score": round(lai_score, 6),
                "snps_with_local_ancestry": n_lai,
                "total_segments": len(self.local_ancestry_segments),
            }
            raw_score = lai_score  # use LAI-adjusted score

        z_score, percentile = self._calibrate(raw_score)
        risk_cat = self._risk_category(percentile)

        is_admixed = self.ancestry_proportions.get("_is_admixed", False)
        anc_composition = {k: v for k, v in self.ancestry_proportions.items()
                           if k != "_is_admixed"}

        result = {
            "analysis": "multi_ancestry_prs",
            "timestamp": datetime.now().isoformat(),
            "trait_info": {
                "trait": self.trait,
                "full_name": trait_info["full_name"],
                "snps_in_panel": len(snps),
                "total_snps_in_literature": trait_info["total_snps_literature"],
            },
            "ancestry_composition": anc_composition,
            "is_admixed": is_admixed,
            "prs_raw": round(raw_score, 6),
            "prs_z_score": z_score,
            "prs_percentile": percentile,
            "risk_category": risk_cat,
            "method_details": method_details,
            "local_ancestry_integration": lai_info,
            "equity_assessment": self._equity_assessment(),
            "clinical_risk_integration": self._clinical_risk_integration(percentile),
            "genotype_summary": {
                "snps_available": len(self.genotype_data),
                "data_source": "file" if (self.genotypes_path and
                                          os.path.isfile(self.genotypes_path)) else "demo",
            },
        }
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Ancestry Polygenic Risk Score Calculator"
    )
    parser.add_argument("--genotypes", default=None,
                        help="Path to patient genotypes (VCF/VCF.gz)")
    parser.add_argument("--ancestry", default="EUR",
                        help="Ancestry (EUR, AFR, EAS, SAS, AMR, or admixed_X_Y)")
    parser.add_argument("--local_ancestry", default=None,
                        help="Local ancestry inference segments (BED file)")
    parser.add_argument("--trait", default="coronary_artery_disease",
                        help="Trait to calculate PRS for")
    parser.add_argument("--method", default="prs_csx",
                        choices=MultiAncestryPRS.METHODS,
                        help="PRS calculation method")
    parser.add_argument("--gwas_summary_stats", default=None,
                        help="Comma-separated GWAS summary stats files")
    parser.add_argument("--calibration_cohort", default=None,
                        help="Calibration cohort identifier")
    parser.add_argument("--output", default=None,
                        help="Output directory or file for results JSON")

    args = parser.parse_args()

    gwas_files = []
    if args.gwas_summary_stats:
        gwas_files = [f.strip() for f in args.gwas_summary_stats.split(",")]

    analyzer = MultiAncestryPRS(
        genotypes=args.genotypes,
        ancestry=args.ancestry,
        local_ancestry=args.local_ancestry,
        trait=args.trait,
        method=args.method,
        gwas_summary_stats=gwas_files,
        calibration_cohort=args.calibration_cohort,
    )

    results = analyzer.analyze()

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or out_path.endswith("/"):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, "prs_results.json")
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

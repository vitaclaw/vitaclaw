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
CHIP Analysis – Clonal Hematopoiesis of Indeterminate Potential detection & risk.

Usage:
    python3 chip_analysis.py \
        --variants blood_variants.vcf \
        --cbc_data patient_cbc.csv \
        --clinical_data patient_demographics.json \
        --vaf_threshold 0.02 \
        --age 65 \
        --calculate_cvd_risk true \
        --output chip_analysis/
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    pd = None

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

CHIP_GENES = [
    "DNMT3A", "TET2", "ASXL1", "JAK2", "TP53", "PPM1D", "SF3B1", "SRSF2",
    "U2AF1", "IDH1", "IDH2", "RUNX1", "EZH2", "CBL", "GNAS", "GNB1",
    "NRAS", "KRAS", "BCOR", "BCORL1", "STAG2", "CUX1", "ZRSR2", "PHF6",
    "SETD2",
]

HIGH_RISK_GENES = {"TP53", "SRSF2", "IDH1", "IDH2", "RUNX1", "U2AF1", "EZH2", "SF3B1"}

CVD_RISK_MULTIPLIERS = {
    "DNMT3A": 1.7,
    "TET2":   1.9,
    "JAK2":   12.0,  # especially for thrombosis
    "ASXL1":  2.0,
    "TP53":   1.5,
    "PPM1D":  1.3,
    "SF3B1":  1.4,
    "SRSF2":  1.6,
    "U2AF1":  1.5,
    "IDH1":   1.3,
    "IDH2":   1.3,
}

MDS_AML_PROGRESSION_TABLE = {
    "TP53":  {"base_annual_risk_pct": 3.0, "vaf_multiplier": 2.0},
    "SRSF2": {"base_annual_risk_pct": 2.5, "vaf_multiplier": 1.8},
    "IDH1":  {"base_annual_risk_pct": 2.0, "vaf_multiplier": 1.5},
    "IDH2":  {"base_annual_risk_pct": 2.0, "vaf_multiplier": 1.5},
    "RUNX1": {"base_annual_risk_pct": 2.0, "vaf_multiplier": 1.5},
    "U2AF1": {"base_annual_risk_pct": 1.8, "vaf_multiplier": 1.5},
    "EZH2":  {"base_annual_risk_pct": 1.5, "vaf_multiplier": 1.3},
    "SF3B1": {"base_annual_risk_pct": 1.0, "vaf_multiplier": 1.2},
    "DNMT3A": {"base_annual_risk_pct": 0.5, "vaf_multiplier": 1.2},
    "TET2":  {"base_annual_risk_pct": 0.5, "vaf_multiplier": 1.2},
    "ASXL1": {"base_annual_risk_pct": 1.5, "vaf_multiplier": 1.5},
    "JAK2":  {"base_annual_risk_pct": 0.8, "vaf_multiplier": 1.3},
}

CHRS_COMPONENTS = {
    "age_gte_65": 1,
    "vaf_gte_0.1": 1,
    "multi_chip_mutations": 1,
    "high_risk_gene": 2,
    "cytopenia": 1,
    "rdw_gt_15": 1,
}

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_VARIANTS = [
    {"gene": "DNMT3A", "variant": "p.Arg882His", "vaf": 0.12, "type": "missense", "chr": "chr2", "pos": 25457242},
    {"gene": "TET2", "variant": "p.Gln1034Ter", "vaf": 0.05, "type": "nonsense", "chr": "chr4", "pos": 106196829},
    {"gene": "ASXL1", "variant": "p.Gly646TrpfsTer12", "vaf": 0.03, "type": "frameshift", "chr": "chr20", "pos": 32434638},
]

DEMO_CBC = {
    "wbc": 6.8,
    "rbc": 4.1,
    "hgb": 12.5,
    "hct": 37.8,
    "mcv": 92.2,
    "platelets": 185,
    "anc": 4.2,
    "rdw": 15.8,
}

DEMO_CLINICAL = {
    "patient_id": "CHIP-2026-0092",
    "age": 68,
    "sex": "male",
    "smoking": True,
    "hypertension": True,
    "diabetes": False,
    "prior_chemo": False,
    "cytopenias": [],
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class CHIPAnalyzer:
    """CHIP detection and cardiovascular / myeloid risk assessment."""

    def __init__(
        self,
        variants_path=None,
        cbc_path=None,
        clinical_path=None,
        vaf_threshold=0.02,
        age=None,
        calculate_cvd_risk=True,
    ):
        self.vaf_threshold = float(vaf_threshold)
        self.calculate_cvd = str(calculate_cvd_risk).lower() in ("true", "1", "yes")
        self.variants = self._load_variants(variants_path)
        self.cbc = self._load_json(cbc_path, DEMO_CBC)
        self.clinical = self._load_json(clinical_path, DEMO_CLINICAL)
        if age is not None:
            self.clinical["age"] = int(age)
        self.timestamp = datetime.now().isoformat()

    # --- loaders --------------------------------------------------------

    @staticmethod
    def _load_json(path, default):
        if path and os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext == ".json":
                with open(path) as fh:
                    return json.load(fh)
            if ext == ".csv" and pd is not None:
                df = pd.read_csv(path)
                return df.to_dict(orient="records")[0] if len(df) else default
        return default

    def _load_variants(self, path):
        if path and os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext == ".json":
                with open(path) as fh:
                    return json.load(fh)
            if ext == ".vcf":
                return self._parse_vcf(path)
            if ext == ".csv" and pd is not None:
                df = pd.read_csv(path)
                return df.to_dict(orient="records")
        return DEMO_VARIANTS

    @staticmethod
    def _parse_vcf(path):
        variants = []
        with open(path) as fh:
            for line in fh:
                if line.startswith("#"):
                    continue
                parts = line.strip().split("\t")
                if len(parts) >= 8:
                    info = parts[7]
                    gene = ""
                    vaf = 0.0
                    for field in info.split(";"):
                        if field.startswith("GENE="):
                            gene = field.split("=")[1]
                        if field.startswith("VAF="):
                            try:
                                vaf = float(field.split("=")[1])
                            except ValueError:
                                pass
                    variants.append({
                        "chr": parts[0], "pos": int(parts[1]),
                        "ref": parts[3], "alt": parts[4],
                        "gene": gene, "vaf": vaf,
                    })
        return variants if variants else DEMO_VARIANTS

    # --- classification -------------------------------------------------

    def _classify_variants(self):
        classified = []
        for v in self.variants:
            gene = v.get("gene", "")
            vaf = v.get("vaf", 0)
            if gene not in CHIP_GENES:
                continue
            if vaf >= self.vaf_threshold:
                label = "CHIP"
            elif 0.01 <= vaf < self.vaf_threshold:
                label = "CH (clonal hematopoiesis, sub-CHIP VAF)"
            else:
                label = "Below detection threshold"
            classified.append({**v, "classification": label, "is_high_risk_gene": gene in HIGH_RISK_GENES})
        return classified

    def _check_ccus(self, chip_variants):
        has_chip = any(v["classification"] == "CHIP" for v in chip_variants)
        cytopenias = self.clinical.get("cytopenias", [])
        hgb = self.cbc.get("hgb", 14)
        anc = self.cbc.get("anc", 4)
        platelets = self.cbc.get("platelets", 250)

        cytopenia_detected = []
        if hgb < 10:
            cytopenia_detected.append("anemia")
        if anc < 1.8:
            cytopenia_detected.append("neutropenia")
        if platelets < 150:
            cytopenia_detected.append("thrombocytopenia")
        cytopenia_detected.extend(cytopenias)

        if has_chip and cytopenia_detected:
            return "CCUS", cytopenia_detected
        return None, cytopenia_detected

    # --- CHRS -----------------------------------------------------------

    def _compute_chrs(self, chip_variants):
        score = 0
        details = {}
        age = self.clinical.get("age", 50)

        age_hit = age >= 65
        details["age_gte_65"] = {"met": age_hit, "points": 1 if age_hit else 0}
        score += 1 if age_hit else 0

        max_vaf = max((v.get("vaf", 0) for v in chip_variants), default=0)
        vaf_hit = max_vaf >= 0.1
        details["vaf_gte_0.1"] = {"met": vaf_hit, "max_vaf": max_vaf, "points": 1 if vaf_hit else 0}
        score += 1 if vaf_hit else 0

        n_chip = sum(1 for v in chip_variants if v["classification"] == "CHIP")
        multi = n_chip >= 2
        details["multi_chip_mutations"] = {"met": multi, "count": n_chip, "points": 1 if multi else 0}
        score += 1 if multi else 0

        hrg = any(v.get("is_high_risk_gene") for v in chip_variants)
        details["high_risk_gene"] = {"met": hrg, "points": 2 if hrg else 0}
        score += 2 if hrg else 0

        _, cytopenias = self._check_ccus(chip_variants)
        cyto = len(cytopenias) > 0
        details["cytopenia"] = {"met": cyto, "details": cytopenias, "points": 1 if cyto else 0}
        score += 1 if cyto else 0

        rdw = self.cbc.get("rdw", 13)
        rdw_hit = rdw > 15
        details["rdw_gt_15"] = {"met": rdw_hit, "value": rdw, "points": 1 if rdw_hit else 0}
        score += 1 if rdw_hit else 0

        if score <= 1:
            risk = "LOW"
        elif score <= 3:
            risk = "INTERMEDIATE"
        else:
            risk = "HIGH"

        return {"chrs_score": score, "risk_category": risk, "components": details}

    # --- CVD risk -------------------------------------------------------

    def _cvd_risk(self, chip_variants):
        if not self.calculate_cvd:
            return {"calculated": False, "reason": "CVD risk calculation not requested"}
        gene_multipliers = {}
        max_multiplier = 1.0
        for v in chip_variants:
            gene = v.get("gene", "")
            if gene in CVD_RISK_MULTIPLIERS and v["classification"] == "CHIP":
                m = CVD_RISK_MULTIPLIERS[gene]
                gene_multipliers[gene] = m
                max_multiplier = max(max_multiplier, m)

        risk_level = "STANDARD"
        if max_multiplier >= 5.0:
            risk_level = "VERY HIGH"
        elif max_multiplier >= 2.0:
            risk_level = "HIGH"
        elif max_multiplier >= 1.5:
            risk_level = "MODERATE"

        return {
            "calculated": True,
            "gene_multipliers": gene_multipliers,
            "max_cvd_risk_multiplier": max_multiplier,
            "risk_level": risk_level,
            "note": "JAK2 V617F carries ~12x thrombosis risk; consider anti-platelet / anticoagulation.",
        }

    # --- progression risk -----------------------------------------------

    def _progression_risk(self, chip_variants):
        risks = []
        for v in chip_variants:
            gene = v.get("gene", "")
            vaf = v.get("vaf", 0)
            table = MDS_AML_PROGRESSION_TABLE.get(gene)
            if table and v["classification"] == "CHIP":
                annual = table["base_annual_risk_pct"]
                if vaf >= 0.1:
                    annual *= table["vaf_multiplier"]
                risks.append({
                    "gene": gene,
                    "vaf": vaf,
                    "estimated_annual_progression_risk_pct": round(annual, 2),
                })
        n_mutations = sum(1 for v in chip_variants if v["classification"] == "CHIP")
        overall = "LOW"
        if n_mutations >= 2 or any(r["estimated_annual_progression_risk_pct"] >= 2.0 for r in risks):
            overall = "MODERATE-HIGH"
        elif any(r["estimated_annual_progression_risk_pct"] >= 1.0 for r in risks):
            overall = "MODERATE"
        return {
            "per_gene": risks,
            "overall_risk": overall,
            "n_chip_mutations": n_mutations,
            "recommendation": "Annual CBC monitoring; consider bone marrow biopsy if cytopenias develop." if overall != "LOW" else "Annual CBC monitoring.",
        }

    # --- ctDNA filter flags ---------------------------------------------

    def _ctdna_flags(self, chip_variants):
        flags = []
        for v in chip_variants:
            if v["classification"] in ("CHIP", "CH (clonal hematopoiesis, sub-CHIP VAF)"):
                flags.append({
                    "gene": v.get("gene"),
                    "variant": v.get("variant", f"{v.get('ref','')}->{v.get('alt','')}"),
                    "vaf": v.get("vaf"),
                    "flag": "EXCLUDE_FROM_LIQUID_BIOPSY",
                    "reason": "CHIP/CH variant – likely hematopoietic origin, not tumor-derived",
                })
        return flags

    # --- main -----------------------------------------------------------

    def analyze(self) -> dict:
        chip_variants = self._classify_variants()
        ccus_status, cytopenias = self._check_ccus(chip_variants)
        chrs = self._compute_chrs(chip_variants)

        overall_classification = "No CHIP detected"
        if ccus_status == "CCUS":
            overall_classification = "CCUS (Clonal Cytopenia of Undetermined Significance)"
        elif any(v["classification"] == "CHIP" for v in chip_variants):
            overall_classification = "CHIP"
        elif any(v["classification"].startswith("CH") for v in chip_variants):
            overall_classification = "CH (sub-CHIP threshold)"

        return {
            "analysis": "CHIP Detection & Risk Assessment",
            "timestamp": self.timestamp,
            "patient_id": self.clinical.get("patient_id", "UNKNOWN"),
            "vaf_threshold": self.vaf_threshold,
            "chip_variants": chip_variants,
            "classification": overall_classification,
            "ccus_status": ccus_status,
            "cytopenias": cytopenias,
            "chrs_score": chrs,
            "cvd_risk": self._cvd_risk(chip_variants),
            "progression_risk": self._progression_risk(chip_variants),
            "ctdna_filter_flags": self._ctdna_flags(chip_variants),
            "chip_gene_panel": CHIP_GENES,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="CHIP Analysis – Clonal hematopoiesis detection & risk")
    parser.add_argument("--variants", type=str, default=None, help="Blood variants VCF/JSON/CSV")
    parser.add_argument("--cbc_data", type=str, default=None, help="Patient CBC CSV/JSON")
    parser.add_argument("--clinical_data", type=str, default=None, help="Patient demographics JSON")
    parser.add_argument("--vaf_threshold", type=float, default=0.02, help="VAF threshold for CHIP (default 0.02)")
    parser.add_argument("--age", type=int, default=None, help="Patient age")
    parser.add_argument("--calculate_cvd_risk", type=str, default="true", help="Calculate CVD risk (true/false)")
    parser.add_argument("--output", type=str, default=None, help="Output path (file or directory)")
    args = parser.parse_args()

    analyzer = CHIPAnalyzer(
        variants_path=args.variants,
        cbc_path=args.cbc_data,
        clinical_path=args.clinical_data,
        vaf_threshold=args.vaf_threshold,
        age=args.age,
        calculate_cvd_risk=args.calculate_cvd_risk,
    )
    result = analyzer.analyze()
    output_json = json.dumps(result, indent=2, default=str)

    if args.output:
        out = args.output
        if os.path.isdir(out) or out.endswith("/"):
            os.makedirs(out, exist_ok=True)
            out = os.path.join(out, "chip_analysis.json")
        else:
            os.makedirs(os.path.dirname(out) if os.path.dirname(out) else ".", exist_ok=True)
        with open(out, "w") as fh:
            fh.write(output_json)
        print(f"[INFO] Report written to {out}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

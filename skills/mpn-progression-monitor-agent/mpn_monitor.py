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
MPN Progression Monitor – MPN prognostic scoring and molecular tracking.

Usage:
    python3 mpn_monitor.py \
        --patient_id MF_001 \
        --molecular_data serial_mutations.csv \
        --cbc_data serial_cbc.csv \
        --clinical_data symptoms.json \
        --mpn_type pmf \
        --baseline_date 2024-01-15 \
        --calculate_scores dipss,mipss70 \
        --output mpn_monitoring/
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

DIPSS_CRITERIA = {
    "age_gt_65":             {"points": 1, "description": "Age > 65 years"},
    "hgb_lt_10":             {"points": 2, "description": "Hemoglobin < 10 g/dL"},
    "wbc_gt_25":             {"points": 1, "description": "WBC > 25 x10^9/L"},
    "circulating_blasts_gte_1": {"points": 1, "description": "Circulating blasts >= 1%"},
    "constitutional_symptoms": {"points": 1, "description": "Constitutional symptoms present"},
}

DIPSS_RISK = {
    0:     {"category": "Low", "median_survival_yr": "Not reached"},
    1:     {"category": "Intermediate-1", "median_survival_yr": 14.2},
    2:     {"category": "Intermediate-1", "median_survival_yr": 14.2},
    3:     {"category": "Intermediate-2", "median_survival_yr": 4.0},
    4:     {"category": "Intermediate-2", "median_survival_yr": 4.0},
    5:     {"category": "High", "median_survival_yr": 1.5},
    6:     {"category": "High", "median_survival_yr": 1.5},
}

MIPSS70_CLINICAL = {
    "hgb_lt_10":              {"points": 1, "description": "Hemoglobin < 10 g/dL"},
    "wbc_gt_25":              {"points": 2, "description": "WBC > 25 x10^9/L"},
    "plt_lt_100":             {"points": 2, "description": "Platelets < 100 x10^9/L"},
    "blasts_gte_2":           {"points": 1, "description": "Peripheral blood blasts >= 2%"},
    "constitutional_symptoms": {"points": 1, "description": "Constitutional symptoms"},
    "bm_fibrosis_gte_2":     {"points": 1, "description": "Bone marrow fibrosis grade >= 2"},
}

MIPSS70_MOLECULAR = {
    "calr_type1_bonus":       {"points": -2, "description": "CALR type 1/like (favorable)"},
    "asxl1_mutation":         {"points": 1, "description": "ASXL1 mutation"},
    "srsf2_mutation":         {"points": 1, "description": "SRSF2 mutation"},
    "ezh2_mutation":          {"points": 1, "description": "EZH2 mutation"},
    "idh1_2_mutation":        {"points": 1, "description": "IDH1/2 mutation"},
    "u2af1_q157":             {"points": 1, "description": "U2AF1 Q157 mutation"},
    "absence_calr_type1":     {"points": 2, "description": "Absence of CALR type 1/like"},
}

MIPSS70_RISK = {
    "Low":  {"range": (0, 1), "description": "Low risk"},
    "Intermediate": {"range": (2, 4), "description": "Intermediate risk"},
    "High": {"range": (5, 99), "description": "High risk"},
}

DRIVER_MUTATIONS = ["JAK2", "CALR", "MPL"]

HMR_GENES = ["ASXL1", "SRSF2", "EZH2", "IDH1", "IDH2", "U2AF1", "TP53"]

TREATMENT_AGENTS = {
    "ruxolitinib": {
        "class": "JAK1/2 inhibitor",
        "response_markers": ["spleen_reduction", "symptom_improvement", "driver_vaf_change"],
    },
    "fedratinib": {
        "class": "JAK2 inhibitor",
        "response_markers": ["spleen_reduction", "symptom_improvement"],
    },
    "momelotinib": {
        "class": "JAK1/2 + ACVR1 inhibitor",
        "response_markers": ["anemia_improvement", "spleen_reduction"],
    },
    "pacritinib": {
        "class": "JAK2/IRAK1 inhibitor",
        "response_markers": ["spleen_reduction", "platelet_sparing"],
    },
}

BLAST_TRANSFORMATION_INDICATORS = [
    {"indicator": "Rising blast percentage", "threshold": ">=10% PB blasts"},
    {"indicator": "New cytogenetic abnormality", "threshold": "Complex karyotype"},
    {"indicator": "Rapidly falling platelets", "threshold": "<50 x10^9/L"},
    {"indicator": "TP53 mutation acquisition", "threshold": "Any detectable VAF"},
    {"indicator": "Increasing LDH", "threshold": ">2x ULN trend"},
    {"indicator": "New RUNX1 or IDH mutation", "threshold": "Any detectable VAF"},
]

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_MOLECULAR = [
    {"date": "2024-01-15", "gene": "JAK2", "variant": "V617F", "vaf": 0.45},
    {"date": "2024-01-15", "gene": "ASXL1", "variant": "G646WfsX12", "vaf": 0.08},
    {"date": "2024-07-01", "gene": "JAK2", "variant": "V617F", "vaf": 0.52},
    {"date": "2024-07-01", "gene": "ASXL1", "variant": "G646WfsX12", "vaf": 0.10},
    {"date": "2025-01-10", "gene": "JAK2", "variant": "V617F", "vaf": 0.38},
    {"date": "2025-01-10", "gene": "ASXL1", "variant": "G646WfsX12", "vaf": 0.09},
    {"date": "2025-07-15", "gene": "JAK2", "variant": "V617F", "vaf": 0.35},
    {"date": "2025-07-15", "gene": "ASXL1", "variant": "G646WfsX12", "vaf": 0.11},
]

DEMO_CBC = [
    {"date": "2024-01-15", "hgb": 9.2, "wbc": 28.5, "platelets": 310, "blasts_pct": 1},
    {"date": "2024-07-01", "hgb": 9.8, "wbc": 22.1, "platelets": 280, "blasts_pct": 1},
    {"date": "2025-01-10", "hgb": 10.5, "wbc": 15.3, "platelets": 245, "blasts_pct": 0},
    {"date": "2025-07-15", "hgb": 10.2, "wbc": 16.8, "platelets": 220, "blasts_pct": 1},
]

DEMO_CLINICAL = {
    "patient_id": "MF_001",
    "age": 68,
    "sex": "male",
    "mpn_type": "PMF",
    "constitutional_symptoms": True,
    "spleen_size_cm": 18,
    "bm_fibrosis_grade": 2,
    "karyotype": "normal",
    "treatment": {"agent": "ruxolitinib", "start_date": "2024-02-01", "dose_mg": 20},
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class MPNMonitor:
    """MPN progression monitoring and prognostic scoring."""

    def __init__(
        self,
        patient_id=None,
        molecular_path=None,
        cbc_path=None,
        clinical_path=None,
        mpn_type="pmf",
        baseline_date=None,
        calculate_scores=None,
    ):
        self.patient_id = patient_id or "UNKNOWN"
        self.mpn_type = mpn_type.upper() if mpn_type else "PMF"
        self.baseline_date = baseline_date or "2024-01-15"
        self.requested_scores = [s.strip().lower() for s in (calculate_scores or "dipss,mipss70").split(",")]
        self.molecular = self._load_serial(molecular_path, DEMO_MOLECULAR)
        self.cbc_series = self._load_serial(cbc_path, DEMO_CBC)
        self.clinical = self._load_json(clinical_path, DEMO_CLINICAL)
        if patient_id:
            self.clinical["patient_id"] = patient_id
        self.timestamp = datetime.now().isoformat()

    # --- loaders --------------------------------------------------------

    @staticmethod
    def _load_json(path, default):
        if path and os.path.isfile(path):
            with open(path) as fh:
                return json.load(fh)
        return default

    @staticmethod
    def _load_serial(path, default):
        if path and os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext == ".json":
                with open(path) as fh:
                    return json.load(fh)
            if ext == ".csv" and pd is not None:
                df = pd.read_csv(path)
                return df.to_dict(orient="records")
        return default

    # --- helper: latest CBC ---------------------------------------------

    def _latest_cbc(self):
        if not self.cbc_series:
            return {}
        return sorted(self.cbc_series, key=lambda r: r.get("date", ""), reverse=True)[0]

    # --- DIPSS ----------------------------------------------------------

    def _score_dipss(self):
        cbc = self._latest_cbc()
        age = self.clinical.get("age", 50)
        score = 0
        details = {}

        checks = [
            ("age_gt_65", age > 65),
            ("hgb_lt_10", cbc.get("hgb", 14) < 10),
            ("wbc_gt_25", cbc.get("wbc", 7) > 25),
            ("circulating_blasts_gte_1", cbc.get("blasts_pct", 0) >= 1),
            ("constitutional_symptoms", self.clinical.get("constitutional_symptoms", False)),
        ]
        for key, met in checks:
            pts = DIPSS_CRITERIA[key]["points"] if met else 0
            details[key] = {"met": met, "points": pts, "description": DIPSS_CRITERIA[key]["description"]}
            score += pts

        risk_info = DIPSS_RISK.get(score, DIPSS_RISK[6])
        return {
            "model": "DIPSS",
            "score": score,
            "risk_category": risk_info["category"],
            "median_survival_yr": risk_info["median_survival_yr"],
            "components": details,
        }

    # --- MIPSS70+ -------------------------------------------------------

    def _score_mipss70(self):
        cbc = self._latest_cbc()
        score = 0
        details = {}

        clinical_checks = [
            ("hgb_lt_10", cbc.get("hgb", 14) < 10),
            ("wbc_gt_25", cbc.get("wbc", 7) > 25),
            ("plt_lt_100", cbc.get("platelets", 250) < 100),
            ("blasts_gte_2", cbc.get("blasts_pct", 0) >= 2),
            ("constitutional_symptoms", self.clinical.get("constitutional_symptoms", False)),
            ("bm_fibrosis_gte_2", self.clinical.get("bm_fibrosis_grade", 0) >= 2),
        ]
        for key, met in clinical_checks:
            pts = MIPSS70_CLINICAL[key]["points"] if met else 0
            details[key] = {"met": met, "points": pts}
            score += pts

        # molecular checks – scan latest molecular data
        latest_genes = set()
        if self.molecular:
            latest_date = max(r.get("date", "") for r in self.molecular)
            latest_genes = {r["gene"] for r in self.molecular if r.get("date") == latest_date}

        has_calr_type1 = "CALR" in latest_genes  # simplified
        mol_checks = [
            ("calr_type1_bonus", has_calr_type1),
            ("asxl1_mutation", "ASXL1" in latest_genes),
            ("srsf2_mutation", "SRSF2" in latest_genes),
            ("ezh2_mutation", "EZH2" in latest_genes),
            ("idh1_2_mutation", "IDH1" in latest_genes or "IDH2" in latest_genes),
            ("u2af1_q157", "U2AF1" in latest_genes),
            ("absence_calr_type1", not has_calr_type1),
        ]
        for key, met in mol_checks:
            pts = MIPSS70_MOLECULAR[key]["points"] if met else 0
            details[key] = {"met": met, "points": pts}
            score += pts

        score = max(score, 0)  # floor at 0

        risk_cat = "High"
        for cat, info in MIPSS70_RISK.items():
            lo, hi = info["range"]
            if lo <= score <= hi:
                risk_cat = cat
                break

        # very high molecular risk
        hmr_count = sum(1 for g in HMR_GENES if g in latest_genes)
        vhmr = hmr_count >= 2

        return {
            "model": "MIPSS70+",
            "score": score,
            "risk_category": risk_cat,
            "very_high_molecular_risk": vhmr,
            "hmr_mutations_count": hmr_count,
            "components": details,
        }

    # --- driver mutation tracking ---------------------------------------

    def _driver_trends(self):
        trends = {}
        for gene in DRIVER_MUTATIONS:
            pts = [
                {"date": r["date"], "vaf": r["vaf"]}
                for r in self.molecular if r.get("gene") == gene
            ]
            if pts:
                pts.sort(key=lambda x: x["date"])
                first = pts[0]["vaf"]
                last = pts[-1]["vaf"]
                delta = round(last - first, 4)
                direction = "increasing" if delta > 0.02 else ("decreasing" if delta < -0.02 else "stable")
                trends[gene] = {"timepoints": pts, "delta_vaf": delta, "direction": direction}
        return trends

    # --- HMR tracking ---------------------------------------------------

    def _hmr_trends(self):
        trends = {}
        for gene in HMR_GENES:
            pts = [
                {"date": r["date"], "vaf": r["vaf"]}
                for r in self.molecular if r.get("gene") == gene
            ]
            if pts:
                pts.sort(key=lambda x: x["date"])
                first = pts[0]["vaf"]
                last = pts[-1]["vaf"]
                delta = round(last - first, 4)
                direction = "increasing" if delta > 0.01 else ("decreasing" if delta < -0.01 else "stable")
                trends[gene] = {"timepoints": pts, "delta_vaf": delta, "direction": direction}
        return trends

    # --- blast transformation risk --------------------------------------

    def _transformation_risk(self):
        cbc = self._latest_cbc()
        flags = []
        blasts = cbc.get("blasts_pct", 0)
        if blasts >= 10:
            flags.append({"indicator": "Elevated blast percentage", "value": f"{blasts}%", "severity": "HIGH"})
        elif blasts >= 5:
            flags.append({"indicator": "Rising blast percentage", "value": f"{blasts}%", "severity": "MODERATE"})

        platelets = cbc.get("platelets", 250)
        if platelets < 50:
            flags.append({"indicator": "Severe thrombocytopenia", "value": f"{platelets} x10^9/L", "severity": "HIGH"})

        latest_genes = set()
        if self.molecular:
            latest_date = max(r.get("date", "") for r in self.molecular)
            latest_genes = {r["gene"] for r in self.molecular if r.get("date") == latest_date}
        if "TP53" in latest_genes:
            flags.append({"indicator": "TP53 mutation detected", "severity": "HIGH"})
        if "RUNX1" in latest_genes:
            flags.append({"indicator": "RUNX1 mutation detected", "severity": "MODERATE"})
        if "IDH1" in latest_genes or "IDH2" in latest_genes:
            flags.append({"indicator": "IDH1/2 mutation detected", "severity": "MODERATE"})

        overall = "LOW"
        if any(f["severity"] == "HIGH" for f in flags):
            overall = "HIGH"
        elif any(f["severity"] == "MODERATE" for f in flags):
            overall = "MODERATE"
        return {"overall_risk": overall, "flags": flags, "reference_indicators": BLAST_TRANSFORMATION_INDICATORS}

    # --- treatment response ---------------------------------------------

    def _treatment_response(self):
        tx = self.clinical.get("treatment")
        if not tx:
            return {"status": "No treatment data available"}

        agent = tx.get("agent", "unknown")
        agent_info = TREATMENT_AGENTS.get(agent, {"class": "Unknown", "response_markers": []})

        # compare baseline vs latest CBC
        if len(self.cbc_series) < 2:
            return {"agent": agent, "class": agent_info["class"], "assessment": "Insufficient data for response assessment"}

        sorted_cbc = sorted(self.cbc_series, key=lambda r: r.get("date", ""))
        baseline = sorted_cbc[0]
        latest = sorted_cbc[-1]

        spleen_baseline = self.clinical.get("spleen_size_cm", 0)
        response_items = []

        # haematologic parameters
        hgb_change = round((latest.get("hgb", 0) - baseline.get("hgb", 0)), 1)
        wbc_change = round((latest.get("wbc", 0) - baseline.get("wbc", 0)), 1)
        response_items.append({"parameter": "Hemoglobin change", "value": f"{hgb_change:+.1f} g/dL"})
        response_items.append({"parameter": "WBC change", "value": f"{wbc_change:+.1f} x10^9/L"})

        # driver VAF change
        driver_trends = self._driver_trends()
        for gene, trend in driver_trends.items():
            response_items.append({"parameter": f"{gene} VAF change", "value": f"{trend['delta_vaf']:+.4f}", "direction": trend["direction"]})

        return {
            "agent": agent,
            "class": agent_info["class"],
            "start_date": tx.get("start_date"),
            "dose_mg": tx.get("dose_mg"),
            "response_markers": response_items,
        }

    # --- main -----------------------------------------------------------

    def analyze(self) -> dict:
        scores = {}
        if "dipss" in self.requested_scores:
            scores["dipss"] = self._score_dipss()
        if "mipss70" in self.requested_scores:
            scores["mipss70_plus"] = self._score_mipss70()

        # determine overall risk
        risk_cats = [s.get("risk_category", "Unknown") for s in scores.values()]
        overall = "Unknown"
        for level in ("High", "Intermediate-2", "Intermediate", "Intermediate-1", "Low"):
            if level in risk_cats:
                overall = level
                break

        return {
            "analysis": "MPN Progression Monitoring",
            "timestamp": self.timestamp,
            "patient_id": self.clinical.get("patient_id", self.patient_id),
            "mpn_type": self.mpn_type,
            "baseline_date": self.baseline_date,
            "prognostic_scores": scores,
            "risk_category": overall,
            "molecular_trends": {
                "driver_mutations": self._driver_trends(),
                "hmr_mutations": self._hmr_trends(),
            },
            "transformation_risk": self._transformation_risk(),
            "treatment_response": self._treatment_response(),
            "cbc_series_summary": {
                "n_timepoints": len(self.cbc_series),
                "latest": self._latest_cbc(),
            },
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MPN Monitor – Progression monitoring & prognostic scoring")
    parser.add_argument("--patient_id", type=str, default=None, help="Patient identifier")
    parser.add_argument("--molecular_data", type=str, default=None, help="Serial mutations CSV/JSON")
    parser.add_argument("--cbc_data", type=str, default=None, help="Serial CBC CSV/JSON")
    parser.add_argument("--clinical_data", type=str, default=None, help="Clinical/symptoms JSON")
    parser.add_argument("--mpn_type", type=str, default="pmf", choices=["pmf", "pv", "et"], help="MPN type")
    parser.add_argument("--baseline_date", type=str, default=None, help="Baseline date (YYYY-MM-DD)")
    parser.add_argument("--calculate_scores", type=str, default="dipss,mipss70", help="Comma-separated scores")
    parser.add_argument("--output", type=str, default=None, help="Output path (file or directory)")
    args = parser.parse_args()

    monitor = MPNMonitor(
        patient_id=args.patient_id,
        molecular_path=args.molecular_data,
        cbc_path=args.cbc_data,
        clinical_path=args.clinical_data,
        mpn_type=args.mpn_type,
        baseline_date=args.baseline_date,
        calculate_scores=args.calculate_scores,
    )
    result = monitor.analyze()
    output_json = json.dumps(result, indent=2, default=str)

    if args.output:
        out = args.output
        if os.path.isdir(out) or out.endswith("/"):
            os.makedirs(out, exist_ok=True)
            out = os.path.join(out, "mpn_monitoring.json")
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

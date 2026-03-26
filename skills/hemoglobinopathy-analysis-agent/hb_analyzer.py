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
Hemoglobin Analyzer – Hemoglobin disorder analysis.

Usage:
    python3 hb_analyzer.py \
        --hplc_data chromatogram.csv \
        --retention_times peak_times.json \
        --cbc cbc_results.json \
        --peripheral_smear smear_findings.txt \
        --molecular hbb_sequencing.vcf \
        --output hb_report.json
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
# Domain constants – HPLC windows & normal ranges
# ---------------------------------------------------------------------------

HPLC_RETENTION_WINDOWS = {
    "HbF":  {"min_min": 0.8, "max_min": 1.6, "typical_min": 1.2},
    "HbA":  {"min_min": 2.0, "max_min": 2.8, "typical_min": 2.4},
    "HbA2": {"min_min": 3.2, "max_min": 4.0, "typical_min": 3.6},
    "HbD":  {"min_min": 3.8, "max_min": 4.4, "typical_min": 4.1},
    "HbS":  {"min_min": 4.0, "max_min": 4.6, "typical_min": 4.3},
    "HbC":  {"min_min": 4.8, "max_min": 5.4, "typical_min": 5.1},
    "HbE":  {"min_min": 3.3, "max_min": 3.9, "typical_min": 3.6},
}

NORMAL_RANGES = {
    "HbA":  {"low": 95.0, "high": 98.0},
    "HbA2": {"low": 2.0,  "high": 3.3},
    "HbF":  {"low": 0.0,  "high": 1.0},
    "HbS":  {"low": 0.0,  "high": 0.0},
    "HbC":  {"low": 0.0,  "high": 0.0},
}

CLASSIFICATION_RULES = [
    {"name": "Sickle Cell Disease (HbSS)", "criteria": lambda f: f.get("HbS", 0) > 50 and f.get("HbA", 100) < 10},
    {"name": "Sickle Cell Trait (HbAS)", "criteria": lambda f: 30 <= f.get("HbS", 0) <= 45 and f.get("HbA", 0) > 50},
    {"name": "HbSC Disease", "criteria": lambda f: f.get("HbS", 0) > 40 and f.get("HbC", 0) > 40},
    {"name": "Beta-Thalassemia Major", "criteria": lambda f: f.get("HbF", 0) > 90 and f.get("HbA", 100) < 10},
    {"name": "Beta-Thalassemia Minor", "criteria": lambda f: 3.5 <= f.get("HbA2", 0) <= 7.0 and f.get("HbF", 0) < 5},
    {"name": "HbC Disease", "criteria": lambda f: f.get("HbC", 0) > 85},
    {"name": "HbE Disease", "criteria": lambda f: f.get("HbE", 0) > 80},
    {"name": "HbE/Beta-Thal", "criteria": lambda f: f.get("HbE", 0) > 40 and f.get("HbF", 0) > 10},
    {"name": "HbS/Beta-Thal", "criteria": lambda f: f.get("HbS", 0) > 50 and 10 <= f.get("HbA", 0) <= 30},
    {"name": "HPFH (Hereditary Persistence of Fetal Hb)", "criteria": lambda f: f.get("HbF", 0) > 15 and f.get("HbA", 0) > 60},
]

# ~50 common hemoglobin variants
VARIANT_DATABASE = {
    "HbS":       {"aa_change": "Glu6Val (beta)", "clinical": "Sickle cell disease/trait", "severity": "major"},
    "HbC":       {"aa_change": "Glu6Lys (beta)", "clinical": "HbC disease/trait", "severity": "moderate"},
    "HbE":       {"aa_change": "Glu26Lys (beta)", "clinical": "HbE disease, common in SE Asia", "severity": "mild-moderate"},
    "HbD-Punjab": {"aa_change": "Glu121Gln (beta)", "clinical": "Usually benign", "severity": "mild"},
    "HbD-Iran":  {"aa_change": "Glu22Gln (beta)", "clinical": "Benign", "severity": "benign"},
    "HbO-Arab":  {"aa_change": "Glu121Lys (beta)", "clinical": "Mild hemolysis, may interact with HbS", "severity": "mild"},
    "Hb Lepore": {"aa_change": "delta-beta fusion", "clinical": "Thalassemia phenotype", "severity": "moderate"},
    "HbH":       {"aa_change": "beta4 tetramer", "clinical": "Alpha-thal intermedia", "severity": "moderate"},
    "Hb Barts":  {"aa_change": "gamma4 tetramer", "clinical": "Hydrops fetalis", "severity": "lethal"},
    "Hb Constant Spring": {"aa_change": "Ter142Gln (alpha)", "clinical": "Alpha-thal variant", "severity": "mild"},
    "HbJ-Baltimore": {"aa_change": "Gly16Asp (beta)", "clinical": "Benign", "severity": "benign"},
    "HbG-Philadelphia": {"aa_change": "Asn68Lys (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Hasharon": {"aa_change": "Asp47His (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Zurich":  {"aa_change": "His63Arg (beta)", "clinical": "Drug-induced hemolysis", "severity": "mild"},
    "Hb Koln":    {"aa_change": "Val98Met (beta)", "clinical": "Unstable Hb, Heinz bodies", "severity": "moderate"},
    "Hb Hammersmith": {"aa_change": "Phe42Ser (beta)", "clinical": "Unstable Hb", "severity": "moderate"},
    "Hb Gun Hill": {"aa_change": "del 91-95 (beta)", "clinical": "Unstable Hb", "severity": "moderate"},
    "Hb Kansas":  {"aa_change": "Asn102Thr (beta)", "clinical": "Low O2 affinity, cyanosis", "severity": "mild"},
    "Hb Chesapeake": {"aa_change": "Arg92Leu (alpha)", "clinical": "High O2 affinity, polycythemia", "severity": "mild"},
    "Hb Yakima":  {"aa_change": "Asp99His (beta)", "clinical": "High O2 affinity", "severity": "mild"},
    "Hb Rainier": {"aa_change": "Tyr145Cys (beta)", "clinical": "High O2 affinity", "severity": "mild"},
    "Hb Bethesda": {"aa_change": "Tyr145His (beta)", "clinical": "High O2 affinity", "severity": "mild"},
    "Hb Malmo":   {"aa_change": "His97Gln (beta)", "clinical": "High O2 affinity", "severity": "mild"},
    "Hb Hope":    {"aa_change": "Gly136Asp (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb N-Baltimore": {"aa_change": "Lys95Glu (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb Camden":  {"aa_change": "Gly47Arg (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb Porto Alegre": {"aa_change": "Ser9Cys (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb Wayne":   {"aa_change": "frameshift alpha", "clinical": "Alpha-thal", "severity": "mild"},
    "Hb Quong Sze": {"aa_change": "Leu125Pro (alpha)", "clinical": "Unstable, alpha-thal", "severity": "moderate"},
    "Hb Suan Dok": {"aa_change": "Leu109Arg (alpha)", "clinical": "Unstable", "severity": "moderate"},
    "Hb Adana":   {"aa_change": "Gly59Asp (alpha)", "clinical": "Unstable, hydrops risk", "severity": "severe"},
    "Hb Pakse":   {"aa_change": "Ter142Tyr (alpha)", "clinical": "Like Hb Constant Spring", "severity": "mild"},
    "Hb Malay":   {"aa_change": "Ala19Glu (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Setif":   {"aa_change": "Asp94Tyr (alpha)", "clinical": "High O2 affinity", "severity": "mild"},
    "HbA2-prime": {"aa_change": "delta chain variant", "clinical": "Benign delta variant", "severity": "benign"},
    "Hb Leiden":  {"aa_change": "del Glu6-7 (beta)", "clinical": "Unstable", "severity": "moderate"},
    "Hb Freiburg": {"aa_change": "del Val23 (beta)", "clinical": "Unstable Hb", "severity": "moderate"},
    "Hb Titusville": {"aa_change": "Asp94Asn (alpha)", "clinical": "Mildly unstable", "severity": "mild"},
    "Hb Montreal": {"aa_change": "del 73-75 (beta)", "clinical": "Unstable, hemolysis", "severity": "moderate"},
    "Hb J-Cape Town": {"aa_change": "Arg92Gln (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Ottawa":  {"aa_change": "Gly15Arg (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Korle-Bu": {"aa_change": "Asp73Asn (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb Stanleyville-II": {"aa_change": "Asn78Lys (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Q-India": {"aa_change": "Asp64His (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Hekinan": {"aa_change": "Asp56Gly (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb Agenogi": {"aa_change": "Glu90Lys (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb Sogn":    {"aa_change": "Leu14Arg (beta)", "clinical": "Benign", "severity": "benign"},
    "Hb I-Texas": {"aa_change": "Lys16Glu (alpha)", "clinical": "Benign", "severity": "benign"},
    "Hb Tarrant": {"aa_change": "Asp126Asn (alpha)", "clinical": "High O2 affinity", "severity": "mild"},
}

MANAGEMENT_RECS = {
    "Sickle Cell Disease (HbSS)": [
        "Hydroxyurea therapy to increase HbF",
        "Folic acid supplementation",
        "Pneumococcal & meningococcal vaccination",
        "Penicillin prophylaxis (children)",
        "Screen for stroke with transcranial Doppler",
        "Chronic transfusion if indicated",
        "Consider L-glutamine, crizanlizumab, voxelotor",
    ],
    "Beta-Thalassemia Major": [
        "Regular transfusion programme (target pre-transfusion Hb 9-10.5 g/dL)",
        "Iron chelation therapy (deferasirox, deferoxamine, deferiprone)",
        "Monitor ferritin, liver/cardiac iron by MRI",
        "Assess for allogeneic HSCT candidacy",
        "Luspatercept if transfusion dependent",
    ],
    "Beta-Thalassemia Minor": [
        "Genetic counselling",
        "Avoid unnecessary iron supplementation",
        "Monitor Hb periodically; usually no treatment needed",
    ],
    "default": [
        "Genetic counselling recommended",
        "Periodic monitoring of CBC and hemoglobin fractions",
        "Specialist haematology referral as appropriate",
    ],
}

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_HPLC = {
    "HbA": 55.2, "HbA2": 3.1, "HbF": 1.8, "HbS": 38.5, "HbC": 0.0, "HbE": 0.0, "HbD": 0.0,
}

DEMO_CBC = {
    "rbc": 5.2,
    "hgb": 12.1,
    "hct": 36.5,
    "mcv": 70.2,
    "mch": 23.3,
    "mchc": 33.2,
    "rdw": 16.5,
    "wbc": 8.2,
    "platelets": 310,
}

DEMO_SMEAR = [
    "target cells noted",
    "occasional sickle forms",
    "polychromasia",
    "mild anisocytosis",
]


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class HemoglobinAnalyzer:
    """Hemoglobin disorder analysis engine."""

    def __init__(
        self,
        hplc_path=None,
        retention_times_path=None,
        cbc_path=None,
        peripheral_smear_path=None,
        molecular_path=None,
    ):
        self.fractions = self._load_hplc(hplc_path)
        self.retention_times = self._load_json(retention_times_path, HPLC_RETENTION_WINDOWS)
        self.cbc = self._load_json(cbc_path, DEMO_CBC)
        self.smear = self._load_smear(peripheral_smear_path)
        self.molecular = self._load_molecular(molecular_path)
        self.timestamp = datetime.now().isoformat()

    # --- loaders --------------------------------------------------------

    @staticmethod
    def _load_json(path, default):
        if path and os.path.isfile(path):
            with open(path) as fh:
                return json.load(fh)
        return default

    def _load_hplc(self, path):
        if path and os.path.isfile(path):
            if path.endswith(".json"):
                with open(path) as fh:
                    return json.load(fh)
            if pd is not None and path.endswith(".csv"):
                df = pd.read_csv(path)
                return {row["fraction"]: row["percent"] for _, row in df.iterrows()} if "fraction" in df.columns else DEMO_HPLC
        return DEMO_HPLC

    @staticmethod
    def _load_smear(path):
        if path and os.path.isfile(path):
            with open(path) as fh:
                return [line.strip() for line in fh if line.strip()]
        return DEMO_SMEAR

    @staticmethod
    def _load_molecular(path):
        if path and os.path.isfile(path):
            with open(path) as fh:
                return {"raw_vcf_lines": [l.strip() for l in fh if not l.startswith("#")]}
        return {"note": "No molecular data provided – demo mode"}

    # --- interpretation -------------------------------------------------

    def _interpret_hplc(self):
        results = {}
        for fraction, pct in self.fractions.items():
            nr = NORMAL_RANGES.get(fraction)
            if nr:
                if pct < nr["low"]:
                    status = "DECREASED"
                elif pct > nr["high"]:
                    status = "INCREASED"
                else:
                    status = "NORMAL"
            else:
                status = "DETECTED" if pct > 0 else "NOT DETECTED"
            results[fraction] = {"percent": pct, "status": status}
        return results

    def _classify(self):
        for rule in CLASSIFICATION_RULES:
            if rule["criteria"](self.fractions):
                return rule["name"]
        # Alpha-thal check: normal HPLC but microcytic
        mcv = self.cbc.get("mcv", 90)
        if mcv < 80 and all(
            self.fractions.get(f, 0) <= NORMAL_RANGES.get(f, {}).get("high", 100)
            for f in ("HbA2", "HbF")
        ):
            return "Possible Alpha-Thalassemia (normal HPLC, microcytic)"
        return "Normal hemoglobin pattern"

    def _thalassemia_indices(self):
        mcv = self.cbc.get("mcv", 90)
        mch = self.cbc.get("mch", 30)
        rbc = self.cbc.get("rbc", 4.5)

        mentzer = round(mcv / rbc, 2) if rbc > 0 else None
        england_fraser = round(mcv - rbc - (5 * mch) - 3.4, 2)
        srivastava = round(mch / rbc, 2) if rbc > 0 else None

        return {
            "mentzer_index": {
                "value": mentzer,
                "interpretation": "Suggests thalassemia" if mentzer and mentzer < 13 else "Suggests iron deficiency",
                "threshold": "<13 thalassemia, >=13 iron deficiency",
            },
            "england_fraser": {
                "value": england_fraser,
                "interpretation": "Suggests thalassemia" if england_fraser < 0 else "Suggests iron deficiency",
            },
            "srivastava_index": {
                "value": srivastava,
                "interpretation": "Suggests thalassemia" if srivastava and srivastava < 3.8 else "Suggests iron deficiency",
            },
        }

    def _identify_variants(self):
        detected = []
        for fraction, pct in self.fractions.items():
            if fraction in ("HbA", "HbA2", "HbF"):
                continue
            if pct > 0:
                info = VARIANT_DATABASE.get(fraction, {"aa_change": "Unknown", "clinical": "Uncharacterized", "severity": "unknown"})
                detected.append({"variant": fraction, "percent": pct, **info})
        return detected if detected else [{"variant": "None detected above background"}]

    def _severity_classification(self, classification):
        severe = ["Sickle Cell Disease", "Beta-Thalassemia Major", "Hb Barts"]
        moderate = ["HbSC Disease", "HbC Disease", "HbE Disease", "HbS/Beta-Thal", "HbE/Beta-Thal"]
        mild = ["Sickle Cell Trait", "Beta-Thalassemia Minor", "Alpha-Thalassemia", "HPFH"]
        for s in severe:
            if s in classification:
                return "SEVERE"
        for m in moderate:
            if m in classification:
                return "MODERATE"
        for m in mild:
            if m in classification:
                return "MILD"
        if "Normal" in classification:
            return "NONE"
        return "INDETERMINATE"

    def _management(self, classification):
        for key, recs in MANAGEMENT_RECS.items():
            if key in classification:
                return recs
        return MANAGEMENT_RECS["default"]

    # --- main -----------------------------------------------------------

    def analyze(self) -> dict:
        classification = self._classify()
        return {
            "analysis": "Hemoglobin Disorder Analysis",
            "timestamp": self.timestamp,
            "hplc_interpretation": self._interpret_hplc(),
            "hemoglobin_fractions": self.fractions,
            "classification": classification,
            "severity": self._severity_classification(classification),
            "thalassemia_indices": self._thalassemia_indices(),
            "variant_identification": self._identify_variants(),
            "peripheral_smear_findings": self.smear,
            "molecular_data": self.molecular,
            "management": self._management(classification),
            "cbc_summary": self.cbc,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hemoglobin Analyzer – Hemoglobinopathy analysis")
    parser.add_argument("--hplc_data", type=str, default=None, help="HPLC chromatogram CSV/JSON")
    parser.add_argument("--retention_times", type=str, default=None, help="Peak retention times JSON")
    parser.add_argument("--cbc", type=str, default=None, help="CBC results JSON")
    parser.add_argument("--peripheral_smear", type=str, default=None, help="Peripheral smear findings TXT")
    parser.add_argument("--molecular", type=str, default=None, help="HBB sequencing VCF")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    analyzer = HemoglobinAnalyzer(
        hplc_path=args.hplc_data,
        retention_times_path=args.retention_times,
        cbc_path=args.cbc,
        peripheral_smear_path=args.peripheral_smear,
        molecular_path=args.molecular,
    )
    result = analyzer.analyze()
    output_json = json.dumps(result, indent=2, default=str)

    if args.output:
        os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
        with open(args.output, "w") as fh:
            fh.write(output_json)
        print(f"[INFO] Report written to {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

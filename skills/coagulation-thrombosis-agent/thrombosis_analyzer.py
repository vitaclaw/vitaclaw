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
Thrombosis Analyzer – VTE risk assessment and anticoagulation analysis.

Usage:
    python3 thrombosis_analyzer.py \
        --patient_data patient_demographics.json \
        --labs coagulation_panel.csv \
        --risk_model improved_padua \
        --anticoagulant lmwh \
        --renal_function egfr_45 \
        --output vte_assessment.json
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

PADUA_CRITERIA = {
    "active_cancer": 3,
    "previous_vte": 3,
    "reduced_mobility": 3,
    "thrombophilia": 3,
    "recent_trauma_surgery": 2,
    "age_gte_70": 1,
    "heart_respiratory_failure": 1,
    "ami_stroke": 1,
    "infection_rheum": 1,
    "obesity_bmi_gte_30": 1,
    "hormonal_therapy": 1,
}

IMPROVE_CRITERIA = {
    "previous_vte": 3,
    "known_thrombophilia": 2,
    "lower_limb_paralysis": 2,
    "active_cancer": 2,
    "icu_ccu_stay": 1,
    "complete_immobilization": 1,
    "age_gt_60": 1,
}

CHADS2_VASC_CRITERIA = {
    "chf": 1,
    "hypertension": 1,
    "age_gte_75": 2,
    "diabetes": 1,
    "stroke_tia": 2,
    "vascular_disease": 1,
    "age_65_74": 1,
    "female_sex": 1,
}

CAPRINI_CRITERIA = {
    "age_41_60": 1,
    "age_61_74": 2,
    "age_gte_75": 3,
    "minor_surgery": 1,
    "major_surgery": 2,
    "varicose_veins": 1,
    "bmi_gt_25": 1,
    "oral_contraceptives": 1,
    "pregnancy_postpartum": 1,
    "sepsis": 1,
    "serious_lung_disease": 1,
    "abnormal_pulmonary_function": 1,
    "previous_vte": 3,
    "family_history_vte": 3,
    "factor_v_leiden": 3,
    "prothrombin_mutation": 3,
    "lupus_anticoagulant": 3,
    "anticardiolipin_antibody": 3,
    "heparin_induced_thrombocytopenia": 3,
    "immobility_72h": 2,
    "central_venous_access": 2,
    "malignancy": 2,
    "confined_bed_gt_72h": 2,
    "hip_knee_fracture": 5,
    "stroke": 5,
    "multiple_trauma": 5,
    "spinal_cord_injury": 5,
}

HAS_BLED_CRITERIA = {
    "hypertension_uncontrolled": 1,
    "abnormal_renal_function": 1,
    "abnormal_liver_function": 1,
    "stroke_history": 1,
    "bleeding_history": 1,
    "labile_inr": 1,
    "age_gt_65": 1,
    "drugs_alcohol": 1,
}

ANTICOAGULANT_DOSING = {
    "lmwh": {
        "egfr_gte_30": {"drug": "Enoxaparin", "dose": "1 mg/kg SC q12h or 1.5 mg/kg SC daily", "monitoring": "Anti-Xa levels if needed"},
        "egfr_15_29": {"drug": "Enoxaparin", "dose": "1 mg/kg SC daily (reduced)", "monitoring": "Anti-Xa levels required"},
        "egfr_lt_15": {"drug": "UFH preferred", "dose": "Switch to UFH", "monitoring": "aPTT monitoring"},
    },
    "ufh": {
        "egfr_gte_30": {"drug": "Heparin", "dose": "80 U/kg bolus, then 18 U/kg/hr", "monitoring": "aPTT q6h"},
        "egfr_15_29": {"drug": "Heparin", "dose": "80 U/kg bolus, then 18 U/kg/hr", "monitoring": "aPTT q6h"},
        "egfr_lt_15": {"drug": "Heparin", "dose": "80 U/kg bolus, then 18 U/kg/hr", "monitoring": "aPTT q6h"},
    },
    "doac": {
        "egfr_gte_30": {"drug": "Apixaban / Rivaroxaban", "dose": "Apixaban 5 mg PO BID or Rivaroxaban 15 mg PO BID x21d then 20 mg daily", "monitoring": "Renal function periodically"},
        "egfr_15_29": {"drug": "Apixaban", "dose": "Apixaban 2.5 mg PO BID (dose-adjusted)", "monitoring": "Renal function, drug levels"},
        "egfr_lt_15": {"drug": "Avoid DOAC", "dose": "Switch to UFH or warfarin", "monitoring": "aPTT / INR"},
    },
}

DIC_PLATELET_SCORE = {">100000": 0, "50000-100000": 1, "<50000": 2}
DIC_DDIMER_SCORE = {"normal": 0, "moderate_increase": 2, "strong_increase": 3}
DIC_PT_PROLONGATION = {"<3s": 0, "3-6s": 1, ">6s": 2}
DIC_FIBRINOGEN_SCORE = {">100": 0, "<100": 1}

# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_PATIENT = {
    "patient_id": "VTE-2026-0451",
    "age": 72,
    "sex": "male",
    "bmi": 31.2,
    "conditions": [
        "active_cancer",
        "reduced_mobility",
        "hypertension",
        "diabetes",
    ],
    "medications": ["metformin", "amlodipine"],
    "recent_surgery": False,
    "previous_vte": False,
    "thrombophilia": False,
}

DEMO_LABS = {
    "platelet_count": 85000,
    "d_dimer": "strong_increase",
    "pt_prolongation_seconds": 4.5,
    "fibrinogen_mg_dl": 90,
    "inr": 1.6,
    "aptt": 38,
    "creatinine": 1.8,
    "egfr": 45,
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class ThrombosisAnalyzer:
    """VTE risk assessment and anticoagulation analysis engine."""

    def __init__(
        self,
        patient_data_path: str = None,
        labs_path: str = None,
        risk_model: str = "padua",
        anticoagulant: str = "lmwh",
        renal_function: str = None,
    ):
        self.risk_model = risk_model.lower()
        self.anticoagulant = anticoagulant.lower()
        self.renal_function = renal_function
        self.patient = self._load_patient(patient_data_path)
        self.labs = self._load_labs(labs_path)
        self.timestamp = datetime.now().isoformat()

    # --- data loading ---------------------------------------------------

    def _load_patient(self, path):
        if path and os.path.isfile(path):
            with open(path, "r") as fh:
                return json.load(fh)
        return DEMO_PATIENT

    def _load_labs(self, path):
        if path and os.path.isfile(path):
            if path.endswith(".json"):
                with open(path, "r") as fh:
                    return json.load(fh)
            if pd is not None and path.endswith(".csv"):
                df = pd.read_csv(path)
                return df.to_dict(orient="records")[0] if len(df) else DEMO_LABS
        return DEMO_LABS

    # --- scoring engines -----------------------------------------------

    def _score_padua(self):
        score = 0
        details = {}
        conditions = self.patient.get("conditions", [])
        age = self.patient.get("age", 0)
        bmi = self.patient.get("bmi", 0)

        mapping = {
            "active_cancer": "active_cancer",
            "previous_vte": "previous_vte",
            "reduced_mobility": "reduced_mobility",
            "thrombophilia": "thrombophilia",
            "recent_trauma_surgery": "recent_trauma_surgery",
            "heart_respiratory_failure": "heart_respiratory_failure",
            "ami_stroke": "ami_stroke",
            "infection_rheum": "infection_rheum",
            "hormonal_therapy": "hormonal_therapy",
        }
        for cond, key in mapping.items():
            present = cond in conditions or self.patient.get(cond, False)
            pts = PADUA_CRITERIA[key] if present else 0
            details[key] = {"present": present, "points": pts}
            score += pts

        age_hit = age >= 70
        details["age_gte_70"] = {"present": age_hit, "points": 1 if age_hit else 0}
        score += 1 if age_hit else 0

        obesity_hit = bmi >= 30
        details["obesity_bmi_gte_30"] = {"present": obesity_hit, "points": 1 if obesity_hit else 0}
        score += 1 if obesity_hit else 0

        risk_level = "HIGH" if score >= 4 else "LOW"
        return {"model": "Padua", "score": score, "threshold": 4, "risk_level": risk_level, "details": details}

    def _score_improve(self):
        score = 0
        details = {}
        conditions = self.patient.get("conditions", [])
        age = self.patient.get("age", 0)

        bool_fields = {
            "previous_vte": "previous_vte",
            "known_thrombophilia": "thrombophilia",
            "lower_limb_paralysis": "lower_limb_paralysis",
            "active_cancer": "active_cancer",
            "icu_ccu_stay": "icu_ccu_stay",
            "complete_immobilization": "reduced_mobility",
        }
        for field, cond_key in bool_fields.items():
            present = cond_key in conditions or self.patient.get(cond_key, False)
            pts = IMPROVE_CRITERIA[field] if present else 0
            details[field] = {"present": present, "points": pts}
            score += pts

        age_hit = age > 60
        details["age_gt_60"] = {"present": age_hit, "points": 1 if age_hit else 0}
        score += 1 if age_hit else 0

        risk_level = "HIGH" if score >= 2 else "LOW"
        return {"model": "IMPROVE", "score": score, "threshold": 2, "risk_level": risk_level, "details": details}

    def _score_chads_vasc(self):
        score = 0
        details = {}
        conditions = self.patient.get("conditions", [])
        age = self.patient.get("age", 0)
        sex = self.patient.get("sex", "unknown").lower()

        simple = {
            "chf": "chf",
            "hypertension": "hypertension",
            "diabetes": "diabetes",
            "stroke_tia": "stroke_tia",
            "vascular_disease": "vascular_disease",
        }
        for field, cond_key in simple.items():
            present = cond_key in conditions
            pts = CHADS2_VASC_CRITERIA[field] if present else 0
            details[field] = {"present": present, "points": pts}
            score += pts

        age_75 = age >= 75
        details["age_gte_75"] = {"present": age_75, "points": 2 if age_75 else 0}
        score += 2 if age_75 else 0

        age_65_74 = 65 <= age < 75
        details["age_65_74"] = {"present": age_65_74, "points": 1 if age_65_74 else 0}
        score += 1 if age_65_74 else 0

        female = sex == "female"
        details["female_sex"] = {"present": female, "points": 1 if female else 0}
        score += 1 if female else 0

        if score == 0:
            risk_level = "LOW"
        elif score == 1:
            risk_level = "LOW-MODERATE"
        elif score == 2:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"
        return {"model": "CHA2DS2-VASc", "score": score, "risk_level": risk_level, "details": details}

    def _score_caprini(self):
        score = 0
        details = {}
        conditions = self.patient.get("conditions", [])
        age = self.patient.get("age", 0)
        bmi = self.patient.get("bmi", 0)

        if age >= 75:
            score += 3; details["age_gte_75"] = {"present": True, "points": 3}
        elif age >= 61:
            score += 2; details["age_61_74"] = {"present": True, "points": 2}
        elif age >= 41:
            score += 1; details["age_41_60"] = {"present": True, "points": 1}

        if bmi > 25:
            score += 1; details["bmi_gt_25"] = {"present": True, "points": 1}

        for crit in ("minor_surgery", "major_surgery", "varicose_veins",
                      "previous_vte", "family_history_vte", "factor_v_leiden",
                      "malignancy", "immobility_72h", "central_venous_access"):
            present = crit in conditions or self.patient.get(crit, False)
            pts = CAPRINI_CRITERIA.get(crit, 0) if present else 0
            details[crit] = {"present": present, "points": pts}
            score += pts

        if score <= 1:
            risk_level = "LOW"
        elif score <= 2:
            risk_level = "MODERATE"
        elif score <= 4:
            risk_level = "HIGH"
        else:
            risk_level = "VERY HIGH"
        return {"model": "Caprini", "score": score, "risk_level": risk_level, "details": details}

    # --- DIC ------------------------------------------------------------

    def _assess_dic(self):
        platelets = self.labs.get("platelet_count", 150000)
        d_dimer = self.labs.get("d_dimer", "normal")
        pt_sec = self.labs.get("pt_prolongation_seconds", 0)
        fibrinogen = self.labs.get("fibrinogen_mg_dl", 300)

        score = 0
        breakdown = {}

        if platelets > 100000:
            p = 0
        elif platelets >= 50000:
            p = 1
        else:
            p = 2
        breakdown["platelets"] = {"value": platelets, "points": p}
        score += p

        d_map = {"normal": 0, "moderate_increase": 2, "strong_increase": 3}
        d = d_map.get(d_dimer, 0)
        breakdown["d_dimer"] = {"value": d_dimer, "points": d}
        score += d

        if pt_sec < 3:
            t = 0
        elif pt_sec <= 6:
            t = 1
        else:
            t = 2
        breakdown["pt_prolongation"] = {"value_seconds": pt_sec, "points": t}
        score += t

        f = 1 if fibrinogen < 100 else 0
        breakdown["fibrinogen"] = {"value_mg_dl": fibrinogen, "points": f}
        score += f

        dic_positive = score >= 5
        return {
            "isth_dic_score": score,
            "threshold": 5,
            "dic_positive": dic_positive,
            "interpretation": "Compatible with overt DIC" if dic_positive else "Not suggestive of overt DIC",
            "breakdown": breakdown,
        }

    # --- bleeding risk --------------------------------------------------

    def _assess_bleeding_risk(self):
        score = 0
        details = {}
        conditions = self.patient.get("conditions", [])
        age = self.patient.get("age", 0)

        mapping = {
            "hypertension_uncontrolled": "hypertension",
            "abnormal_renal_function": None,
            "abnormal_liver_function": "liver_disease",
            "stroke_history": "stroke_tia",
            "bleeding_history": "bleeding_history",
            "labile_inr": None,
            "drugs_alcohol": "drugs_alcohol",
        }
        for field, cond in mapping.items():
            if field == "abnormal_renal_function":
                present = self.labs.get("egfr", 90) < 60
            elif field == "labile_inr":
                present = self.labs.get("inr", 1.0) > 1.5
            else:
                present = (cond in conditions) if cond else False
            pts = HAS_BLED_CRITERIA[field] if present else 0
            details[field] = {"present": present, "points": pts}
            score += pts

        age_hit = age > 65
        details["age_gt_65"] = {"present": age_hit, "points": 1 if age_hit else 0}
        score += 1 if age_hit else 0

        if score <= 1:
            risk_level = "LOW"
        elif score <= 2:
            risk_level = "MODERATE"
        else:
            risk_level = "HIGH"
        return {"has_bled_score": score, "risk_level": risk_level, "details": details}

    # --- anticoagulant recommendation -----------------------------------

    def _recommend_anticoagulant(self):
        egfr = self.labs.get("egfr", 90)
        if self.renal_function:
            try:
                egfr = int(self.renal_function.lower().replace("egfr_", ""))
            except ValueError:
                pass

        if egfr >= 30:
            tier = "egfr_gte_30"
        elif egfr >= 15:
            tier = "egfr_15_29"
        else:
            tier = "egfr_lt_15"

        agent = self.anticoagulant if self.anticoagulant in ANTICOAGULANT_DOSING else "lmwh"
        rec = ANTICOAGULANT_DOSING[agent].get(tier, ANTICOAGULANT_DOSING[agent]["egfr_gte_30"])
        return {
            "selected_agent": agent.upper(),
            "egfr": egfr,
            "renal_tier": tier,
            "recommendation": rec,
        }

    # --- main analysis --------------------------------------------------

    def analyze(self) -> dict:
        model_map = {
            "padua": self._score_padua,
            "improved_padua": self._score_padua,
            "improve": self._score_improve,
            "caprini": self._score_caprini,
            "chads_vasc": self._score_chads_vasc,
        }
        scoring_fn = model_map.get(self.risk_model, self._score_padua)

        result = {
            "analysis": "VTE Risk Assessment & Anticoagulation Analysis",
            "timestamp": self.timestamp,
            "patient_id": self.patient.get("patient_id", "UNKNOWN"),
            "risk_scores": scoring_fn(),
            "dic_assessment": self._assess_dic(),
            "bleeding_risk": self._assess_bleeding_risk(),
            "anticoagulation_recommendation": self._recommend_anticoagulant(),
            "risk_level": scoring_fn()["risk_level"],
            "notes": [
                "All scores are computed from available clinical data.",
                "Verify with attending physician before initiating therapy.",
                "Re-assess VTE risk with clinical status changes.",
            ],
        }
        return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Thrombosis Analyzer – VTE risk & anticoagulation")
    parser.add_argument("--patient_data", type=str, default=None, help="Patient demographics JSON")
    parser.add_argument("--labs", type=str, default=None, help="Coagulation panel (CSV/JSON)")
    parser.add_argument("--risk_model", type=str, default="padua",
                        choices=["padua", "improved_padua", "improve", "caprini", "chads_vasc"],
                        help="Risk scoring model")
    parser.add_argument("--anticoagulant", type=str, default="lmwh",
                        choices=["lmwh", "ufh", "doac"], help="Anticoagulant class")
    parser.add_argument("--renal_function", type=str, default=None, help="eGFR value, e.g. egfr_45")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    analyzer = ThrombosisAnalyzer(
        patient_data_path=args.patient_data,
        labs_path=args.labs,
        risk_model=args.risk_model,
        anticoagulant=args.anticoagulant,
        renal_function=args.renal_function,
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

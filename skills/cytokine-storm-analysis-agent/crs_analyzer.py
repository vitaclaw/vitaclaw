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
Cytokine Release Syndrome (CRS) Analysis.

Grades CRS severity using ASTCT and Lee criteria, analyzes cytokine profiles,
performs differential diagnosis (CRS vs HLH/MAS vs sepsis vs ICANS),
predicts risk, and recommends treatment interventions.
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Cytokine normal ranges and thresholds (pg/mL unless noted)
CYTOKINE_REFERENCE = {
    "IL-6": {"normal_max": 7.0, "unit": "pg/mL", "crs_threshold_fold": 10,
             "peak_day_range": (2, 5), "key_role": "Central CRS mediator"},
    "IFN-gamma": {"normal_max": 15.0, "unit": "pg/mL", "crs_threshold_fold": 5,
                   "peak_day_range": (1, 4), "key_role": "T cell/NK activation marker"},
    "IL-10": {"normal_max": 10.0, "unit": "pg/mL", "crs_threshold_fold": 5,
              "peak_day_range": (2, 5), "key_role": "Anti-inflammatory response"},
    "IL-2": {"normal_max": 10.0, "unit": "pg/mL", "crs_threshold_fold": 5,
             "peak_day_range": (1, 3), "key_role": "T cell proliferation"},
    "TNF-alpha": {"normal_max": 8.0, "unit": "pg/mL", "crs_threshold_fold": 5,
                   "peak_day_range": (1, 3), "key_role": "Pro-inflammatory"},
    "IL-1beta": {"normal_max": 5.0, "unit": "pg/mL", "crs_threshold_fold": 5,
                  "peak_day_range": (1, 3), "key_role": "Inflammasome activation"},
    "IL-8": {"normal_max": 15.0, "unit": "pg/mL", "crs_threshold_fold": 5,
             "peak_day_range": (2, 5), "key_role": "Neutrophil chemotaxis"},
    "MCP-1": {"normal_max": 300.0, "unit": "pg/mL", "crs_threshold_fold": 3,
              "peak_day_range": (2, 5), "key_role": "Monocyte recruitment"},
    "sCD25": {"normal_max": 1000.0, "unit": "pg/mL", "crs_threshold_fold": 3,
              "peak_day_range": (3, 7), "key_role": "T cell activation / HLH marker"},
    "Ferritin": {"normal_max": 300.0, "unit": "ng/mL", "crs_threshold_fold": 5,
                 "peak_day_range": (3, 7), "key_role": "Macrophage activation / HLH marker"},
}

# CAR-T product-specific CRS profiles
CART_PRODUCT_PROFILES = {
    "tisagenlecleucel": {
        "trade_name": "Kymriah",
        "target": "CD19",
        "crs_rate_any_grade": 0.79,
        "crs_rate_grade3plus": 0.22,
        "median_onset_days": 3,
        "median_duration_days": 8,
        "icans_rate": 0.21,
    },
    "axicabtagene_ciloleucel": {
        "trade_name": "Yescarta",
        "target": "CD19",
        "crs_rate_any_grade": 0.93,
        "crs_rate_grade3plus": 0.13,
        "median_onset_days": 2,
        "median_duration_days": 7,
        "icans_rate": 0.64,
    },
    "lisocabtagene_maraleucel": {
        "trade_name": "Breyanzi",
        "target": "CD19",
        "crs_rate_any_grade": 0.42,
        "crs_rate_grade3plus": 0.02,
        "median_onset_days": 5,
        "median_duration_days": 5,
        "icans_rate": 0.10,
    },
    "idecabtagene_vicleucel": {
        "trade_name": "Abecma",
        "target": "BCMA",
        "crs_rate_any_grade": 0.84,
        "crs_rate_grade3plus": 0.05,
        "median_onset_days": 1,
        "median_duration_days": 5,
        "icans_rate": 0.18,
    },
    "ciltacabtagene_autoleucel": {
        "trade_name": "Carvykti",
        "target": "BCMA",
        "crs_rate_any_grade": 0.95,
        "crs_rate_grade3plus": 0.04,
        "median_onset_days": 7,
        "median_duration_days": 4,
        "icans_rate": 0.21,
    },
}


class CRSAnalyzer:
    """Cytokine release syndrome analysis and grading."""

    def __init__(self, patient_data_path=None, cytokines_path=None,
                 vitals_path=None, labs_path=None, cart_product="tisagenlecleucel",
                 day_post_infusion=5, model_name="crs_predictor_v3"):
        self.patient_data_path = patient_data_path
        self.cytokines_path = cytokines_path
        self.vitals_path = vitals_path
        self.labs_path = labs_path
        self.cart_product = cart_product.lower().replace("-", "_").replace(" ", "_")
        self.day_post_infusion = day_post_infusion
        self.model_name = model_name
        self.product_profile = CART_PRODUCT_PROFILES.get(
            self.cart_product, CART_PRODUCT_PROFILES["tisagenlecleucel"]
        )

    def _load_json_data(self, path, demo_data):
        """Load JSON data or return demo."""
        if path and os.path.isfile(path):
            with open(path, "r") as fh:
                return json.load(fh)
        return demo_data

    def _load_csv_data(self, path, demo_data):
        """Load CSV data or return demo."""
        if path and os.path.isfile(path):
            rows = []
            with open(path, "r") as fh:
                header = fh.readline().strip().split(",")
                for line in fh:
                    fields = line.strip().split(",")
                    rows.append(dict(zip(header, fields)))
            return rows
        return demo_data

    def _load_patient_data(self):
        return self._load_json_data(self.patient_data_path, {
            "age": 55, "sex": "M", "weight_kg": 80,
            "diagnosis": "DLBCL", "disease_burden": "high",
            "prior_lines": 3, "lymphodepletion": "flu_cy",
            "baseline_crp": 25.0, "baseline_ferritin": 450.0,
            "baseline_ldh": 380.0,
        })

    def _load_cytokines(self):
        return self._load_csv_data(self.cytokines_path, [
            {"cytokine": "IL-6", "value": "850", "unit": "pg/mL"},
            {"cytokine": "IFN-gamma", "value": "320", "unit": "pg/mL"},
            {"cytokine": "IL-10", "value": "180", "unit": "pg/mL"},
            {"cytokine": "IL-2", "value": "55", "unit": "pg/mL"},
            {"cytokine": "TNF-alpha", "value": "42", "unit": "pg/mL"},
            {"cytokine": "IL-1beta", "value": "18", "unit": "pg/mL"},
            {"cytokine": "IL-8", "value": "95", "unit": "pg/mL"},
            {"cytokine": "MCP-1", "value": "1500", "unit": "pg/mL"},
            {"cytokine": "sCD25", "value": "8500", "unit": "pg/mL"},
            {"cytokine": "Ferritin", "value": "12000", "unit": "ng/mL"},
        ])

    def _load_vitals(self):
        return self._load_csv_data(self.vitals_path, [
            {"temp_c": "39.2", "sbp": "88", "dbp": "55", "hr": "110",
             "rr": "22", "spo2": "93", "fio2": "0.40", "vasopressor": "norepinephrine",
             "o2_device": "high_flow_nasal_cannula"},
        ])

    def _load_labs(self):
        return self._load_csv_data(self.labs_path, [
            {"crp": "180", "ferritin": "12000", "ldh": "850",
             "fibrinogen": "120", "triglycerides": "310",
             "ast": "220", "alt": "185", "creatinine": "1.8",
             "wbc": "0.5", "platelets": "45"},
        ])

    def _grade_crs_astct(self, vitals):
        """Grade CRS using ASTCT (Lee 2019) consensus criteria."""
        v = vitals[0] if vitals else {}
        temp = float(v.get("temp_c", 37.0))
        has_fever = temp >= 38.0
        vasopressor = v.get("vasopressor", "none").lower()
        has_hypotension = float(v.get("sbp", 120)) < 90
        spo2 = float(v.get("spo2", 99))
        fio2 = float(v.get("fio2", 0.21))
        o2_device = v.get("o2_device", "none").lower()

        needs_vasopressor = vasopressor not in ("none", "", "no")
        needs_multiple_vasopressors = vasopressor in ("multiple", "norepinephrine+vasopressin",
                                                       "norepinephrine+phenylephrine")
        needs_low_flow_o2 = spo2 < 94 and fio2 <= 0.40 and "low_flow" in o2_device
        needs_high_flow_o2 = ("high_flow" in o2_device or "non_rebreather" in o2_device
                               or (fio2 > 0.40 and "positive_pressure" not in o2_device))
        needs_positive_pressure = any(x in o2_device for x in ["cpap", "bipap", "ventilator",
                                                                  "positive_pressure", "intubat"])

        if not has_fever:
            grade = 0
            criteria = "No fever >= 38°C"
        elif not has_hypotension and spo2 >= 94:
            grade = 1
            criteria = "Fever >= 38°C; no hypotension; no hypoxia"
        elif (has_hypotension and not needs_vasopressor) or needs_low_flow_o2:
            grade = 2
            criteria = ("Fever + hypotension not requiring vasopressors "
                        "OR hypoxia requiring low-flow O2")
        elif needs_vasopressor or needs_high_flow_o2:
            grade = 3
            criteria = ("Fever + hypotension requiring a vasopressor "
                        "OR hypoxia requiring high-flow O2/non-rebreather")
        elif needs_multiple_vasopressors or needs_positive_pressure:
            grade = 4
            criteria = ("Fever + hypotension requiring multiple vasopressors "
                        "OR hypoxia requiring positive pressure")
        else:
            grade = 3
            criteria = "Fever + vasopressor/supplemental O2 support"

        return {"grade": grade, "criteria": criteria, "system": "ASTCT_2019"}

    def _grade_crs_lee(self, vitals):
        """Grade CRS using Lee 2014 criteria (alternative)."""
        astct = self._grade_crs_astct(vitals)
        # Lee criteria are similar; we approximate with slight adjustments
        return {
            "grade": astct["grade"],
            "criteria": astct["criteria"],
            "system": "Lee_2014",
            "note": "Lee criteria are similar to ASTCT; minor differences in O2 thresholds",
        }

    def _analyze_cytokine_profile(self, cytokines):
        """Analyze individual cytokine levels against reference."""
        profile = []
        for c in cytokines:
            name = c.get("cytokine", "")
            value = float(c.get("value", 0))
            ref = CYTOKINE_REFERENCE.get(name, None)
            if ref:
                fold = value / ref["normal_max"] if ref["normal_max"] > 0 else 0
                elevated = fold >= ref["crs_threshold_fold"]
                profile.append({
                    "cytokine": name,
                    "value": value,
                    "unit": ref["unit"],
                    "normal_max": ref["normal_max"],
                    "fold_elevation": round(fold, 1),
                    "significantly_elevated": elevated,
                    "peak_day_range": list(ref["peak_day_range"]),
                    "key_role": ref["key_role"],
                })
            else:
                profile.append({
                    "cytokine": name, "value": value,
                    "unit": c.get("unit", ""), "note": "No reference available",
                })
        return profile

    def _differential_diagnosis(self, cytokines, labs):
        """Differentiate CRS from HLH/MAS, sepsis, and ICANS."""
        lab = labs[0] if labs else {}
        ferritin = float(lab.get("ferritin", 0))
        triglycerides = float(lab.get("triglycerides", 0))
        fibrinogen = float(lab.get("fibrinogen", 400))
        ast = float(lab.get("ast", 0))

        hlh_criteria_met = 0
        hlh_details = []
        if ferritin > 10000:
            hlh_criteria_met += 1
            hlh_details.append(f"Ferritin {ferritin} > 10000 ng/mL")
        if triglycerides > 265:
            hlh_criteria_met += 1
            hlh_details.append(f"Triglycerides {triglycerides} > 265 mg/dL")
        if fibrinogen < 150:
            hlh_criteria_met += 1
            hlh_details.append(f"Fibrinogen {fibrinogen} < 150 mg/dL")
        if ast > 100:
            hlh_criteria_met += 1
            hlh_details.append(f"AST {ast} > 100 U/L (liver enzymes elevated)")

        # Check for sepsis indicators (simplified)
        wbc = float(lab.get("wbc", 5.0))
        sepsis_concern = wbc > 12 or wbc < 4

        differentials = {
            "HLH_MAS": {
                "criteria_met": hlh_criteria_met,
                "criteria_total": 4,
                "likely": hlh_criteria_met >= 3,
                "details": hlh_details,
                "note": "HLH/MAS overlap with severe CRS is common post-CAR-T",
            },
            "sepsis": {
                "concern": sepsis_concern,
                "note": "Blood cultures and procalcitonin recommended to rule out infection",
                "distinguishing_features": "Procalcitonin typically elevated in sepsis but not CRS",
            },
            "ICANS": {
                "note": "Assess with ICE score; ICANS can co-occur with CRS",
                "risk_factors": "High CRS grade, rapid CAR-T expansion, high IL-6/IL-15",
            },
        }
        return differentials

    def _predict_risk(self, patient_data, crs_grade):
        """Rule-based CRS risk prediction."""
        risk_factors = []
        risk_score = 0

        burden = patient_data.get("disease_burden", "unknown").lower()
        if burden == "high":
            risk_factors.append("High tumor burden")
            risk_score += 2

        baseline_crp = float(patient_data.get("baseline_crp", 0))
        if baseline_crp > 10:
            risk_factors.append(f"Elevated baseline CRP ({baseline_crp})")
            risk_score += 1

        baseline_ferritin = float(patient_data.get("baseline_ferritin", 0))
        if baseline_ferritin > 500:
            risk_factors.append(f"Elevated baseline ferritin ({baseline_ferritin})")
            risk_score += 1

        product_crs_rate = self.product_profile.get("crs_rate_grade3plus", 0)
        if product_crs_rate > 0.10:
            risk_factors.append(f"Product with higher severe CRS rate ({product_crs_rate:.0%})")
            risk_score += 1

        prior_lines = int(patient_data.get("prior_lines", 0))
        if prior_lines >= 3:
            risk_factors.append(f"Heavily pretreated ({prior_lines} prior lines)")
            risk_score += 1

        level = "high" if risk_score >= 4 else "moderate" if risk_score >= 2 else "low"
        return {
            "risk_level": level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "cart_product_profile": self.product_profile,
        }

    def _recommend_treatment(self, crs_grade):
        """Generate treatment recommendations based on CRS grade."""
        grade = crs_grade["grade"]
        recommendations = {
            "crs_grade": grade,
            "primary_interventions": [],
            "supportive_care": [
                "Aggressive IV fluid resuscitation",
                "Antipyretics (acetaminophen)",
                "Continuous monitoring (telemetry, SpO2, vitals q2-4h)",
            ],
        }

        if grade == 0:
            recommendations["primary_interventions"].append("Observation only")
        elif grade == 1:
            recommendations["primary_interventions"].extend([
                "Supportive care",
                "Antipyretics for fever",
                "IV fluids as needed",
            ])
        elif grade == 2:
            recommendations["primary_interventions"].extend([
                "Tocilizumab 8 mg/kg IV (max 800 mg)",
                "May repeat tocilizumab in 8 hours if no improvement",
                "IV fluid bolus for hypotension",
                "Supplemental O2 as needed",
            ])
        elif grade == 3:
            recommendations["primary_interventions"].extend([
                "Tocilizumab 8 mg/kg IV (max 800 mg)",
                "Dexamethasone 10 mg IV q6h",
                "Vasopressor support",
                "High-flow O2 or non-rebreather",
                "ICU transfer",
            ])
        elif grade >= 4:
            recommendations["primary_interventions"].extend([
                "Tocilizumab 8 mg/kg IV (max 800 mg)",
                "Dexamethasone 10 mg IV q6h (or methylprednisolone 2 mg/kg if refractory)",
                "Multiple vasopressors as needed",
                "Mechanical ventilation if needed",
                "ICU management",
                "Consider siltuximab, ruxolitinib, or anakinra if refractory",
            ])
        return recommendations

    def _assess_icans(self, crs_grade, cytokine_profile):
        """Assess ICANS risk correlation with CRS."""
        crs_g = crs_grade["grade"]
        il6_fold = 0
        for c in cytokine_profile:
            if c.get("cytokine") == "IL-6":
                il6_fold = c.get("fold_elevation", 0)
                break

        icans_risk = "low"
        if crs_g >= 3 or il6_fold > 100:
            icans_risk = "high"
        elif crs_g >= 2 or il6_fold > 50:
            icans_risk = "moderate"

        ice_score_note = (
            "ICE (Immune Effector Cell-Associated Encephalopathy) score: "
            "Orientation (4pts) + Naming (3pts) + Following commands (1pt) + "
            "Writing (1pt) + Attention (1pt) = 10 total. "
            "Grade 1: ICE 7-9; Grade 2: ICE 3-6; Grade 3: ICE 0-2; Grade 4: obtunded"
        )

        return {
            "icans_risk": icans_risk,
            "crs_grade_correlation": crs_g,
            "il6_fold_elevation": il6_fold,
            "product_icans_rate": self.product_profile.get("icans_rate", 0),
            "ice_score_assessment": ice_score_note,
            "management": (
                "Dexamethasone 10 mg IV q6h for Grade >= 2 ICANS"
                if icans_risk in ("moderate", "high")
                else "Monitor neurological status"
            ),
        }

    def _temporal_dynamics(self, cytokine_profile):
        """Assess temporal dynamics of cytokine release."""
        day = self.day_post_infusion
        dynamics = []
        for c in cytokine_profile:
            name = c.get("cytokine", "")
            peak_range = c.get("peak_day_range", [0, 0])
            if peak_range:
                at_peak = peak_range[0] <= day <= peak_range[1]
                pre_peak = day < peak_range[0]
                post_peak = day > peak_range[1]
                phase = "at_peak" if at_peak else "pre_peak" if pre_peak else "post_peak"
            else:
                phase = "unknown"
            dynamics.append({
                "cytokine": name,
                "current_day": day,
                "expected_peak_range": peak_range,
                "phase": phase,
            })
        return {
            "day_post_infusion": day,
            "cytokine_dynamics": dynamics,
            "expected_onset": self.product_profile.get("median_onset_days", "N/A"),
            "expected_duration": self.product_profile.get("median_duration_days", "N/A"),
        }

    def analyze(self):
        """Run CRS analysis pipeline."""
        patient = self._load_patient_data()
        cytokines_raw = self._load_cytokines()
        vitals = self._load_vitals()
        labs = self._load_labs()

        crs_grade_astct = self._grade_crs_astct(vitals)
        crs_grade_lee = self._grade_crs_lee(vitals)
        cytokine_profile = self._analyze_cytokine_profile(cytokines_raw)
        differential = self._differential_diagnosis(cytokines_raw, labs)
        risk = self._predict_risk(patient, crs_grade_astct)
        treatment = self._recommend_treatment(crs_grade_astct)
        icans = self._assess_icans(crs_grade_astct, cytokine_profile)
        temporal = self._temporal_dynamics(cytokine_profile)

        results = {
            "analysis": "cytokine_release_syndrome_analysis",
            "analysis_date": datetime.now().isoformat(),
            "cart_product": self.cart_product,
            "day_post_infusion": self.day_post_infusion,
            "crs_grade": crs_grade_astct,
            "crs_grading_criteria": {
                "astct": crs_grade_astct,
                "lee": crs_grade_lee,
            },
            "cytokine_profile": cytokine_profile,
            "differential_diagnosis": differential,
            "risk_assessment": risk,
            "treatment_recommendation": treatment,
            "icans_risk": icans,
            "temporal_dynamics": temporal,
        }
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Cytokine release syndrome analysis"
    )
    parser.add_argument("--patient_data", default=None,
                        help="Path to patient demographics (JSON)")
    parser.add_argument("--cytokines", default=None,
                        help="Path to cytokine panel values (CSV)")
    parser.add_argument("--vitals", default=None,
                        help="Path to vital signs (CSV)")
    parser.add_argument("--labs", default=None,
                        help="Path to laboratory values (CSV)")
    parser.add_argument("--cart_product", default="tisagenlecleucel",
                        help="CAR-T product name")
    parser.add_argument("--day_post_infusion", type=int, default=5,
                        help="Day post CAR-T infusion")
    parser.add_argument("--model", default="crs_predictor_v3",
                        help="Risk prediction model name")
    parser.add_argument("--output", default="crs_report.json",
                        help="Output JSON file path")
    args = parser.parse_args()

    analyzer = CRSAnalyzer(
        patient_data_path=args.patient_data,
        cytokines_path=args.cytokines,
        vitals_path=args.vitals,
        labs_path=args.labs,
        cart_product=args.cart_product,
        day_post_infusion=args.day_post_infusion,
        model_name=args.model,
    )

    results = analyzer.analyze()

    output_path = args.output
    if output_path.endswith("/"):
        os.makedirs(output_path, exist_ok=True)
        output_path = os.path.join(output_path, "crs_analysis_results.json")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"CRS analysis complete. Results: {output_path}")
    print(f"  CRS Grade (ASTCT): {results['crs_grade']['grade']}")
    print(f"  Criteria: {results['crs_grade']['criteria']}")
    print(f"  Risk level: {results['risk_assessment']['risk_level']}")
    print(f"  ICANS risk: {results['icans_risk']['icans_risk']}")
    print(f"  HLH/MAS concern: {'YES' if results['differential_diagnosis']['HLH_MAS']['likely'] else 'no'}")


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

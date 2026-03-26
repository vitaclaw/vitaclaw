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
ctDNA Dynamics and MRD (Minimal Residual Disease) Analysis.

Analyzes circulating tumor DNA kinetics, monitors molecular residual disease,
predicts relapse risk, and classifies treatment response using serial ctDNA
measurements from liquid biopsy.
"""

import argparse
import json
import os
import sys
import math
from datetime import datetime

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from scipy.optimize import curve_fit
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# Cancer-type specific shedding and clearance parameters
CANCER_TYPE_PROFILES = {
    "colorectal": {
        "shedding_rate": "high",
        "expected_clearance_days": 1.5,
        "ctdna_detection_rate_stage_I": 0.50,
        "ctdna_detection_rate_stage_IV": 0.95,
        "common_tracked_genes": ["APC", "TP53", "KRAS", "PIK3CA", "BRAF", "SMAD4"],
        "median_lead_time_months": 5.5,
    },
    "breast": {
        "shedding_rate": "moderate",
        "expected_clearance_days": 1.8,
        "ctdna_detection_rate_stage_I": 0.30,
        "ctdna_detection_rate_stage_IV": 0.85,
        "common_tracked_genes": ["TP53", "PIK3CA", "ESR1", "ERBB2", "CDH1", "GATA3"],
        "median_lead_time_months": 8.0,
    },
    "lung": {
        "shedding_rate": "high",
        "expected_clearance_days": 1.2,
        "ctdna_detection_rate_stage_I": 0.40,
        "ctdna_detection_rate_stage_IV": 0.90,
        "common_tracked_genes": ["EGFR", "KRAS", "TP53", "ALK", "BRAF", "MET"],
        "median_lead_time_months": 4.0,
    },
    "pancreatic": {
        "shedding_rate": "high",
        "expected_clearance_days": 1.0,
        "ctdna_detection_rate_stage_I": 0.60,
        "ctdna_detection_rate_stage_IV": 0.95,
        "common_tracked_genes": ["KRAS", "TP53", "CDKN2A", "SMAD4"],
        "median_lead_time_months": 3.0,
    },
    "brain": {
        "shedding_rate": "low",
        "expected_clearance_days": 2.0,
        "ctdna_detection_rate_stage_I": 0.05,
        "ctdna_detection_rate_stage_IV": 0.40,
        "common_tracked_genes": ["IDH1", "IDH2", "TP53", "ATRX", "TERT"],
        "median_lead_time_months": 2.0,
    },
    "melanoma": {
        "shedding_rate": "moderate",
        "expected_clearance_days": 1.5,
        "ctdna_detection_rate_stage_I": 0.20,
        "ctdna_detection_rate_stage_IV": 0.85,
        "common_tracked_genes": ["BRAF", "NRAS", "TP53", "CDKN2A", "PTEN"],
        "median_lead_time_months": 4.5,
    },
}

DEFAULT_LOD_VAF = 0.001  # 0.001% = 0.00001 fraction, but we treat as percent


class CtDNAMRDAnalyzer:
    """Analyzes ctDNA dynamics for MRD detection and treatment monitoring."""

    def __init__(self, ctdna_data_path=None, tracked_mutations_path=None,
                 sample_times=None, treatment_start=0, surgery_date=None,
                 cancer_type="colorectal", lod_vaf=DEFAULT_LOD_VAF):
        self.ctdna_data_path = ctdna_data_path
        self.tracked_mutations_path = tracked_mutations_path
        self.sample_times = sample_times or [0, 14, 42, 90, 180]
        self.treatment_start = treatment_start
        self.surgery_date = surgery_date
        self.cancer_type = cancer_type.lower()
        self.lod_vaf = lod_vaf
        self.cancer_profile = CANCER_TYPE_PROFILES.get(
            self.cancer_type, CANCER_TYPE_PROFILES["colorectal"]
        )
        self.timepoint_data = []
        self.tracked_mutations = []

    def _load_ctdna_data(self):
        """Load ctDNA data from TSV or generate demo data."""
        if self.ctdna_data_path and os.path.isfile(self.ctdna_data_path):
            data = []
            with open(self.ctdna_data_path, "r") as fh:
                header = fh.readline().strip().split("\t")
                for line in fh:
                    fields = line.strip().split("\t")
                    row = dict(zip(header, fields))
                    data.append(row)
            return data
        # Demo data: serial ctDNA measurements
        return self._generate_demo_ctdna_data()

    def _generate_demo_ctdna_data(self):
        """Generate demo serial ctDNA data."""
        demo = []
        vaf_trajectory = [5.2, 3.8, 0.45, 0.02, 0.0, 0.0, 0.005, 0.03, 0.12]
        times = [0, 3, 7, 14, 42, 90, 150, 180, 210]
        mutations = ["KRAS_G12D", "TP53_R175H", "APC_R876*", "PIK3CA_E545K"]
        for i, t in enumerate(times):
            base_vaf = vaf_trajectory[i] if i < len(vaf_trajectory) else 0.0
            for mut in mutations:
                noise = (hash(mut + str(t)) % 100) / 500.0
                vaf = max(0.0, base_vaf + noise - 0.1)
                demo.append({
                    "timepoint_day": str(t),
                    "mutation": mut,
                    "vaf_percent": str(round(vaf, 4)),
                    "depth": "10000",
                    "alt_reads": str(max(0, int(vaf / 100.0 * 10000))),
                })
        return demo

    def _load_tracked_mutations(self):
        """Load tracked mutations from VCF or generate demo list."""
        if self.tracked_mutations_path and os.path.isfile(self.tracked_mutations_path):
            mutations = []
            with open(self.tracked_mutations_path, "r") as fh:
                for line in fh:
                    if line.startswith("#"):
                        continue
                    parts = line.strip().split("\t")
                    if len(parts) >= 5:
                        mutations.append({
                            "chrom": parts[0], "pos": parts[1],
                            "ref": parts[3], "alt": parts[4],
                            "gene": parts[2] if len(parts) > 7 else "UNKNOWN"
                        })
            return mutations
        return [
            {"chrom": "12", "pos": "25398284", "ref": "C", "alt": "A", "gene": "KRAS_G12D"},
            {"chrom": "17", "pos": "7577120", "ref": "G", "alt": "A", "gene": "TP53_R175H"},
            {"chrom": "5", "pos": "112175770", "ref": "C", "alt": "T", "gene": "APC_R876*"},
            {"chrom": "3", "pos": "178936091", "ref": "G", "alt": "A", "gene": "PIK3CA_E545K"},
        ]

    def _compute_timepoint_summary(self, raw_data):
        """Compute mean VAF and detection status per timepoint."""
        timepoints = {}
        for row in raw_data:
            day = int(row["timepoint_day"])
            vaf = float(row["vaf_percent"])
            if day not in timepoints:
                timepoints[day] = {"vafs": [], "depths": [], "alt_reads": []}
            timepoints[day]["vafs"].append(vaf)
            timepoints[day]["depths"].append(int(row.get("depth", 10000)))
            timepoints[day]["alt_reads"].append(int(row.get("alt_reads", 0)))

        summaries = []
        for day in sorted(timepoints.keys()):
            vafs = timepoints[day]["vafs"]
            mean_vaf = sum(vafs) / len(vafs) if vafs else 0.0
            detected = any(v > self.lod_vaf for v in vafs)
            n_detected = sum(1 for v in vafs if v > self.lod_vaf)
            summaries.append({
                "day": day,
                "mean_vaf_percent": round(mean_vaf, 5),
                "max_vaf_percent": round(max(vafs), 5) if vafs else 0.0,
                "n_mutations_detected": n_detected,
                "n_mutations_tracked": len(vafs),
                "ctdna_detected": detected,
                "mean_depth": int(sum(timepoints[day]["depths"]) / len(timepoints[day]["depths"])),
            })
        return summaries

    def _calculate_half_life(self, timepoint_summaries):
        """Calculate ctDNA half-life from exponential decay fit post-surgery."""
        ref_day = self.surgery_date if self.surgery_date is not None else self.treatment_start
        post_treatment = [tp for tp in timepoint_summaries
                          if tp["day"] >= ref_day and tp["mean_vaf_percent"] > 0]
        if len(post_treatment) < 2:
            return {"half_life_days": None, "decay_rate": None,
                    "fit_quality": "insufficient_data"}
        # Find peak and subsequent decline
        peak_idx = 0
        for i, tp in enumerate(post_treatment):
            if tp["mean_vaf_percent"] >= post_treatment[peak_idx]["mean_vaf_percent"]:
                peak_idx = i
        declining = post_treatment[peak_idx:]
        if len(declining) < 2:
            return {"half_life_days": None, "decay_rate": None,
                    "fit_quality": "insufficient_decline_data"}
        # Simple log-linear fit
        t0 = declining[0]["day"]
        v0 = declining[0]["mean_vaf_percent"]
        if v0 <= 0:
            return {"half_life_days": None, "decay_rate": None,
                    "fit_quality": "zero_baseline"}
        rates = []
        for tp in declining[1:]:
            dt = tp["day"] - t0
            if dt > 0 and tp["mean_vaf_percent"] > 0:
                k = -math.log(tp["mean_vaf_percent"] / v0) / dt
                rates.append(k)
        if not rates:
            return {"half_life_days": None, "decay_rate": None,
                    "fit_quality": "no_valid_rates"}
        avg_k = sum(rates) / len(rates)
        half_life = math.log(2) / avg_k if avg_k > 0 else None
        normal_halflife_note = "Normal cfDNA half-life ~1-2 hours; tumor ctDNA clearance ~1-2 days"
        return {
            "half_life_days": round(half_life, 2) if half_life else None,
            "decay_rate_per_day": round(avg_k, 5) if avg_k else None,
            "fit_quality": "estimated",
            "reference": normal_halflife_note,
            "expected_clearance_days": self.cancer_profile["expected_clearance_days"],
        }

    def _calculate_response_rates(self, timepoint_summaries):
        """Calculate % reduction from baseline at each timepoint."""
        if not timepoint_summaries:
            return []
        baseline_vaf = timepoint_summaries[0]["mean_vaf_percent"]
        if baseline_vaf <= 0:
            return [{"day": tp["day"], "reduction_percent": 0.0} for tp in timepoint_summaries]
        responses = []
        for tp in timepoint_summaries:
            reduction = ((baseline_vaf - tp["mean_vaf_percent"]) / baseline_vaf) * 100.0
            responses.append({
                "day": tp["day"],
                "mean_vaf_percent": tp["mean_vaf_percent"],
                "reduction_percent": round(reduction, 2),
            })
        return responses

    def _check_early_molecular_response(self, timepoint_summaries):
        """Check for early molecular response (>50% drop at day 14-21)."""
        if not timepoint_summaries:
            return {"emr_achieved": False, "detail": "no data"}
        baseline = timepoint_summaries[0]["mean_vaf_percent"]
        if baseline <= 0:
            return {"emr_achieved": False, "detail": "zero baseline"}
        for tp in timepoint_summaries:
            if 14 <= tp["day"] <= 21:
                reduction = ((baseline - tp["mean_vaf_percent"]) / baseline) * 100.0
                achieved = reduction >= 50.0
                return {
                    "emr_achieved": achieved,
                    "emr_day": tp["day"],
                    "reduction_percent": round(reduction, 2),
                    "threshold": ">=50% reduction at day 14-21",
                }
        return {"emr_achieved": False, "detail": "no timepoint in day 14-21 window"}

    def _classify_mrd_status(self, timepoint_summaries):
        """Classify MRD status at each timepoint."""
        results = []
        for tp in timepoint_summaries:
            if tp["ctdna_detected"]:
                status = "ctDNA-positive (MRD+)"
            else:
                status = "ctDNA-negative (MRD-)"
            results.append({
                "day": tp["day"],
                "mrd_status": status,
                "n_mutations_detected": tp["n_mutations_detected"],
                "sensitivity_note": f"Tracking {tp['n_mutations_tracked']} mutations at ~{tp['mean_depth']}x depth",
            })
        return results

    def _detect_relapse_pattern(self, timepoint_summaries):
        """Detect rising ctDNA patterns indicating molecular relapse."""
        if len(timepoint_summaries) < 3:
            return {"relapse_detected": False, "detail": "insufficient timepoints"}
        # Find nadir
        nadir_idx = 0
        for i, tp in enumerate(timepoint_summaries):
            if tp["mean_vaf_percent"] <= timepoint_summaries[nadir_idx]["mean_vaf_percent"]:
                nadir_idx = i
        post_nadir = timepoint_summaries[nadir_idx:]
        consecutive_rises = 0
        rise_start = None
        for i in range(1, len(post_nadir)):
            if post_nadir[i]["mean_vaf_percent"] > post_nadir[i - 1]["mean_vaf_percent"]:
                consecutive_rises += 1
                if rise_start is None:
                    rise_start = post_nadir[i - 1]["day"]
            else:
                consecutive_rises = 0
                rise_start = None
        rising_pattern = consecutive_rises >= 2
        # Doubling time estimation
        doubling_time = None
        if rising_pattern and rise_start is not None:
            rising_pts = [tp for tp in post_nadir if tp["day"] >= rise_start and tp["mean_vaf_percent"] > 0]
            if len(rising_pts) >= 2:
                v1 = rising_pts[0]["mean_vaf_percent"]
                v2 = rising_pts[-1]["mean_vaf_percent"]
                dt = rising_pts[-1]["day"] - rising_pts[0]["day"]
                if v2 > v1 and dt > 0:
                    doubling_time = round(dt * math.log(2) / math.log(v2 / v1), 1)
        lead_time = self.cancer_profile.get("median_lead_time_months", 5.0)
        return {
            "relapse_detected": rising_pattern,
            "consecutive_rises": consecutive_rises,
            "rise_start_day": rise_start,
            "doubling_time_days": doubling_time,
            "expected_clinical_lead_time_months": lead_time,
            "note": f"ctDNA molecular relapse precedes clinical relapse by median {lead_time} months",
        }

    def _classify_treatment_response(self, timepoint_summaries):
        """Classify treatment response based on ctDNA dynamics."""
        if len(timepoint_summaries) < 2:
            return {"classification": "insufficient_data"}
        baseline = timepoint_summaries[0]["mean_vaf_percent"]
        latest = timepoint_summaries[-1]["mean_vaf_percent"]
        if baseline <= 0:
            return {"classification": "no_baseline_ctdna"}
        reduction = ((baseline - latest) / baseline) * 100.0
        undetectable = not timepoint_summaries[-1]["ctdna_detected"]
        if undetectable:
            classification = "major_molecular_response"
            description = "ctDNA undetectable post-treatment"
        elif reduction >= 90:
            classification = "molecular_response"
            description = ">90% ctDNA reduction"
        elif reduction >= 50:
            classification = "partial_molecular_response"
            description = "50-90% ctDNA reduction"
        elif reduction > 0:
            classification = "molecular_non_response"
            description = "<50% reduction"
        else:
            # Check for rising pattern
            rising = sum(1 for i in range(1, len(timepoint_summaries))
                         if timepoint_summaries[i]["mean_vaf_percent"] >
                         timepoint_summaries[i - 1]["mean_vaf_percent"])
            if rising >= 2:
                classification = "molecular_progression"
                description = "Confirmed ctDNA rise"
            else:
                classification = "molecular_non_response"
                description = "<50% reduction or rising trend"
        return {
            "classification": classification,
            "description": description,
            "baseline_vaf_percent": round(baseline, 5),
            "latest_vaf_percent": round(latest, 5),
            "reduction_percent": round(reduction, 2),
        }

    def _cancer_type_context(self):
        """Provide cancer type-specific context."""
        return {
            "cancer_type": self.cancer_type,
            "shedding_rate": self.cancer_profile["shedding_rate"],
            "expected_clearance_days": self.cancer_profile["expected_clearance_days"],
            "common_tracked_genes": self.cancer_profile["common_tracked_genes"],
            "detection_rate_stage_I": self.cancer_profile["ctdna_detection_rate_stage_I"],
            "detection_rate_stage_IV": self.cancer_profile["ctdna_detection_rate_stage_IV"],
            "median_lead_time_months": self.cancer_profile["median_lead_time_months"],
        }

    def analyze(self):
        """Run the full ctDNA MRD analysis pipeline."""
        raw_data = self._load_ctdna_data()
        self.tracked_mutations = self._load_tracked_mutations()
        timepoint_summaries = self._compute_timepoint_summary(raw_data)
        kinetic_params = self._calculate_half_life(timepoint_summaries)
        response_rates = self._calculate_response_rates(timepoint_summaries)
        emr = self._check_early_molecular_response(timepoint_summaries)
        mrd_status = self._classify_mrd_status(timepoint_summaries)
        relapse_risk = self._detect_relapse_pattern(timepoint_summaries)
        response_class = self._classify_treatment_response(timepoint_summaries)
        cancer_context = self._cancer_type_context()

        molecular_timeline = []
        for tp in timepoint_summaries:
            events = []
            if tp["day"] == self.treatment_start:
                events.append("treatment_start")
            if self.surgery_date is not None and tp["day"] == self.surgery_date:
                events.append("surgery")
            if tp["ctdna_detected"]:
                events.append("ctdna_positive")
            else:
                events.append("ctdna_negative")
            molecular_timeline.append({
                "day": tp["day"],
                "mean_vaf_percent": tp["mean_vaf_percent"],
                "events": events,
            })

        results = {
            "analysis": "ctDNA_dynamics_and_MRD_analysis",
            "analysis_date": datetime.now().isoformat(),
            "cancer_type_context": cancer_context,
            "n_tracked_mutations": len(self.tracked_mutations),
            "timepoint_data": timepoint_summaries,
            "kinetic_parameters": kinetic_params,
            "response_rates": response_rates,
            "early_molecular_response": emr,
            "mrd_status": mrd_status,
            "response_classification": response_class,
            "relapse_risk": relapse_risk,
            "molecular_timeline": molecular_timeline,
            "lod_vaf_percent": self.lod_vaf,
        }
        return results


def main():
    parser = argparse.ArgumentParser(
        description="ctDNA dynamics and MRD analysis"
    )
    parser.add_argument("--ctdna_data", default=None,
                        help="Path to serial ctDNA measurements (TSV)")
    parser.add_argument("--tracked_mutations", default=None,
                        help="Path to tracked tumor mutations (VCF)")
    parser.add_argument("--sample_times", default="0,14,42,90,180",
                        help="Comma-separated sample timepoints in days")
    parser.add_argument("--treatment_start", type=int, default=0,
                        help="Day of treatment start")
    parser.add_argument("--surgery_date", type=int, default=None,
                        help="Day of surgery")
    parser.add_argument("--cancer_type", default="colorectal",
                        help="Cancer type (colorectal, breast, lung, pancreatic, brain, melanoma)")
    parser.add_argument("--lod", type=float, default=DEFAULT_LOD_VAF,
                        help="Limit of detection (VAF percent)")
    parser.add_argument("--output", default="mrd_analysis/",
                        help="Output directory or JSON file path")
    args = parser.parse_args()

    sample_times = [int(x) for x in args.sample_times.split(",")]

    analyzer = CtDNAMRDAnalyzer(
        ctdna_data_path=args.ctdna_data,
        tracked_mutations_path=args.tracked_mutations,
        sample_times=sample_times,
        treatment_start=args.treatment_start,
        surgery_date=args.surgery_date,
        cancer_type=args.cancer_type,
        lod_vaf=args.lod,
    )

    results = analyzer.analyze()

    output_path = args.output
    if output_path.endswith("/"):
        os.makedirs(output_path, exist_ok=True)
        output_path = os.path.join(output_path, "ctdna_mrd_results.json")

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as fh:
        json.dump(results, fh, indent=2)

    print(f"ctDNA MRD analysis complete. Results written to: {output_path}")
    print(f"  Cancer type: {results['cancer_type_context']['cancer_type']}")
    print(f"  Tracked mutations: {results['n_tracked_mutations']}")
    print(f"  Response: {results['response_classification']['classification']}")
    latest_mrd = results["mrd_status"][-1] if results["mrd_status"] else {}
    print(f"  Latest MRD status: {latest_mrd.get('mrd_status', 'N/A')}")
    print(f"  Relapse risk: {'DETECTED' if results['relapse_risk']['relapse_detected'] else 'not detected'}")


if __name__ == "__main__":
    main()

__AUTHOR_SIGNATURE__ = "9a7f3c2e-MD-BABU-MIA-2026-MSSM-SECURE"

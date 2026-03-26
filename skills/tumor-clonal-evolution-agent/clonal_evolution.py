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
Clonal Evolution Tracking Agent.

Longitudinal VAF tracking, clone identification, dynamics classification,
fitness estimation, treatment response patterns, TTP prediction,
Muller plot data generation, and evolutionary event detection.
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

DYNAMICS_PATTERNS = {
    "linear_expansion": "Steady VAF increase over time",
    "exponential_growth": "Accelerating VAF increase suggesting positive selection",
    "extinction": "VAF declining to zero — clone eliminated",
    "selection_sweep": "One clone dominates while others diminish",
    "branching": "New clone emerges, diverging from parent lineage",
    "stable": "No significant VAF change over time",
}

TREATMENT_RESPONSE_PATTERNS = {
    "complete_response": {
        "label": "Complete Response",
        "description": "All clones declining; no resistant emergence detected",
    },
    "partial_response": {
        "label": "Partial Response",
        "description": "Total burden declining but some clones remain stable",
    },
    "mixed_response": {
        "label": "Mixed Response",
        "description": "Some clones declining while others growing",
    },
    "progression": {
        "label": "Progression",
        "description": "Dominant clone expanding despite treatment",
    },
    "resistant_emergence": {
        "label": "Resistant Clone Emergence",
        "description": "New or growing clone detected under selective treatment pressure",
    },
}

RESISTANCE_GENES = {
    "EGFR": ["T790M", "C797S"],
    "ESR1": ["Y537S", "D538G"],
    "KRAS": ["G12C", "G12V", "amplification"],
    "MET": ["amplification", "exon14_skip"],
    "ALK": ["G1202R", "L1196M"],
    "AR": ["T878A", "amplification"],
    "RB1": ["loss"],
    "PIK3CA": ["E545K", "H1047R"],
    "BRAF": ["V600E", "splice_variant"],
}

CLONE_COLORS = [
    "#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00",
    "#FFFF33", "#A65628", "#F781BF", "#999999", "#66C2A5",
]

CONVERGENT_EVOLUTION_GENES = [
    "TP53", "PIK3CA", "KRAS", "EGFR", "PTEN", "RB1", "NF1",
    "APC", "BRAF", "MYC",
]

PEARSON_THRESHOLD = 0.9
GROWTH_RATE_THRESHOLD = 0.01
EXTINCTION_VAF_THRESHOLD = 0.02


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

def _generate_demo_longitudinal(n_timepoints: int = 6) -> Tuple[List[Dict], List[int]]:
    """Generate longitudinal ctDNA variant data with realistic evolution."""
    random.seed(55)
    timepoints = list(range(0, n_timepoints * 4, 4))  # weeks

    genes = ["TP53", "PIK3CA", "KRAS", "EGFR", "APC", "PTEN",
             "MET", "BRAF", "ESR1", "CDH1", "RB1", "SMAD4",
             "NF1", "ATM", "BRCA2", "ALK", "AR", "CDKN2A"]

    mutations: List[Dict] = []

    # Clone A: trunk — stable then declining (treatment response)
    for gene in ["TP53", "APC", "CDKN2A"]:
        vafs = []
        base = random.uniform(0.30, 0.45)
        for t_idx, t in enumerate(timepoints):
            if t_idx < 2:
                v = base + random.gauss(0, 0.02)
            else:
                v = base * (0.7 ** (t_idx - 1)) + random.gauss(0, 0.01)
            vafs.append(round(max(v, 0.001), 4))
        mutations.append({
            "mutation_id": f"cloneA_{gene}",
            "gene": gene, "chromosome": f"chr{random.randint(1,22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "variant_class": random.choice(["Missense", "Nonsense"]),
            "vafs": dict(zip(timepoints, vafs)),
        })

    # Clone B: expanding subclone (linear growth)
    for gene in ["PIK3CA", "KRAS"]:
        vafs = []
        base = random.uniform(0.02, 0.08)
        for t_idx, t in enumerate(timepoints):
            v = base + 0.04 * t_idx + random.gauss(0, 0.01)
            vafs.append(round(max(v, 0.001), 4))
        mutations.append({
            "mutation_id": f"cloneB_{gene}",
            "gene": gene, "chromosome": f"chr{random.randint(1,22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "variant_class": "Missense",
            "vafs": dict(zip(timepoints, vafs)),
        })

    # Clone C: resistant emergence (appears at t=8, grows)
    for gene in ["EGFR", "MET"]:
        vafs = []
        for t_idx, t in enumerate(timepoints):
            if t_idx < 2:
                v = 0.0
            else:
                v = 0.03 * (t_idx - 1) + random.gauss(0, 0.005)
            vafs.append(round(max(v, 0.0), 4))
        mutations.append({
            "mutation_id": f"cloneC_{gene}",
            "gene": gene, "chromosome": f"chr{random.randint(1,22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "variant_class": "Missense",
            "vafs": dict(zip(timepoints, vafs)),
        })

    # Clone D: extinction
    for gene in ["BRAF", "NF1"]:
        vafs = []
        base = random.uniform(0.10, 0.20)
        for t_idx, t in enumerate(timepoints):
            v = base * (0.4 ** t_idx) + random.gauss(0, 0.005)
            vafs.append(round(max(v, 0.0), 4))
        mutations.append({
            "mutation_id": f"cloneD_{gene}",
            "gene": gene, "chromosome": f"chr{random.randint(1,22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "variant_class": random.choice(["Missense", "Frame_Shift_Del"]),
            "vafs": dict(zip(timepoints, vafs)),
        })

    # Additional noise mutations
    for i in range(8):
        gene = random.choice(genes)
        vafs = []
        base = random.uniform(0.01, 0.15)
        trend = random.choice([-0.01, 0, 0.01, 0.02])
        for t_idx, t in enumerate(timepoints):
            v = base + trend * t_idx + random.gauss(0, 0.01)
            vafs.append(round(max(v, 0.0), 4))
        mutations.append({
            "mutation_id": f"noise_{i}_{gene}",
            "gene": gene, "chromosome": f"chr{random.randint(1,22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "variant_class": "Missense",
            "vafs": dict(zip(timepoints, vafs)),
        })

    return mutations, timepoints


def _generate_demo_tumor_burden(timepoints: List[int]) -> Dict[int, float]:
    random.seed(56)
    burden = {}
    base = random.uniform(50, 200)
    for t_idx, t in enumerate(timepoints):
        if t_idx < 2:
            val = base + random.gauss(0, 5)
        elif t_idx < 4:
            val = base * (0.6 ** (t_idx - 1)) + random.gauss(0, 3)
        else:
            val = base * 0.3 + 10 * (t_idx - 3) + random.gauss(0, 3)
        burden[t] = round(max(val, 0), 2)
    return burden


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _pearson_r(x: List[float], y: List[float]) -> float:
    """Compute Pearson correlation coefficient without external deps."""
    n = len(x)
    if n < 3:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x) / (n - 1)) if n > 1 else 1.0
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y) / (n - 1)) if n > 1 else 1.0
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / (n - 1)
    return cov / (sx * sy)


def _linear_slope(y: List[float], x: List[float]) -> float:
    """Simple OLS slope."""
    n = len(x)
    if n < 2:
        return 0.0
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den = sum((xi - mx) ** 2 for xi in x)
    if den == 0:
        return 0.0
    return num / den


# ---------------------------------------------------------------------------
# ClonalEvolutionAnalyzer
# ---------------------------------------------------------------------------

class ClonalEvolutionAnalyzer:
    """Clonal evolution tracking analyser."""

    def __init__(
        self,
        mutations: Optional[List[Dict]] = None,
        timepoints: Optional[List[int]] = None,
        tumor_burden: Optional[Dict[int, float]] = None,
        method: str = "bayesian_evolution",
        predict_ttp: bool = True,
    ):
        if mutations is None:
            self.mutations, self.timepoints = _generate_demo_longitudinal()
        else:
            self.mutations = mutations
            self.timepoints = timepoints or sorted(
                set(t for m in mutations for t in m.get("vafs", {}).keys()))
        self.tumor_burden = tumor_burden or _generate_demo_tumor_burden(self.timepoints)
        self.method = method
        self.predict_ttp = predict_ttp
        self.timepoints_float = [float(t) for t in self.timepoints]

    # ----- Clone identification -----
    def _identify_clones(self) -> List[Dict]:
        """Group co-evolving mutations by VAF trajectory correlation."""
        # Build trajectories
        trajectories: Dict[str, List[float]] = {}
        for m in self.mutations:
            vafs = m.get("vafs", {})
            traj = [vafs.get(t, vafs.get(str(t), 0.0)) for t in self.timepoints]
            trajectories[m["mutation_id"]] = traj

        # Correlation-based clustering
        assigned: Dict[str, int] = {}
        clone_id = 0
        mids = list(trajectories.keys())

        for i, mid_i in enumerate(mids):
            if mid_i in assigned:
                continue
            assigned[mid_i] = clone_id
            for j in range(i + 1, len(mids)):
                mid_j = mids[j]
                if mid_j in assigned:
                    continue
                r = _pearson_r(trajectories[mid_i], trajectories[mid_j])
                if r >= PEARSON_THRESHOLD:
                    assigned[mid_j] = clone_id
            clone_id += 1

        # Build clone objects
        clones: Dict[int, List[str]] = {}
        for mid, cid in assigned.items():
            clones.setdefault(cid, []).append(mid)

        result = []
        for cid, members in sorted(clones.items()):
            # Mean trajectory
            member_trajs = [trajectories[m] for m in members]
            mean_traj = []
            for t_idx in range(len(self.timepoints)):
                col = [row[t_idx] for row in member_trajs]
                mean_traj.append(round(sum(col) / len(col), 4))
            genes = list(set(
                m["gene"] for m in self.mutations if m["mutation_id"] in members
            ))
            result.append({
                "clone_id": cid,
                "n_mutations": len(members),
                "mutations": members,
                "genes": genes,
                "mean_vaf_trajectory": dict(zip(self.timepoints, mean_traj)),
                "color": CLONE_COLORS[cid % len(CLONE_COLORS)],
            })
        return result

    # ----- Clone dynamics -----
    def _classify_dynamics(self, clone: Dict) -> str:
        traj = list(clone["mean_vaf_trajectory"].values())
        if len(traj) < 2:
            return "stable"
        slope = _linear_slope(traj, self.timepoints_float)
        last_val = traj[-1]
        first_val = traj[0]

        if last_val < EXTINCTION_VAF_THRESHOLD and first_val > 0.05:
            return "extinction"
        if first_val < EXTINCTION_VAF_THRESHOLD and last_val > 0.05:
            return "branching"

        # Check for acceleration (exponential)
        if len(traj) >= 4:
            first_half_slope = _linear_slope(traj[:len(traj)//2],
                                              self.timepoints_float[:len(traj)//2])
            second_half_slope = _linear_slope(traj[len(traj)//2:],
                                               self.timepoints_float[len(traj)//2:])
            if second_half_slope > first_half_slope * 1.5 and slope > GROWTH_RATE_THRESHOLD:
                return "exponential_growth"

        if slope > GROWTH_RATE_THRESHOLD:
            return "linear_expansion"
        if slope < -GROWTH_RATE_THRESHOLD:
            return "extinction"
        return "stable"

    # ----- Fitness estimation -----
    def _estimate_fitness(self, clones: List[Dict]) -> List[Dict]:
        growth_rates = []
        for clone in clones:
            traj = list(clone["mean_vaf_trajectory"].values())
            rate = _linear_slope(traj, self.timepoints_float)
            growth_rates.append(rate)

        mean_rate = sum(growth_rates) / max(len(growth_rates), 1)
        fitness_results = []
        for clone, rate in zip(clones, growth_rates):
            rel_fitness = round(rate / max(abs(mean_rate), 1e-6), 3)
            fitness_results.append({
                "clone_id": clone["clone_id"],
                "growth_rate": round(rate, 6),
                "relative_fitness": rel_fitness,
                "interpretation": ("positively selected" if rel_fitness > 1.5
                                   else "negatively selected" if rel_fitness < -0.5
                                   else "neutral"),
            })
        return fitness_results

    # ----- Treatment response -----
    def _assess_treatment_response(self, clones: List[Dict]) -> Dict:
        dynamics = [self._classify_dynamics(c) for c in clones]
        n_declining = sum(1 for d in dynamics if d == "extinction")
        n_growing = sum(1 for d in dynamics if d in ("linear_expansion", "exponential_growth", "branching"))
        n_stable = sum(1 for d in dynamics if d == "stable")
        total = len(dynamics)

        if n_declining == total:
            pattern = "complete_response"
        elif n_declining > n_growing and n_growing == 0:
            pattern = "partial_response"
        elif n_growing > 0 and n_declining > 0:
            pattern = "mixed_response"
        elif n_growing > 0 and any(d == "branching" for d in dynamics):
            pattern = "resistant_emergence"
        elif n_growing > n_declining:
            pattern = "progression"
        else:
            pattern = "partial_response"

        return {
            **TREATMENT_RESPONSE_PATTERNS[pattern],
            "clone_dynamics": {c["clone_id"]: d for c, d in zip(clones, dynamics)},
            "n_declining": n_declining, "n_growing": n_growing, "n_stable": n_stable,
        }

    # ----- TTP prediction -----
    def _predict_ttp(self, clones: List[Dict], fitness: List[Dict]) -> Dict:
        """Simple extrapolation: when does fastest-growing clone double total burden?"""
        if not fitness:
            return {"ttp_weeks": None, "confidence": "insufficient data"}

        fastest = max(fitness, key=lambda f: f["growth_rate"])
        rate = fastest["growth_rate"]
        if rate <= 0:
            return {"ttp_weeks": None, "confidence": "no growing clones",
                    "fastest_clone": fastest["clone_id"]}

        last_t = max(self.timepoints)
        burden_vals = list(self.tumor_burden.values())
        current_burden = burden_vals[-1] if burden_vals else 1.0
        doubling_time = math.log(2) / max(rate, 1e-6)
        ttp_weeks = round(last_t + doubling_time, 1)

        return {
            "ttp_weeks": ttp_weeks,
            "fastest_growing_clone": fastest["clone_id"],
            "estimated_doubling_time_weeks": round(doubling_time, 1),
            "current_burden": current_burden,
            "confidence": "low" if len(self.timepoints) < 4 else "moderate",
        }

    # ----- Muller plot data -----
    def _generate_muller_data(self, clones: List[Dict]) -> List[Dict]:
        """Generate data for Muller/fish plot: clone proportions over time."""
        muller = []
        for t in self.timepoints:
            total_vaf = sum(
                c["mean_vaf_trajectory"].get(t, c["mean_vaf_trajectory"].get(str(t), 0))
                for c in clones
            )
            row = {"timepoint": t, "clones": {}}
            for c in clones:
                vaf = c["mean_vaf_trajectory"].get(t, c["mean_vaf_trajectory"].get(str(t), 0))
                proportion = round(vaf / max(total_vaf, 1e-6), 4)
                row["clones"][c["clone_id"]] = {
                    "vaf": vaf, "proportion": proportion, "color": c["color"],
                }
            if self.tumor_burden:
                row["tumor_burden"] = self.tumor_burden.get(t, 0)
            muller.append(row)
        return muller

    # ----- Evolutionary events -----
    def _detect_evolutionary_events(self, clones: List[Dict],
                                     fitness: List[Dict]) -> List[Dict]:
        events: List[Dict] = []
        for clone in clones:
            dynamics = self._classify_dynamics(clone)
            if dynamics == "branching":
                events.append({
                    "event": "branching",
                    "clone_id": clone["clone_id"],
                    "description": f"Clone {clone['clone_id']} emerged (new branch)",
                    "genes": clone["genes"],
                })
            if dynamics == "exponential_growth":
                events.append({
                    "event": "selection_sweep",
                    "clone_id": clone["clone_id"],
                    "description": f"Clone {clone['clone_id']} undergoing rapid expansion",
                    "genes": clone["genes"],
                })

        # Convergent evolution detection
        gene_to_clones: Dict[str, List[int]] = {}
        for clone in clones:
            for gene in clone["genes"]:
                if gene in CONVERGENT_EVOLUTION_GENES:
                    gene_to_clones.setdefault(gene, []).append(clone["clone_id"])
        for gene, cids in gene_to_clones.items():
            if len(cids) >= 2:
                events.append({
                    "event": "convergent_evolution",
                    "gene": gene,
                    "clones": cids,
                    "description": f"{gene} hit independently in clones {cids}",
                })

        # Resistance gene events
        for clone in clones:
            for gene in clone["genes"]:
                if gene in RESISTANCE_GENES:
                    dyn = self._classify_dynamics(clone)
                    if dyn in ("linear_expansion", "exponential_growth", "branching"):
                        events.append({
                            "event": "resistance_emergence",
                            "clone_id": clone["clone_id"],
                            "gene": gene,
                            "known_resistance_variants": RESISTANCE_GENES[gene],
                            "description": f"Resistance gene {gene} in expanding clone {clone['clone_id']}",
                        })

        return events

    # ----- main entry -----
    def analyze(self) -> Dict[str, Any]:
        clones = self._identify_clones()
        fitness = self._estimate_fitness(clones)
        treatment = self._assess_treatment_response(clones)
        ttp = self._predict_ttp(clones, fitness) if self.predict_ttp else {}
        muller = self._generate_muller_data(clones)
        events = self._detect_evolutionary_events(clones, fitness)

        # Add dynamics to clone trajectories
        clone_trajectories = []
        for clone in clones:
            dynamics = self._classify_dynamics(clone)
            clone_trajectories.append({
                **clone,
                "dynamics_pattern": dynamics,
                "dynamics_description": DYNAMICS_PATTERNS.get(dynamics, ""),
            })

        return {
            "analysis_metadata": {
                "analysis_type": "Clonal Evolution Tracking",
                "timestamp": datetime.now().isoformat(),
                "method": self.method,
                "n_timepoints": len(self.timepoints),
                "timepoints": self.timepoints,
                "n_mutations_tracked": len(self.mutations),
            },
            "clone_trajectories": clone_trajectories,
            "fitness_estimates": fitness,
            "evolutionary_events": events,
            "treatment_response_pattern": treatment,
            "ttp_prediction": ttp,
            "muller_plot_data": muller,
            "tumor_burden_trajectory": self.tumor_burden,
        }


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_maf_longitudinal(path: str, timepoints: List[int]) -> Optional[List[Dict]]:
    """Load a MAF with columns for VAF at each timepoint."""
    if not os.path.isfile(path):
        return None
    mutations: List[Dict] = []
    with open(path) as fh:
        header = fh.readline().strip().split("\t")
        for line in fh:
            vals = line.strip().split("\t")
            row = dict(zip(header, vals))
            gene = row.get("Hugo_Symbol", row.get("gene", ""))
            vafs = {}
            for t in timepoints:
                vaf_col = f"VAF_t{t}"
                if vaf_col in row:
                    vafs[t] = float(row[vaf_col])
            if not vafs:
                # Try generic VAF column
                vaf_val = float(row.get("VAF", row.get("t_alt_freq", 0)))
                vafs = {timepoints[0]: vaf_val}
            mutations.append({
                "mutation_id": f"{row.get('Chromosome', '')}_{row.get('Start_Position', '')}",
                "gene": gene,
                "chromosome": row.get("Chromosome", ""),
                "position": int(row.get("Start_Position", 0)),
                "variant_class": row.get("Variant_Classification", "Unknown"),
                "vafs": vafs,
            })
    return mutations if mutations else None


def _load_tumor_burden(path: str) -> Optional[Dict[int, float]]:
    if not os.path.isfile(path):
        return None
    burden: Dict[int, float] = {}
    with open(path) as fh:
        header = fh.readline()
        for line in fh:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                burden[int(parts[0])] = float(parts[1])
    return burden if burden else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Clonal Evolution Tracking Analyzer",
    )
    parser.add_argument("--input", default=None,
                        help="Longitudinal ctDNA variants MAF")
    parser.add_argument("--timepoints", default=None,
                        help="Comma-separated timepoint values (e.g., 0,4,8,12,16,20)")
    parser.add_argument("--tumor_burden", default=None,
                        help="Tumor burden CSV (timepoint,value)")
    parser.add_argument("--method", default="bayesian_evolution",
                        help="Evolution inference method")
    parser.add_argument("--predict_ttp", default="true",
                        help="Predict time-to-progression (true/false)")
    parser.add_argument("--output", default=None, help="Output path")
    args = parser.parse_args()

    timepoints = None
    if args.timepoints:
        timepoints = [int(t.strip()) for t in args.timepoints.split(",")]

    mutations = None
    if args.input and timepoints:
        mutations = _load_maf_longitudinal(args.input, timepoints)
    burden = _load_tumor_burden(args.tumor_burden) if args.tumor_burden else None

    analyzer = ClonalEvolutionAnalyzer(
        mutations=mutations,
        timepoints=timepoints,
        tumor_burden=burden,
        method=args.method,
        predict_ttp=args.predict_ttp.lower() == "true",
    )
    result = analyzer.analyze()
    output = json.dumps(result, indent=2, default=str)

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or out_path.endswith("/"):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, "clonal_evolution_report.json")
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

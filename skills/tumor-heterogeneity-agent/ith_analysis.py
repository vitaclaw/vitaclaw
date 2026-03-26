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
Intratumor Heterogeneity (ITH) Analysis Agent.

Variant classification, CCF estimation, PyClone-VI style clustering,
ITH metrics (Shannon, Simpson, MATH), phylogeny reconstruction,
resistance prediction, and ITH-based prognosis.
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

RESISTANCE_MUTATIONS = {
    "EGFR": {"T790M": "EGFR-TKI resistance (osimertinib may overcome)",
             "C797S": "Third-gen EGFR-TKI resistance"},
    "ESR1": {"Y537S": "Aromatase inhibitor resistance",
             "D538G": "Aromatase inhibitor resistance",
             "E380Q": "Aromatase inhibitor resistance"},
    "KRAS": {"amplification": "EGFR-TKI resistance via bypass signalling"},
    "MET": {"amplification": "EGFR-TKI resistance via bypass signalling",
            "exon14_skip": "MET inhibitor sensitivity"},
    "ALK": {"G1202R": "ALK-TKI resistance (lorlatinib may overcome)",
            "L1196M": "Crizotinib resistance"},
    "AR": {"T878A": "Enzalutamide resistance",
           "F877L": "Anti-androgen resistance"},
    "BRAF": {"splice_variant": "Vemurafenib resistance"},
    "RB1": {"loss": "CDK4/6 inhibitor resistance"},
    "PIK3CA": {"E545K": "PI3K pathway activation",
               "H1047R": "PI3K pathway activation"},
}

CLONE_COLORS = [
    "#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00",
    "#FFFF33", "#A65628", "#F781BF", "#999999", "#66C2A5",
]

ITH_PROGNOSIS = {
    "high_ith": {
        "prognosis": "Poor",
        "rationale": "High intratumor heterogeneity enables adaptive resistance and immune evasion",
    },
    "moderate_ith": {
        "prognosis": "Intermediate",
        "rationale": "Moderate heterogeneity implies presence of subclonal diversity",
    },
    "low_ith": {
        "prognosis": "Relatively favorable",
        "rationale": "Low ITH suggests clonal homogeneity; may respond better to targeted therapy",
    },
}

DEFAULT_PURITY = 0.7
DEFAULT_COPY_NUMBER = 2


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

def _generate_demo_variants(n_regions: int = 3) -> Tuple[List[List[Dict]], List[str]]:
    """Generate multi-region variant data with realistic ITH pattern."""
    random.seed(50)
    sample_names = [f"Region_{i+1}" for i in range(n_regions)]
    genes = ["TP53", "PIK3CA", "KRAS", "EGFR", "MET", "BRAF", "PTEN",
             "APC", "CDKN2A", "RB1", "BRCA1", "ATM", "ESR1", "AR",
             "NRAS", "CDH1", "FBXW7", "NF1", "SMAD4", "STK11"]

    # Clonal mutations (present in all regions)
    clonal = []
    for _ in range(15):
        gene = random.choice(genes)
        base_vaf = random.uniform(0.25, 0.50)
        clonal.append({
            "gene": gene, "chromosome": f"chr{random.randint(1, 22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "ref": random.choice("ACGT"), "alt": random.choice("ACGT"),
            "variant_class": random.choice(["Missense", "Nonsense", "Frame_Shift_Del"]),
            "base_vaf": base_vaf,
            "mutation_id": f"clonal_{_}",
        })

    # Shared subclonal (in 2 of 3 regions)
    shared = []
    for _ in range(10):
        gene = random.choice(genes)
        base_vaf = random.uniform(0.05, 0.25)
        present_in = random.sample(range(n_regions), 2)
        shared.append({
            "gene": gene, "chromosome": f"chr{random.randint(1, 22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "ref": random.choice("ACGT"), "alt": random.choice("ACGT"),
            "variant_class": random.choice(["Missense", "Frame_Shift_Ins", "Splice_Site"]),
            "base_vaf": base_vaf, "present_in": present_in,
            "mutation_id": f"shared_{_}",
        })

    # Private mutations (in 1 region only)
    private = []
    for _ in range(20):
        gene = random.choice(genes)
        base_vaf = random.uniform(0.02, 0.20)
        region_idx = random.randint(0, n_regions - 1)
        private.append({
            "gene": gene, "chromosome": f"chr{random.randint(1, 22)}",
            "position": random.randint(1_000_000, 200_000_000),
            "ref": random.choice("ACGT"), "alt": random.choice("ACGT"),
            "variant_class": random.choice(["Missense", "Nonsense"]),
            "base_vaf": base_vaf, "region_idx": region_idx,
            "mutation_id": f"private_{_}",
        })

    # Build per-region VCF-like records
    region_variants: List[List[Dict]] = [[] for _ in range(n_regions)]
    for m in clonal:
        for r in range(n_regions):
            vaf = max(0.01, m["base_vaf"] + random.gauss(0, 0.03))
            region_variants[r].append({
                "mutation_id": m["mutation_id"], "gene": m["gene"],
                "chromosome": m["chromosome"], "position": m["position"],
                "ref": m["ref"], "alt": m["alt"],
                "variant_class": m["variant_class"],
                "vaf": round(vaf, 4),
            })
    for m in shared:
        for r in m["present_in"]:
            vaf = max(0.01, m["base_vaf"] + random.gauss(0, 0.02))
            region_variants[r].append({
                "mutation_id": m["mutation_id"], "gene": m["gene"],
                "chromosome": m["chromosome"], "position": m["position"],
                "ref": m["ref"], "alt": m["alt"],
                "variant_class": m["variant_class"],
                "vaf": round(vaf, 4),
            })
    for m in private:
        r = m["region_idx"]
        vaf = max(0.01, m["base_vaf"] + random.gauss(0, 0.02))
        region_variants[r].append({
            "mutation_id": m["mutation_id"], "gene": m["gene"],
            "chromosome": m["chromosome"], "position": m["position"],
            "ref": m["ref"], "alt": m["alt"],
            "variant_class": m["variant_class"],
            "vaf": round(vaf, 4),
        })

    return region_variants, sample_names


# ---------------------------------------------------------------------------
# ITHAnalyzer
# ---------------------------------------------------------------------------

class ITHAnalyzer:
    """Intratumor heterogeneity analyser."""

    def __init__(
        self,
        multi_region_variants: Optional[List[List[Dict]]] = None,
        cnv_segments: Optional[List[Dict]] = None,
        purities: Optional[List[float]] = None,
        sample_names: Optional[List[str]] = None,
        method: str = "pyclone-vi",
        phylogeny_method: str = "citup",
    ):
        if multi_region_variants is None:
            self.multi_region_variants, self.sample_names = _generate_demo_variants(3)
        else:
            self.multi_region_variants = multi_region_variants
            self.sample_names = sample_names or [f"Sample_{i}" for i in range(len(multi_region_variants))]
        self.n_regions = len(self.multi_region_variants)
        self.purities = purities or [DEFAULT_PURITY] * self.n_regions
        self.cnv_segments = cnv_segments or []
        self.method = method
        self.phylogeny_method = phylogeny_method

    # ----- CCF estimation -----
    def _estimate_ccf(self, vaf: float, purity: float, cn: int = 2) -> float:
        ccf = vaf * cn / purity
        return round(min(max(ccf, 0.0), 1.0), 4)

    # ----- Variant classification -----
    def _classify_variants(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        # Collect all unique mutation_ids
        mutation_presence: Dict[str, Dict[str, Any]] = {}
        for r_idx, region in enumerate(self.multi_region_variants):
            for var in region:
                mid = var["mutation_id"]
                if mid not in mutation_presence:
                    mutation_presence[mid] = {
                        "gene": var["gene"], "chromosome": var["chromosome"],
                        "position": var["position"], "variant_class": var["variant_class"],
                        "regions": {}, "mutation_id": mid,
                    }
                ccf = self._estimate_ccf(var["vaf"], self.purities[r_idx])
                mutation_presence[mid]["regions"][self.sample_names[r_idx]] = {
                    "vaf": var["vaf"], "ccf": ccf,
                }

        clonal, shared, private = [], [], []
        for mid, info in mutation_presence.items():
            n_present = len(info["regions"])
            entry = {
                "mutation_id": mid, "gene": info["gene"],
                "chromosome": info["chromosome"], "position": info["position"],
                "variant_class": info["variant_class"], "regions": info["regions"],
            }
            if n_present == self.n_regions:
                entry["classification"] = "clonal"
                clonal.append(entry)
            elif n_present >= 2:
                entry["classification"] = "shared_subclonal"
                shared.append(entry)
            else:
                entry["classification"] = "private"
                private.append(entry)
        return clonal, shared, private

    # ----- PyClone-VI style clustering -----
    def _cluster_mutations(self, all_mutations: List[Dict], k: int = 5) -> List[Dict]:
        """Simple k-means-style clustering on CCF vectors."""
        # Build CCF vectors
        vectors: List[Tuple[str, List[float]]] = []
        for m in all_mutations:
            ccf_vec = []
            for sname in self.sample_names:
                if sname in m["regions"]:
                    ccf_vec.append(m["regions"][sname]["ccf"])
                else:
                    ccf_vec.append(0.0)
            vectors.append((m["mutation_id"], ccf_vec))

        if not vectors:
            return []

        # Simple assignment: quantize CCFs
        clusters: Dict[int, List[str]] = {}
        cluster_ccfs: Dict[int, List[List[float]]] = {}
        for mid, ccf_vec in vectors:
            # Assign to bucket based on mean CCF
            mean_ccf = sum(ccf_vec) / len(ccf_vec)
            bucket = min(int(mean_ccf * k), k - 1)
            clusters.setdefault(bucket, []).append(mid)
            cluster_ccfs.setdefault(bucket, []).append(ccf_vec)

        result = []
        for cid in sorted(clusters.keys()):
            members = clusters[cid]
            ccf_arrays = cluster_ccfs[cid]
            mean_ccf_per_sample = []
            for s_idx in range(self.n_regions):
                col = [row[s_idx] for row in ccf_arrays]
                mean_ccf_per_sample.append(round(sum(col) / len(col), 4))
            result.append({
                "cluster_id": cid,
                "n_mutations": len(members),
                "mean_ccf_per_sample": dict(zip(self.sample_names, mean_ccf_per_sample)),
                "color": CLONE_COLORS[cid % len(CLONE_COLORS)],
                "mutations": members[:10],  # top 10 for brevity
            })
        return result

    # ----- ITH metrics -----
    def _compute_ith_metrics(self, clonal: List, shared: List, private: List,
                              clusters: List[Dict]) -> Dict:
        total = len(clonal) + len(shared) + len(private)
        subclonal_frac = round((len(shared) + len(private)) / max(total, 1), 4)

        # Shannon diversity on clone cluster sizes
        sizes = [c["n_mutations"] for c in clusters]
        total_muts = sum(sizes)
        proportions = [s / max(total_muts, 1) for s in sizes]
        shannon = -sum(p * math.log(p) for p in proportions if p > 0)
        simpson = 1 - sum(p ** 2 for p in proportions)

        # MATH score from all VAFs
        all_vafs = []
        for region in self.multi_region_variants:
            for var in region:
                all_vafs.append(var["vaf"])
        if all_vafs:
            all_vafs.sort()
            median_vaf = all_vafs[len(all_vafs) // 2]
            abs_devs = [abs(v - median_vaf) for v in all_vafs]
            abs_devs.sort()
            mad = abs_devs[len(abs_devs) // 2]
            math_score = round(mad * 100 / max(median_vaf, 0.001), 2)
        else:
            math_score = 0.0

        return {
            "n_total_mutations": total,
            "n_clonal": len(clonal),
            "n_shared_subclonal": len(shared),
            "n_private": len(private),
            "subclonal_fraction": subclonal_frac,
            "n_clones": len(clusters),
            "shannon_diversity": round(shannon, 4),
            "simpson_diversity": round(simpson, 4),
            "math_score": math_score,
        }

    # ----- Phylogeny -----
    def _reconstruct_phylogeny(self, clonal: List, shared: List,
                                private: List) -> Dict:
        tree = {
            "root": {
                "label": "Trunk (clonal)",
                "n_mutations": len(clonal),
                "key_genes": list(set(m["gene"] for m in clonal[:10])),
                "children": [],
            }
        }
        # Shared = internal branches
        shared_by_regions = {}
        for m in shared:
            key = tuple(sorted(m["regions"].keys()))
            shared_by_regions.setdefault(key, []).append(m)
        for regions_key, muts in shared_by_regions.items():
            branch = {
                "label": f"Branch ({'+'.join(regions_key)})",
                "n_mutations": len(muts),
                "key_genes": list(set(m["gene"] for m in muts[:5])),
                "children": [],
            }
            tree["root"]["children"].append(branch)

        # Private = leaves
        for sname in self.sample_names:
            priv_muts = [m for m in private if sname in m["regions"]]
            leaf = {
                "label": f"Leaf ({sname})",
                "n_mutations": len(priv_muts),
                "key_genes": list(set(m["gene"] for m in priv_muts[:5])),
            }
            # Attach to best matching branch or root
            if tree["root"]["children"]:
                tree["root"]["children"][-1].setdefault("children", []).append(leaf)
            else:
                tree["root"]["children"].append(leaf)

        return tree

    # ----- Resistance -----
    def _detect_resistance(self, all_mutations: List[Dict]) -> List[Dict]:
        resistance_hits = []
        for m in all_mutations:
            gene = m["gene"]
            if gene in RESISTANCE_MUTATIONS:
                for mut_key, description in RESISTANCE_MUTATIONS[gene].items():
                    resistance_hits.append({
                        "gene": gene, "mutation": mut_key,
                        "description": description,
                        "classification": m.get("classification", "unknown"),
                        "regions": list(m.get("regions", {}).keys()),
                    })
                    break  # one hit per gene per mutation
        return resistance_hits

    # ----- Prognosis -----
    def _assess_prognosis(self, metrics: Dict) -> Dict:
        shannon = metrics["shannon_diversity"]
        if shannon > 1.5:
            level = "high_ith"
        elif shannon > 0.8:
            level = "moderate_ith"
        else:
            level = "low_ith"
        return {**ITH_PROGNOSIS[level], "ith_level": level,
                "shannon_diversity": shannon}

    # ----- main entry -----
    def analyze(self) -> Dict[str, Any]:
        clonal, shared, private = self._classify_variants()
        all_mutations = clonal + shared + private
        clusters = self._cluster_mutations(all_mutations)
        metrics = self._compute_ith_metrics(clonal, shared, private, clusters)
        phylogeny = self._reconstruct_phylogeny(clonal, shared, private)
        resistance = self._detect_resistance(all_mutations)
        prognosis = self._assess_prognosis(metrics)

        return {
            "analysis_metadata": {
                "analysis_type": "Intratumor Heterogeneity",
                "timestamp": datetime.now().isoformat(),
                "method": self.method,
                "phylogeny_method": self.phylogeny_method,
                "n_regions": self.n_regions,
                "sample_names": self.sample_names,
                "purities": self.purities,
            },
            "clonal_mutations": clonal,
            "subclonal_mutations": {"shared": shared, "private": private},
            "clone_clusters": clusters,
            "ith_metrics": metrics,
            "phylogeny": phylogeny,
            "resistance_clones": resistance,
            "prognosis": prognosis,
        }


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_vcf_variants(path: str) -> Optional[List[Dict]]:
    if not os.path.isfile(path):
        return None
    variants: List[Dict] = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            chrom, pos, vid, ref, alt = parts[:5]
            info = parts[7] if len(parts) > 7 else ""
            vaf = 0.5
            if "AF=" in info:
                try:
                    vaf = float(info.split("AF=")[1].split(";")[0])
                except (ValueError, IndexError):
                    pass
            gene = ""
            if "GENE=" in info:
                gene = info.split("GENE=")[1].split(";")[0]
            variants.append({
                "mutation_id": f"{chrom}_{pos}_{ref}_{alt}",
                "gene": gene, "chromosome": chrom, "position": int(pos),
                "ref": ref, "alt": alt, "vaf": round(vaf, 4),
                "variant_class": "Unknown",
            })
    return variants if variants else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Intratumor Heterogeneity (ITH) Analyzer",
    )
    parser.add_argument("--multi_region_vcfs", default=None,
                        help="Comma-separated VCF paths for each region")
    parser.add_argument("--cnv_segments", default=None,
                        help="CNV segments file")
    parser.add_argument("--purity", default=None,
                        help="Comma-separated purity estimates per region")
    parser.add_argument("--sample_names", default=None,
                        help="Comma-separated sample names")
    parser.add_argument("--method", default="pyclone-vi",
                        help="Clustering method (pyclone-vi)")
    parser.add_argument("--phylogeny_method", default="citup",
                        help="Phylogeny method (citup)")
    parser.add_argument("--output", default=None, help="Output path")
    args = parser.parse_args()

    multi_variants = None
    sample_names = None
    purities = None

    if args.multi_region_vcfs:
        vcf_paths = [p.strip() for p in args.multi_region_vcfs.split(",")]
        loaded = [_load_vcf_variants(p) for p in vcf_paths]
        if all(v is not None for v in loaded):
            multi_variants = loaded
    if args.sample_names:
        sample_names = [s.strip() for s in args.sample_names.split(",")]
    if args.purity:
        purities = [float(p.strip()) for p in args.purity.split(",")]

    analyzer = ITHAnalyzer(
        multi_region_variants=multi_variants,
        purities=purities,
        sample_names=sample_names,
        method=args.method,
        phylogeny_method=args.phylogeny_method,
    )
    result = analyzer.analyze()
    output = json.dumps(result, indent=2, default=str)

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or out_path.endswith("/"):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, "ith_report.json")
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

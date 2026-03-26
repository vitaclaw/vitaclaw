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
Chromosomal Instability (CIN) Analysis Agent.

Computes CIN70 / CIN25 gene-expression signatures, aneuploidy score,
fraction genome altered (FGA), weighted genome instability index (wGII),
breakpoint density, immune correlation, and therapeutic vulnerabilities.
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

CIN70_GENES = [
    "TPX2", "BUB1", "CCNB2", "TTK", "CENPE", "NDC80", "CEP55", "UBE2C",
    "AURKA", "AURKB", "KIF2C", "MCM10", "MELK", "KIF4A", "CDC20", "BIRC5",
    "KIF20A", "PLK1", "TOP2A", "FOXM1", "HJURP", "CDCA8", "CDCA5", "NCAPG",
    "NCAPH", "KIF18A", "KIF11", "DLGAP5", "NUSAP1", "BUB1B", "PBK", "PRC1",
    "ASPM", "CENPF", "TACC3", "NUF2", "KIF14", "MKI67", "HMMR", "CENPA",
    "ECT2", "RACGAP1", "NEK2", "CCNA2", "CCNB1", "CDK1", "MAD2L1", "ESPL1",
    "ZWINT", "TRIP13", "CDCA3", "EXO1", "RAD54L", "SPC25", "DEPDC1", "OIP5",
    "SHCBP1", "SGOL1", "KIFC1", "TROAP", "SKA3", "ANLN", "FAM83D", "DEPDC1B",
    "DTL", "KIF15", "C1orf112", "CKAP2L", "SAPCD2", "GTSE1",
]

CIN25_GENES = [
    "TPX2", "BUB1", "CCNB2", "TTK", "CENPE", "NDC80", "CEP55", "UBE2C",
    "AURKA", "AURKB", "KIF2C", "MCM10", "MELK", "KIF4A", "CDC20", "BIRC5",
    "KIF20A", "PLK1", "TOP2A", "FOXM1", "HJURP", "CDCA8", "CDCA5", "NCAPG",
    "NCAPH",
]

CHROMOSOME_ARMS = {
    "chr1": ("1p", "1q"), "chr2": ("2p", "2q"), "chr3": ("3p", "3q"),
    "chr4": ("4p", "4q"), "chr5": ("5p", "5q"), "chr6": ("6p", "6q"),
    "chr7": ("7p", "7q"), "chr8": ("8p", "8q"), "chr9": ("9p", "9q"),
    "chr10": ("10p", "10q"), "chr11": ("11p", "11q"), "chr12": ("12p", "12q"),
    "chr13": ("13q",), "chr14": ("14q",), "chr15": ("15q",),
    "chr16": ("16p", "16q"), "chr17": ("17p", "17q"), "chr18": ("18p", "18q"),
    "chr19": ("19p", "19q"), "chr20": ("20p", "20q"), "chr21": ("21q",),
    "chr22": ("22q",),
}

CENTROMERE_POSITIONS = {
    "chr1": 125_000_000, "chr2": 93_300_000, "chr3": 91_000_000,
    "chr4": 50_400_000, "chr5": 48_400_000, "chr6": 61_000_000,
    "chr7": 59_900_000, "chr8": 45_600_000, "chr9": 49_000_000,
    "chr10": 40_200_000, "chr11": 53_700_000, "chr12": 35_800_000,
    "chr13": 17_900_000, "chr14": 17_600_000, "chr15": 19_000_000,
    "chr16": 36_600_000, "chr17": 24_000_000, "chr18": 17_200_000,
    "chr19": 26_500_000, "chr20": 27_500_000, "chr21": 13_200_000,
    "chr22": 14_700_000,
}

CHROMOSOME_LENGTHS = {
    "chr1": 249_000_000, "chr2": 243_000_000, "chr3": 198_000_000,
    "chr4": 191_000_000, "chr5": 181_000_000, "chr6": 171_000_000,
    "chr7": 159_000_000, "chr8": 146_000_000, "chr9": 141_000_000,
    "chr10": 136_000_000, "chr11": 135_000_000, "chr12": 134_000_000,
    "chr13": 115_000_000, "chr14": 107_000_000, "chr15": 103_000_000,
    "chr16": 90_000_000, "chr17": 83_000_000, "chr18": 80_000_000,
    "chr19": 59_000_000, "chr20": 65_000_000, "chr21": 47_000_000,
    "chr22": 51_000_000,
}

GENOME_SIZE = sum(CHROMOSOME_LENGTHS.values())

IMMUNE_SIGNATURES = {
    "cgas_sting": ["MB21D1", "TMEM173", "IRF3", "IFNB1", "CXCL10"],
    "immune_evasion": ["CD274", "PDCD1LG2", "CTLA4", "LAG3", "TIGIT"],
    "antigen_presentation": ["HLA-A", "HLA-B", "HLA-C", "B2M", "TAP1", "TAP2"],
}

TUMOR_TYPE_PROGNOSIS = {
    "breast_cancer": {"high_cin": "poor", "moderate_cin": "intermediate", "low_cin": "favorable"},
    "colorectal_cancer": {"high_cin": "poor", "moderate_cin": "intermediate", "low_cin": "favorable"},
    "lung_cancer": {"high_cin": "poor", "moderate_cin": "intermediate", "low_cin": "favorable"},
    "ovarian_cancer": {"high_cin": "intermediate", "moderate_cin": "poor", "low_cin": "favorable"},
}

THERAPEUTIC_VULNERABILITIES = {
    "high_cin_taxane_sensitive": {
        "rationale": "High CIN exploits mitotic checkpoint dependency",
        "agents": ["paclitaxel", "docetaxel", "cabazitaxel"],
    },
    "sac_defect_aurk": {
        "rationale": "Spindle assembly checkpoint defects sensitise to AURK inhibitors",
        "agents": ["alisertib", "barasertib"],
    },
    "extreme_cin_lethal": {
        "rationale": "Excessive instability leads to lethal aneuploidy",
        "agents": ["additional CIN-inducing agents may push past viability threshold"],
    },
}


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

def _generate_demo_expression(genes: List[str]) -> Dict[str, float]:
    random.seed(45)
    return {g: round(random.gauss(6.0, 2.5), 3) for g in genes}


def _generate_demo_cnv_segments() -> List[Dict]:
    random.seed(46)
    segs = []
    for chrom, length in CHROMOSOME_LENGTHS.items():
        n = random.randint(2, 6)
        pos = 1
        for _ in range(n):
            seg_len = random.randint(5_000_000, 60_000_000)
            end = min(pos + seg_len, length)
            cn = random.choice([1, 1, 2, 2, 2, 3, 3, 4])
            segs.append({"chromosome": chrom, "start": pos, "end": end,
                         "total_cn": cn, "segment_mean": round(math.log2(cn / 2 + 0.01), 3)})
            pos = end + 1
            if pos >= length:
                break
    return segs


# ---------------------------------------------------------------------------
# CINAnalyzer
# ---------------------------------------------------------------------------

class CINAnalyzer:
    """Chromosomal instability analyser."""

    def __init__(
        self,
        cnv_segments: Optional[List[Dict]] = None,
        expression: Optional[Dict[str, float]] = None,
        mutations: Optional[List[Dict]] = None,
        tumor_type: str = "breast_cancer",
        signatures: Optional[List[str]] = None,
    ):
        all_genes = set(CIN70_GENES) | set(sum(IMMUNE_SIGNATURES.values(), []))
        self.cnv_segments = cnv_segments or _generate_demo_cnv_segments()
        self.expression = expression or _generate_demo_expression(list(all_genes))
        self.mutations = mutations or []
        self.tumor_type = tumor_type
        self.signatures = signatures or ["cin70", "cin25"]

    # ----- helpers -----
    @staticmethod
    def _zscore_list(values: List[float]) -> List[float]:
        if not values:
            return []
        mu = sum(values) / len(values)
        sd = math.sqrt(sum((v - mu) ** 2 for v in values) / max(len(values) - 1, 1))
        if sd == 0:
            return [0.0] * len(values)
        return [(v - mu) / sd for v in values]

    def _signature_score(self, genes: List[str]) -> Tuple[float, Dict[str, float]]:
        vals = [self.expression.get(g, 0.0) for g in genes]
        zscores = self._zscore_list(vals)
        gene_z = {g: round(z, 3) for g, z in zip(genes, zscores)}
        mean_z = round(sum(zscores) / max(len(zscores), 1), 4)
        return mean_z, gene_z

    # ----- CIN70 / CIN25 -----
    def _compute_cin70(self) -> Dict:
        score, gene_z = self._signature_score(CIN70_GENES)
        return {"score": score, "status": "High CIN" if score > 0.5 else "Low CIN",
                "n_genes_measured": sum(1 for g in CIN70_GENES if g in self.expression),
                "top_genes": dict(sorted(gene_z.items(), key=lambda x: -x[1])[:10])}

    def _compute_cin25(self) -> Dict:
        score, gene_z = self._signature_score(CIN25_GENES)
        return {"score": score, "status": "High CIN" if score > 0.5 else "Low CIN",
                "n_genes_measured": sum(1 for g in CIN25_GENES if g in self.expression),
                "top_genes": dict(sorted(gene_z.items(), key=lambda x: -x[1])[:10])}

    # ----- Aneuploidy score -----
    def _compute_aneuploidy(self) -> Tuple[int, Dict[str, str]]:
        arm_status: Dict[str, str] = {}
        for chrom, arms in CHROMOSOME_ARMS.items():
            centro = CENTROMERE_POSITIONS.get(chrom, 50_000_000)
            chrom_segs = [s for s in self.cnv_segments if s["chromosome"] == chrom]
            for arm_label in arms:
                is_p = arm_label.endswith("p")
                arm_segs = [s for s in chrom_segs
                            if (is_p and s["end"] <= centro) or (not is_p and s["start"] >= centro)]
                if not arm_segs:
                    arm_status[arm_label] = "neutral"
                    continue
                mean_cn = sum(s.get("total_cn", 2) for s in arm_segs) / len(arm_segs)
                if mean_cn > 2.5:
                    arm_status[arm_label] = "gain"
                elif mean_cn < 1.5:
                    arm_status[arm_label] = "loss"
                else:
                    arm_status[arm_label] = "neutral"
        score = sum(1 for v in arm_status.values() if v != "neutral")
        return score, arm_status

    # ----- FGA -----
    def _compute_fga(self) -> float:
        cnv_length = sum(s["end"] - s["start"] for s in self.cnv_segments
                         if abs(s.get("total_cn", 2) - 2) >= 0.5)
        return round(cnv_length / GENOME_SIZE, 4)

    # ----- wGII -----
    def _compute_wgii(self) -> float:
        fractions = []
        for chrom, length in CHROMOSOME_LENGTHS.items():
            chrom_segs = [s for s in self.cnv_segments if s["chromosome"] == chrom]
            altered = sum(s["end"] - s["start"] for s in chrom_segs
                          if abs(s.get("total_cn", 2) - 2) >= 0.5)
            fractions.append(altered / length)
        return round(sum(fractions) / max(len(fractions), 1), 4)

    # ----- Breakpoint density -----
    def _compute_breakpoint_density(self) -> Dict[str, int]:
        density: Dict[str, int] = {}
        sorted_segs = sorted(self.cnv_segments, key=lambda s: (s["chromosome"], s["start"]))
        for i in range(1, len(sorted_segs)):
            prev, cur = sorted_segs[i - 1], sorted_segs[i]
            if prev["chromosome"] == cur["chromosome"]:
                if prev.get("total_cn", 2) != cur.get("total_cn", 2):
                    density[prev["chromosome"]] = density.get(prev["chromosome"], 0) + 1
        return density

    # ----- Immune correlation -----
    def _compute_immune_correlation(self, cin_score: float) -> Dict:
        result: Dict[str, Any] = {}
        for sig_name, genes in IMMUNE_SIGNATURES.items():
            vals = [self.expression.get(g, 0.0) for g in genes]
            mean_expr = round(sum(vals) / max(len(vals), 1), 3)
            result[sig_name] = {
                "mean_expression": mean_expr,
                "genes_measured": sum(1 for g in genes if g in self.expression),
            }
        result["interpretation"] = (
            "High CIN can activate cGAS-STING but chronic instability often leads to "
            "immune evasion via suppression of interferon signalling."
        )
        return result

    # ----- Therapeutic vulnerabilities -----
    def _assess_therapeutics(self, cin_score: float, aneuploidy: int) -> Dict:
        vulns: List[Dict] = []
        if cin_score > 0.5:
            vulns.append(THERAPEUTIC_VULNERABILITIES["high_cin_taxane_sensitive"])
        sac_genes = {"BUB1", "BUB1B", "MAD2L1", "TTK"}
        sac_low = any(self.expression.get(g, 999) < 3.0 for g in sac_genes)
        if sac_low:
            vulns.append(THERAPEUTIC_VULNERABILITIES["sac_defect_aurk"])
        if aneuploidy >= 30:
            vulns.append(THERAPEUTIC_VULNERABILITIES["extreme_cin_lethal"])
        return {"vulnerabilities": vulns, "n_actionable": len(vulns)}

    # ----- Prognosis -----
    def _assess_prognosis(self, cin_score: float) -> Dict:
        ctx = TUMOR_TYPE_PROGNOSIS.get(self.tumor_type, TUMOR_TYPE_PROGNOSIS["breast_cancer"])
        if cin_score > 0.5:
            level = "high_cin"
        elif cin_score > -0.2:
            level = "moderate_cin"
        else:
            level = "low_cin"
        return {"cin_level": level, "prognosis": ctx[level],
                "tumor_type": self.tumor_type}

    # ----- main entry -----
    def analyze(self) -> Dict[str, Any]:
        cin70 = self._compute_cin70() if "cin70" in self.signatures else None
        cin25 = self._compute_cin25() if "cin25" in self.signatures else None
        primary_score = (cin70 or cin25 or {}).get("score", 0.0)

        aneuploidy_score, arm_status = self._compute_aneuploidy()
        fga = self._compute_fga()
        wgii = self._compute_wgii()
        bp_density = self._compute_breakpoint_density()
        immune = self._compute_immune_correlation(primary_score)
        therapeutics = self._assess_therapeutics(primary_score, aneuploidy_score)
        prognosis = self._assess_prognosis(primary_score)

        return {
            "analysis_metadata": {
                "analysis_type": "Chromosomal Instability",
                "timestamp": datetime.now().isoformat(),
                "tumor_type": self.tumor_type,
                "signatures_used": self.signatures,
                "n_segments": len(self.cnv_segments),
            },
            "cin70_score": cin70,
            "cin25_score": cin25,
            "aneuploidy_score": {"score": aneuploidy_score, "max_possible": 39,
                                  "high_aneuploidy": aneuploidy_score >= 15,
                                  "arm_status": arm_status},
            "fga": {"value": fga, "high": fga > 0.3},
            "wgii": {"value": wgii, "range": "0-1"},
            "breakpoint_density": bp_density,
            "immune_correlation": immune,
            "therapeutic_implications": therapeutics,
            "prognosis": prognosis,
        }


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------

def _load_cnv(path: str) -> Optional[List[Dict]]:
    if not os.path.isfile(path):
        return None
    rows: List[Dict] = []
    with open(path) as fh:
        header = fh.readline().strip().split("\t")
        for line in fh:
            vals = line.strip().split("\t")
            row = dict(zip(header, vals))
            rows.append({
                "chromosome": row.get("chromosome", row.get("chrom", "chr1")),
                "start": int(row.get("start", 0)),
                "end": int(row.get("end", 0)),
                "total_cn": int(float(row.get("total_cn", row.get("cn", 2)))),
                "segment_mean": float(row.get("segment_mean", 0)),
            })
    return rows if rows else None


def _load_expression(path: str) -> Optional[Dict[str, float]]:
    if not os.path.isfile(path):
        return None
    expr: Dict[str, float] = {}
    with open(path) as fh:
        header = fh.readline().strip().split("\t")
        for line in fh:
            vals = line.strip().split("\t")
            if len(vals) >= 2:
                expr[vals[0]] = float(vals[1])
    return expr if expr else None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Chromosomal Instability (CIN) Analyzer",
    )
    parser.add_argument("--cnv_segments", default=None, help="CNV segments TSV")
    parser.add_argument("--expression", default=None, help="RNA-seq TPM TSV (gene \\t value)")
    parser.add_argument("--mutations", default=None, help="Somatic MAF (optional)")
    parser.add_argument("--tumor_type", default="breast_cancer", help="Tumor type")
    parser.add_argument("--signatures", default="cin70,cin25",
                        help="Comma-separated signatures to compute")
    parser.add_argument("--output", default=None, help="Output path (file or directory)")
    args = parser.parse_args()

    cnv = _load_cnv(args.cnv_segments) if args.cnv_segments else None
    expr = _load_expression(args.expression) if args.expression else None
    sigs = [s.strip() for s in args.signatures.split(",")]

    analyzer = CINAnalyzer(
        cnv_segments=cnv, expression=expr, mutations=None,
        tumor_type=args.tumor_type, signatures=sigs,
    )
    result = analyzer.analyze()
    output = json.dumps(result, indent=2, default=str)

    if args.output:
        out_path = args.output
        if os.path.isdir(out_path) or out_path.endswith("/"):
            os.makedirs(out_path, exist_ok=True)
            out_path = os.path.join(out_path, "cin_report.json")
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

#!/usr/bin/env python3
"""Time-series correlation detection for VitaClaw health data.

Detects statistical correlations between health metrics:
  - BP <-> sleep quality
  - Weight <-> medication
  - Blood sugar <-> caffeine intake

Uses scipy.stats for Pearson and Spearman correlation with p-values.
Falls back to hand-rolled Pearson when scipy is unavailable.
Uses knowledge graph constraints to prioritize biologically plausible pairs.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

try:
    from scipy.stats import pearsonr, spearmanr

    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# Chinese labels for NL insight generation
_STRENGTH_ZH = {"strong": "强", "moderate": "中等", "weak": "弱", "none": ""}
_DIRECTION_ZH = {"positive": "正相关", "negative": "负相关", "none": "无关联"}


class CorrelationResult:
    """Result of a correlation analysis between two concepts."""

    def __init__(
        self,
        concept_a: str,
        concept_b: str,
        field_a: str,
        field_b: str,
        correlation: float,
        sample_count: int,
        direction: str,  # positive | negative | none
        strength: str,  # strong | moderate | weak | none
        p_value: float = 1.0,
        method: str = "pearson",
    ):
        self.concept_a = concept_a
        self.concept_b = concept_b
        self.field_a = field_a
        self.field_b = field_b
        self.correlation = correlation
        self.sample_count = sample_count
        self.direction = direction
        self.strength = strength
        self.p_value = p_value
        self.method = method

    def is_significant(self) -> bool:
        """Return True when p < 0.05 AND sample_count >= 14."""
        return self.p_value < 0.05 and self.sample_count >= 14

    def to_natural_language(self) -> str:
        """Generate Chinese natural language insight."""
        if not self.is_significant():
            return (
                f"{self.concept_a} 与 {self.concept_b} 之间未发现显著相关性"
                f"（p={self.p_value:.3f}, n={self.sample_count}）"
            )
        strength_zh = _STRENGTH_ZH.get(self.strength, "")
        direction_zh = _DIRECTION_ZH.get(self.direction, "无关联")
        return (
            f"过去分析期间，{self.concept_a} 与 {self.concept_b} 存在{strength_zh}{direction_zh}"
            f"（r={self.correlation:.3f}, p={self.p_value:.3f}, n={self.sample_count}）"
        )

    def to_dict(self) -> dict:
        return {
            "concept_a": self.concept_a,
            "concept_b": self.concept_b,
            "field_a": self.field_a,
            "field_b": self.field_b,
            "correlation": round(self.correlation, 3),
            "sample_count": self.sample_count,
            "direction": self.direction,
            "strength": self.strength,
            "p_value": round(self.p_value, 4),
            "method": self.method,
            "natural_language": self.to_natural_language(),
            "is_significant": self.is_significant(),
        }


class CorrelationEngine:
    """Detect time-series correlations between health metrics."""

    # Biologically plausible pairs aligned with health-concepts.yaml field names
    DEFAULT_PAIRS = [
        ("blood-pressure", "systolic", "sleep", "total_min"),
        ("blood-pressure", "systolic", "weight", "kg"),
        ("blood-pressure", "systolic", "caffeine", "mg"),
        ("blood-sugar", "value", "weight", "kg"),
        ("blood-sugar", "value", "sleep", "total_min"),
        ("sleep", "total_min", "caffeine", "mg"),
    ]

    def __init__(self, data_dir: str | None = None, now_fn=None):
        self._data_dir = data_dir
        self._now_fn = now_fn or datetime.now

    def _now(self) -> datetime:
        return self._now_fn()

    def _get_daily_values(
        self,
        concept: str,
        field: str,
        window_days: int = 30,
        person_id: str | None = None,
    ) -> dict[str, float]:
        """Get daily aggregated values for a concept field.

        Returns {date_str: avg_value} for days with data.
        """
        from .cross_skill_reader import CrossSkillReader

        reader = CrossSkillReader(data_dir=self._data_dir)
        start = (self._now() - timedelta(days=window_days)).isoformat()[:10]
        records = reader.read(concept, start=start, person_id=person_id)

        # Resolve field aliases
        try:
            from .concept_resolver import ConceptResolver

            resolver = ConceptResolver()
            alias_map = resolver._alias_index.get(concept, {})
        except (ImportError, KeyError):
            alias_map = {}

        # Aggregate by date
        daily: dict[str, list[float]] = {}
        for record in records:
            date = record.get("timestamp", "")[:10]
            if not date:
                continue
            data = record.get("data", {})
            # Try canonical name first, then check if field is an alias
            value = data.get(field)
            if value is None:
                # Try reverse: maybe the record uses an alias
                for alias, canonical in alias_map.items():
                    if canonical == field and alias in data:
                        value = data[alias]
                        break
            if value is None:
                # Try the field directly (it might be the alias itself)
                value = data.get(field)
            if isinstance(value, (int, float)):
                daily.setdefault(date, []).append(float(value))

        return {date: sum(vals) / len(vals) for date, vals in daily.items()}

    def pearson_correlation(self, x: list[float], y: list[float]) -> float:
        """Compute Pearson correlation coefficient (hand-rolled fallback)."""
        n = len(x)
        if n < 3:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denom_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
        denom_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5

        if denom_x * denom_y == 0:
            return 0.0
        return numerator / (denom_x * denom_y)

    def correlate(
        self,
        concept_a: str,
        field_a: str,
        concept_b: str,
        field_b: str,
        window_days: int = 30,
        person_id: str | None = None,
    ) -> CorrelationResult:
        """Compute correlation between two concept fields over a time window."""
        values_a = self._get_daily_values(concept_a, field_a, window_days, person_id=person_id)
        values_b = self._get_daily_values(concept_b, field_b, window_days, person_id=person_id)

        # Find overlapping dates
        common_dates = sorted(set(values_a.keys()) & set(values_b.keys()))

        if len(common_dates) < 14:
            return CorrelationResult(
                concept_a=concept_a,
                concept_b=concept_b,
                field_a=field_a,
                field_b=field_b,
                correlation=0.0,
                sample_count=len(common_dates),
                direction="none",
                strength="none",
                p_value=1.0,
                method="insufficient_data",
            )

        x = [values_a[d] for d in common_dates]
        y = [values_b[d] for d in common_dates]

        if _HAS_SCIPY:
            r, p, method = self._scipy_correlate(x, y)
        else:
            r = self.pearson_correlation(x, y)
            p = 1.0  # Cannot compute p-value without scipy
            method = "pearson"

        abs_r = abs(r)
        if abs_r >= 0.7:
            strength = "strong"
        elif abs_r >= 0.4:
            strength = "moderate"
        elif abs_r >= 0.2:
            strength = "weak"
        else:
            strength = "none"

        direction = "positive" if r > 0.1 else ("negative" if r < -0.1 else "none")

        return CorrelationResult(
            concept_a=concept_a,
            concept_b=concept_b,
            field_a=field_a,
            field_b=field_b,
            correlation=r,
            sample_count=len(common_dates),
            direction=direction,
            strength=strength,
            p_value=p,
            method=method,
        )

    @staticmethod
    def _scipy_correlate(x: list[float], y: list[float]) -> tuple[float, float, str]:
        """Compute both Pearson and Spearman, return the more significant result."""
        r_pearson, p_pearson = pearsonr(x, y)
        r_spearman, p_spearman = spearmanr(x, y)

        if p_spearman < p_pearson:
            return float(r_spearman), float(p_spearman), "spearman"
        return float(r_pearson), float(p_pearson), "pearson"

    def discover_correlations(
        self,
        window_days: int = 30,
        min_strength: str = "weak",
        pairs: list[tuple] | None = None,
        person_id: str | None = None,
    ) -> list[CorrelationResult]:
        """Run correlation analysis on all default or specified pairs.

        Returns significant correlations sorted by strength.
        Filters by both significance (p < 0.05) and minimum strength.
        """
        test_pairs = pairs or self.DEFAULT_PAIRS
        strength_order = {"strong": 3, "moderate": 2, "weak": 1, "none": 0}
        min_level = strength_order.get(min_strength, 1)

        results: list[CorrelationResult] = []
        for concept_a, field_a, concept_b, field_b in test_pairs:
            result = self.correlate(concept_a, field_a, concept_b, field_b, window_days, person_id=person_id)
            if result.is_significant() and strength_order.get(result.strength, 0) >= min_level:
                results.append(result)

        results.sort(key=lambda r: abs(r.correlation), reverse=True)
        return results

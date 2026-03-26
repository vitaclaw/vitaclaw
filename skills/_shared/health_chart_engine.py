#!/usr/bin/env python3
"""Shared health metric chart engine for VitaClaw.

Generates clinically contextualized trend charts for blood pressure,
blood glucose, weight, and sleep. Charts include clinical reference bands,
CJK labels, and configurable time ranges.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ── CJK Font Configuration ──────────────────────────────────────

_CJK_FONT_PREFERENCE = [
    "PingFang HK",
    "PingFang SC",
    "Heiti TC",
    "Hiragino Sans GB",
    "Hiragino Sans",
    "STHeiti",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
]


def _configure_cjk_fonts() -> str | None:
    """Detect and configure a CJK font for matplotlib. Call once at module import."""
    import matplotlib.font_manager as fm

    available_fonts = {f.name for f in fm.fontManager.ttflist}
    for font_name in _CJK_FONT_PREFERENCE:
        if font_name in available_fonts:
            existing = plt.rcParams.get("font.sans-serif", [])
            plt.rcParams["font.sans-serif"] = [font_name] + [
                f for f in existing if f != font_name
            ]
            plt.rcParams["axes.unicode_minus"] = False
            return font_name

    print(
        "[WARN] No CJK font found for matplotlib. Chinese labels will not render correctly.",
        file=sys.stderr,
    )
    return None


_configured_cjk_font = _configure_cjk_fonts()


# ── Helpers ──────────────────────────────────────────────────────

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_data_root(data_dir: str | None) -> Path:
    if data_dir:
        return Path(data_dir).expanduser().resolve()
    env_data_dir = os.environ.get("VITACLAW_DATA_DIR")
    if env_data_dir:
        return Path(env_data_dir).expanduser().resolve()
    return _repo_root() / "data"


# ── HealthChartEngine ────────────────────────────────────────────


class HealthChartEngine:
    """Shared chart engine for health metric visualization.

    Generates PNG trend charts with clinical reference bands for
    blood pressure, blood glucose, weight, and sleep.
    """

    DEFAULT_FIGSIZE = (12, 6)
    DEFAULT_DPI = 150

    # Skill-to-store mapping for data access
    _SKILL_MAP = {
        "bp": ("blood-pressure-tracker", "bp"),
        "glucose": ("chronic-condition-monitor", "glucose"),
        "weight": ("chronic-condition-monitor", "weight"),
        "sleep": ("sleep-analyzer", "sleep_session"),
    }

    def __init__(self, data_dir: str | None = None, person_id: str | None = None):
        self.data_dir = data_dir
        self.person_id = person_id
        self._stores: dict[str, object] = {}

    def _store(self, skill_name: str):
        """Get or create a HealthDataStore for a skill."""
        if skill_name not in self._stores:
            from health_data_store import HealthDataStore

            self._stores[skill_name] = HealthDataStore(skill_name, data_dir=self.data_dir)
        return self._stores[skill_name]

    def _query(self, metric: str, start: str, person_id: str | None = None) -> list[dict]:
        """Query records for a metric using direct HealthDataStore access."""
        skill_name, record_type = self._SKILL_MAP[metric]
        return self._store(skill_name).query(record_type, start=start, person_id=person_id)

    @property
    def _pid(self) -> str:
        """Person ID for filenames — 'self' when None (Pitfall 6)."""
        return self.person_id or "self"

    def _start_date(self, days: int) -> str:
        """ISO date string for N days ago."""
        return (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")

    def _chart_path(self, metric: str, days: int, skill_name: str) -> str:
        """Build chart output path: data/{skill}/charts/{metric}_{pid}_{days}d_{date}.png"""
        data_root = _resolve_data_root(self.data_dir)
        charts_dir = data_root / skill_name / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{metric}_{self._pid}_{days}d_{date_str}.png"
        return str(charts_dir / filename)

    # ── Blood Pressure Chart ─────────────────────────────────────

    def generate_blood_pressure_chart(self, days: int = 30) -> str:
        """Generate dual-line BP chart with clinical reference bands.

        Returns file path string, or '' if no data.
        """
        records = self._query("bp", start=self._start_date(days), person_id=self.person_id)

        if not records:
            return ""

        dates = []
        systolic_vals = []
        diastolic_vals = []
        for r in records:
            dates.append(r["timestamp"][:10])
            systolic_vals.append(r["data"].get("systolic", 0))
            diastolic_vals.append(r["data"].get("diastolic", 0))

        n = len(records)
        fig, ax = plt.subplots(figsize=self.DEFAULT_FIGSIZE)

        # Reference bands (D-03)
        ax.axhspan(40, 120, alpha=0.06, color="green", label="正常 (<120)")
        ax.axhspan(120, 130, alpha=0.08, color="gold", label="偏高 (120-129)")
        ax.axhspan(130, 140, alpha=0.08, color="orange", label="1期 (130-139)")
        ax.axhspan(140, 200, alpha=0.08, color="red", label="2期 (>=140)")

        # Data lines
        ax.plot(
            dates, systolic_vals, "o-",
            color="#E74C3C", linewidth=2, markersize=4, label="收缩压",
        )
        ax.plot(
            dates, diastolic_vals, "s-",
            color="#3498DB", linewidth=2, markersize=4, label="舒张压",
        )

        ax.set_title(f"血压趋势 (近{days}天)", fontsize=14)
        ax.set_ylabel("mmHg")
        ax.set_ylim(40, 200)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

        # Subtitle with data point count
        ax.text(
            0.5, 1.02, f"共 {n} 个数据点",
            transform=ax.transAxes, ha="center", fontsize=9, color="gray",
        )

        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()

        path = self._chart_path("bp", days, "blood-pressure-tracker")
        fig.savefig(path, dpi=self.DEFAULT_DPI, bbox_inches="tight")
        plt.close(fig)
        return path

    # ── Blood Glucose Chart ──────────────────────────────────────

    def generate_blood_glucose_chart(self, days: int = 30) -> str:
        """Generate blood glucose line chart with reference bands.

        Returns file path string, or '' if no data.
        """
        records = self._query("glucose", start=self._start_date(days), person_id=self.person_id)

        if not records:
            return ""

        dates = []
        values = []
        for r in records:
            dates.append(r["timestamp"][:10])
            values.append(r["data"].get("value", r["data"].get("glucose", 0)))

        n = len(records)
        fig, ax = plt.subplots(figsize=self.DEFAULT_FIGSIZE)

        # Reference bands (D-03)
        ax.axhspan(2, 3.9, alpha=0.06, color="orange", label="偏低 (<3.9)")
        ax.axhspan(3.9, 6.1, alpha=0.06, color="green", label="正常 (3.9-6.1)")
        ax.axhspan(6.1, 7.0, alpha=0.08, color="gold", label="糖前期 (6.1-7.0)")
        ax.axhspan(7.0, 15, alpha=0.08, color="red", label="偏高 (>7.0)")

        ax.plot(
            dates, values, "o-",
            color="#27AE60", linewidth=2, markersize=5, label="血糖",
        )

        ax.set_title(f"血糖趋势 (近{days}天)", fontsize=14)
        ax.set_ylabel("mmol/L")
        ax.set_ylim(2, 15)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

        ax.text(
            0.5, 1.02, f"共 {n} 个数据点",
            transform=ax.transAxes, ha="center", fontsize=9, color="gray",
        )

        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()

        path = self._chart_path("glucose", days, "chronic-condition-monitor")
        fig.savefig(path, dpi=self.DEFAULT_DPI, bbox_inches="tight")
        plt.close(fig)
        return path

    # ── Weight Chart ─────────────────────────────────────────────

    def generate_weight_chart(self, days: int = 30) -> str:
        """Generate weight line chart with moving average trend line.

        Returns file path string, or '' if no data.
        """
        records = self._query("weight", start=self._start_date(days), person_id=self.person_id)

        if not records:
            return ""

        dates = []
        values = []
        for r in records:
            dates.append(r["timestamp"][:10])
            values.append(r["data"].get("value", r["data"].get("weight", 0)))

        n = len(records)
        fig, ax = plt.subplots(figsize=self.DEFAULT_FIGSIZE)

        ax.plot(
            dates, values, "o-",
            color="#8E44AD", linewidth=1.5, markersize=5, label="体重",
        )

        # Moving average trend line (7-day window)
        if len(values) >= 7:
            import numpy as np

            kernel = np.ones(7) / 7
            ma = np.convolve(values, kernel, mode="valid")
            # Align moving average with dates (offset by half window)
            ma_dates = dates[3 : 3 + len(ma)]
            ax.plot(
                ma_dates, ma, "-",
                color="#E67E22", linewidth=2.5, alpha=0.8, label="7日移动均线",
            )

        ax.set_title(f"体重趋势 (近{days}天)", fontsize=14)
        ax.set_ylabel("kg")

        # Auto y-axis with 10% padding (Pitfall 3)
        if values:
            v_min, v_max = min(values), max(values)
            padding = max((v_max - v_min) * 0.1, 0.5)
            ax.set_ylim(v_min - padding, v_max + padding)

        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)

        ax.text(
            0.5, 1.02, f"共 {n} 个数据点",
            transform=ax.transAxes, ha="center", fontsize=9, color="gray",
        )

        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()

        path = self._chart_path("weight", days, "chronic-condition-monitor")
        fig.savefig(path, dpi=self.DEFAULT_DPI, bbox_inches="tight")
        plt.close(fig)
        return path

    # ── Sleep Chart ──────────────────────────────────────────────

    def generate_sleep_chart(self, days: int = 30) -> str:
        """Generate sleep duration bar chart with recommended range band.

        Returns file path string, or '' if no data.
        """
        records = self._query("sleep", start=self._start_date(days), person_id=self.person_id)

        if not records:
            return ""

        dates = []
        hours = []
        for r in records:
            dates.append(r["timestamp"][:10])
            total_min = r["data"].get("total_min", r["data"].get("duration_min", 0))
            hours.append(total_min / 60.0)

        n = len(records)
        fig, ax = plt.subplots(figsize=self.DEFAULT_FIGSIZE)

        # Reference band: 7-9h recommended range (D-03)
        ax.axhspan(7, 9, alpha=0.10, color="green", label="推荐 (7-9h)")

        # Bar chart
        colors = ["#2ECC71" if 7 <= h <= 9 else "#E74C3C" if h < 6 else "#F39C12" for h in hours]
        ax.bar(dates, hours, color=colors, alpha=0.8, label="睡眠时长")

        ax.set_title(f"睡眠时长 (近{days}天)", fontsize=14)
        ax.set_ylabel("小时")
        ax.set_ylim(0, 14)
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

        ax.text(
            0.5, 1.02, f"共 {n} 个数据点",
            transform=ax.transAxes, ha="center", fontsize=9, color="gray",
        )

        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()

        path = self._chart_path("sleep", days, "sleep-analyzer")
        fig.savefig(path, dpi=self.DEFAULT_DPI, bbox_inches="tight")
        plt.close(fig)
        return path

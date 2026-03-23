#!/usr/bin/env python3
"""补剂管理 — 管理日常补剂方案，跟踪服用记录与依从率，RxNorm 交互检查。"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore
from health_memory import HealthMemoryWriter

# ---------------------------------------------------------------------------
# Frequency mapping: frequency code -> expected doses per day
# ---------------------------------------------------------------------------
FREQUENCY_MAP = {
    "qd": 1,
    "bid": 2,
    "tid": 3,
    "prn": 0,
    "qw": 1 / 7,
    "qod": 0.5,
}

FREQUENCY_LABELS = {
    "qd": "每日1次",
    "bid": "每日2次",
    "tid": "每日3次",
    "prn": "按需",
    "qw": "每周1次",
    "qod": "隔日1次",
}

# ---------------------------------------------------------------------------
# Supplement categories
# ---------------------------------------------------------------------------
CATEGORIES = [
    "vitamin",
    "mineral",
    "amino_acid",
    "herbal",
    "nootropic",
    "omega",
    "probiotic",
    "other",
]

# ---------------------------------------------------------------------------
# Built-in timing knowledge
# ---------------------------------------------------------------------------
TIMING_ADVICE = {
    "VD": {"with_food": True, "best_time": "随餐(早/午)", "reason": "脂溶性，需脂肪辅助吸收"},
    "VD3": {"with_food": True, "best_time": "随餐(早/午)", "reason": "脂溶性，需脂肪辅助吸收"},
    "鱼油": {"with_food": True, "best_time": "随餐", "reason": "脂溶性，餐后吸收率提高3倍"},
    "fish_oil": {"with_food": True, "best_time": "随餐", "reason": "脂溶性，餐后吸收率提高3倍"},
    "omega3": {"with_food": True, "best_time": "随餐", "reason": "脂溶性"},
    "CoQ10": {"with_food": True, "best_time": "随餐(早)", "reason": "脂溶性，可能影响睡眠故避免晚服"},
    "Q10": {"with_food": True, "best_time": "随餐(早)", "reason": "脂溶性，可能影响睡眠故避免晚服"},
    "镁": {"with_food": False, "best_time": "睡前30min", "reason": "促进放松和睡眠"},
    "magnesium": {"with_food": False, "best_time": "睡前30min", "reason": "促进放松和睡眠"},
    "NMN": {"with_food": False, "best_time": "空腹(早)", "reason": "空腹吸收更好，避免晚服影响睡眠"},
    "铁": {"with_food": False, "best_time": "空腹 + VC", "reason": "空腹吸收好，VC促进吸收，与钙间隔2h"},
    "iron": {"with_food": False, "best_time": "空腹 + VC", "reason": "空腹吸收好，VC促进吸收，与钙间隔2h"},
    "钙": {"with_food": True, "best_time": "随餐/睡前", "reason": "与铁间隔2h，VD促进吸收"},
    "calcium": {"with_food": True, "best_time": "随餐/睡前", "reason": "与铁间隔2h，VD促进吸收"},
    "褪黑素": {"with_food": False, "best_time": "睡前30-60min", "reason": "辅助入睡"},
    "melatonin": {"with_food": False, "best_time": "睡前30-60min", "reason": "辅助入睡"},
    "B族": {"with_food": True, "best_time": "早餐后", "reason": "可能提神，避免晚服"},
    "VB": {"with_food": True, "best_time": "早餐后", "reason": "可能提神，避免晚服"},
}


class SupplementManager:
    """补剂管理器 — 方案管理、服用记录、依从率、交互检查。"""

    RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("supplement-manager", data_dir=data_dir)
        self.memory_writer = HealthMemoryWriter()

    # ------------------------------------------------------------------
    # RxNorm helpers
    # ------------------------------------------------------------------

    def _make_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        session.headers.update({"Accept": "application/json"})
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _resolve_rxcui(self, name: str) -> str | None:
        """Resolve a supplement name to an RxCUI via RxNorm (best effort)."""
        session = self._make_session()
        url = f"{self.RXNORM_BASE}/rxcui.json"
        try:
            resp = session.get(url, params={"name": name}, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            ids = data.get("idGroup", {}).get("rxnormId", [])
            if ids:
                return ids[0]
            # Fallback: approximate search
            approx_url = f"{self.RXNORM_BASE}/approximateTerm.json"
            resp2 = session.get(approx_url, params={"term": name, "maxEntries": 1}, timeout=15)
            resp2.raise_for_status()
            candidates = resp2.json().get("approximateGroup", {}).get("candidate", [])
            if candidates:
                return candidates[0].get("rxcui")
        except Exception:
            pass
        return None

    def _check_rxnorm_interactions(self, supplement_names: list[str]) -> list[dict]:
        """Check pairwise interactions among supplements via RxNorm interaction API.

        Returns:
            List of dicts with keys: drugs, description, severity
        """
        session = self._make_session()

        # Resolve RxCUIs
        rxcuis: list[str] = []
        for name in supplement_names:
            rxcui = self._resolve_rxcui(name)
            if rxcui:
                rxcuis.append(rxcui)

        if len(rxcuis) < 2:
            return []

        url = f"{self.RXNORM_BASE}/interaction/list.json"
        params = {"rxcuis": "+".join(rxcuis)}

        try:
            resp = session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            interactions: list[dict] = []
            full_results = data.get("fullInteractionTypeGroup", [])

            for group in full_results:
                for itype in group.get("fullInteractionType", []):
                    for pair in itype.get("interactionPair", []):
                        description = pair.get("description", "")
                        severity = pair.get("severity", "N/A")
                        concepts = pair.get("interactionConcept", [])
                        drugs_involved = []
                        for concept in concepts:
                            drug = concept.get("minConceptItem", {}).get("name", "")
                            if drug:
                                drugs_involved.append(drug)
                        interactions.append({
                            "drugs": drugs_involved,
                            "description": description,
                            "severity": severity,
                        })

            return interactions

        except Exception:
            return []

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def add(
        self,
        name: str,
        dose: str,
        frequency: str = "qd",
        timing: str = "08:00",
        category: str = "other",
        with_food: bool | None = None,
    ) -> dict:
        """添加补剂到日常方案。"""
        freq = frequency.lower()
        if freq not in FREQUENCY_MAP:
            print(f"[-] 不支持的频率代码: {frequency}")
            print(f"    可用频率: {', '.join(FREQUENCY_MAP.keys())}")
            return {}

        if category not in CATEGORIES:
            print(f"[-] 不支持的类别: {category}")
            print(f"    可用类别: {', '.join(CATEGORIES)}")
            return {}

        # Auto-detect with_food from timing advice if not specified
        advice = TIMING_ADVICE.get(name)
        if with_food is None:
            with_food = advice["with_food"] if advice else False

        # Print timing advice if available
        if advice:
            print(f"[i] 服用建议 ({name}):")
            print(f"    最佳时间: {advice['best_time']}")
            print(f"    是否随餐: {'是' if advice['with_food'] else '否'}")
            print(f"    原因: {advice['reason']}")

        # Resolve RxCUI (best effort)
        rxcui = self._resolve_rxcui(name)

        data = {
            "name": name,
            "dose": dose,
            "frequency": freq,
            "timing": timing,
            "category": category,
            "rxcui": rxcui,
            "with_food": with_food,
            "status": "active",
        }
        record = self.store.append("supplement", data)

        freq_label = FREQUENCY_LABELS.get(freq, freq)
        print(f"[+] 已添加补剂: {name} {dose}")
        print(f"    频率: {freq_label} | 时间: {timing} | 类别: {category}")
        print(f"    随餐: {'是' if with_food else '否'} | RxCUI: {rxcui or '未找到'}")
        print(f"    ID: {record['id']}")

        self._update_memory()
        return record

    def remove(self, name: str) -> bool:
        """停用一种补剂（按名称匹配）。"""
        supplements = self._get_active_supplements()
        found = None
        for s in supplements:
            if s["data"]["name"].lower() == name.lower():
                found = s
                break

        if not found:
            print(f"[-] 未找到名为 '{name}' 的活跃补剂。")
            return False

        self._update_supplement_field(found["id"], "status", "inactive")
        print(f"[x] 已停用补剂: {name} (ID: {found['id']})")

        self._update_memory()
        return True

    def log(self, name: str, taken: bool = True, note: str = "") -> dict:
        """记录一次服用/跳过。"""
        data = {
            "supplement_name": name,
            "taken": taken,
            "time": datetime.now().strftime("%H:%M"),
            "note": note,
        }
        record = self.store.append("dose_log", data)

        action = "已服用" if taken else "已跳过"
        print(f"[{'v' if taken else 'x'}] {name} {action} ({data['time']})")
        if note:
            print(f"    备注: {note}")

        self._update_memory()
        return record

    def list_supplements(self) -> str:
        """列出所有活跃补剂。"""
        supplements = self._get_active_supplements()
        if not supplements:
            msg = "暂无活跃的补剂方案。"
            print(msg)
            return msg

        lines = ["## 当前补剂列表\n"]
        lines.append("| 补剂 | 剂量 | 频率 | 时间 | 类别 | 随餐 | 建议 |")
        lines.append("|------|------|------|------|------|------|------|")

        for s in supplements:
            d = s["data"]
            freq_label = FREQUENCY_LABELS.get(d["frequency"], d["frequency"])
            with_food = "是" if d.get("with_food") else "否"
            advice = TIMING_ADVICE.get(d["name"])
            advice_text = advice["best_time"] if advice else "-"
            lines.append(
                f"| {d['name']} | {d['dose']} | {freq_label} "
                f"| {d['timing']} | {d['category']} | {with_food} | {advice_text} |"
            )

        lines.append("")
        output = "\n".join(lines)
        print(output)
        return output

    def interactions(self) -> str:
        """检查所有活跃补剂之间的交互。"""
        supplements = self._get_active_supplements()
        names = [s["data"]["name"] for s in supplements]

        if len(names) < 2:
            msg = "活跃补剂少于2种，无需检查交互。"
            print(msg)
            return msg

        print(f"[i] 正在检查 {len(names)} 种补剂的交互: {', '.join(names)} ...")
        results = self._check_rxnorm_interactions(names)

        lines = ["## 补剂交互检查结果\n"]
        lines.append(f"检查补剂: {', '.join(names)}\n")

        if not results:
            lines.append("未发现已知的药物交互。\n")
            lines.append("*注: RxNorm 数据库可能不包含所有补剂的交互信息。"
                         "如有疑虑，请咨询药师。*")
        else:
            for i, intr in enumerate(results, 1):
                drugs = ", ".join(intr.get("drugs", []))
                severity = intr.get("severity", "N/A")
                description = intr.get("description", "")
                lines.append(f"**{i}. {drugs}**")
                lines.append(f"- 严重程度: {severity}")
                lines.append(f"- 说明: {description}")
                lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def adherence(self, days: int = 30) -> str:
        """计算指定时间段的补剂依从率。"""
        supplements = self._get_active_supplements()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        dose_logs = [
            r for r in self.store.query(record_type="dose_log")
            if r["timestamp"] >= cutoff
        ]

        if not supplements:
            msg = "暂无活跃的补剂方案。"
            print(msg)
            return msg

        lines = [f"## 补剂依从性报告 (过去{days}天)\n"]

        total_expected = 0
        total_taken = 0

        for s in supplements:
            d = s["data"]
            name = d["name"]
            freq = d["frequency"]
            daily_doses = FREQUENCY_MAP.get(freq, 0)

            if daily_doses == 0:
                # prn — just show count
                taken_count = len([
                    log for log in dose_logs
                    if log["data"]["supplement_name"] == name and log["data"].get("taken")
                ])
                lines.append(f"### {name} {d['dose']} (按需)")
                lines.append(f"- 过去{days}天服用次数: {taken_count}")
                lines.append("")
                continue

            expected = int(daily_doses * days)
            taken_count = len([
                log for log in dose_logs
                if log["data"]["supplement_name"] == name and log["data"].get("taken")
            ])
            skipped_count = len([
                log for log in dose_logs
                if log["data"]["supplement_name"] == name and not log["data"].get("taken")
            ])
            rate = (taken_count / expected * 100) if expected > 0 else 0

            total_expected += expected
            total_taken += taken_count

            lines.append(f"### {name} {d['dose']}")
            lines.append(f"- 预期服用次数: {expected}")
            lines.append(f"- 实际服用次数: {taken_count}")
            lines.append(f"- 记录跳过次数: {skipped_count}")
            lines.append(f"- 未记录次数: {max(0, expected - taken_count - skipped_count)}")
            lines.append(f"- **依从率: {rate:.1f}%**")
            if rate < 80:
                lines.append(f"- **警告: 依从率低于80%，请注意按时服用**")
            lines.append("")

        if total_expected > 0:
            overall_rate = total_taken / total_expected * 100
            lines.append(f"**总体依从率: {overall_rate:.1f}%**")
        lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def due(self) -> str:
        """检查当前时间窗口（前后30分钟）应服用的补剂。"""
        supplements = self._get_active_supplements()
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        window = 30  # minutes

        due_supplements = []
        for s in supplements:
            d = s["data"]
            try:
                parts = d["timing"].split(":")
                t_minutes = int(parts[0]) * 60 + int(parts[1])
                if abs(current_minutes - t_minutes) <= window:
                    due_supplements.append(s)
            except (ValueError, IndexError):
                continue

        if not due_supplements:
            msg = f"当前时间 ({now.strftime('%H:%M')}) 无需服用补剂。"
            print(msg)
            return msg

        lines = [f"## 当前需服用的补剂 ({now.strftime('%H:%M')})\n"]
        for s in due_supplements:
            d = s["data"]
            with_food = "随餐" if d.get("with_food") else "空腹"
            advice = TIMING_ADVICE.get(d["name"])
            extra = f" | {advice['reason']}" if advice else ""
            lines.append(
                f"- **{d['name']}** {d['dose']} (计划: {d['timing']}, {with_food}{extra})"
            )
        lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    # ------------------------------------------------------------------
    # Memory integration
    # ------------------------------------------------------------------

    def _update_memory(self) -> None:
        """Sync current supplement state to shared health memory."""
        supplements = self._get_active_supplements()

        # Build active regimen
        active_regimen = []
        for s in supplements:
            d = s["data"]
            freq_label = FREQUENCY_LABELS.get(d["frequency"], d["frequency"])
            active_regimen.append({
                "name": d["name"],
                "dose": d["dose"],
                "frequency": freq_label,
                "timing": d["timing"],
                "category": d["category"],
            })

        # Calculate today's adherence
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        today_logs = [
            r for r in self.store.query(record_type="dose_log")
            if r["timestamp"] >= today_start
        ]
        taken_today = len([
            log for log in today_logs if log["data"].get("taken")
        ])
        expected_today = 0
        for s in supplements:
            daily = FREQUENCY_MAP.get(s["data"]["frequency"], 0)
            expected_today += int(daily) if daily >= 1 else (1 if daily > 0 else 0)

        rate_pct = (taken_today / expected_today * 100) if expected_today > 0 else 0
        today_adherence = {
            "taken": taken_today,
            "expected": expected_today,
            "rate_pct": rate_pct,
        }

        # Build warnings from timing conflicts
        warnings = []
        active_names = [s["data"]["name"] for s in supplements]
        # Iron + Calcium conflict
        iron_names = {"铁", "iron"}
        calcium_names = {"钙", "calcium"}
        has_iron = any(n.lower() in iron_names for n in active_names)
        has_calcium = any(n.lower() in calcium_names for n in active_names)
        if has_iron and has_calcium:
            warnings.append("铁与钙应间隔至少2小时服用")

        self.memory_writer.update_supplements(
            active_regimen=active_regimen,
            today_adherence=today_adherence,
            warnings=warnings if warnings else None,
        )
        self.memory_writer.update_daily_snapshot()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_active_supplements(self) -> list:
        """获取所有活跃的补剂。"""
        supplements = self.store.query(record_type="supplement")
        return [s for s in supplements if s["data"].get("status") == "active"]

    def _update_supplement_field(self, record_id: str, field: str, value) -> None:
        """通过重写文件更新指定补剂记录的字段。"""
        if not os.path.exists(self.store.data_file):
            return
        lines = []
        with open(self.store.data_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec["id"] == record_id and rec["type"] == "supplement":
                    rec["data"][field] = value
                lines.append(json.dumps(rec, ensure_ascii=False))
        with open(self.store.data_file, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="补剂管理 — 方案管理、服用记录、依从率、交互检查")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # add
    p_add = subparsers.add_parser("add", help="添加补剂")
    p_add.add_argument("--name", required=True, help="补剂名称 (如 VD3, CoQ10, 鱼油)")
    p_add.add_argument("--dose", required=True, help="剂量 (如 5000IU, 100mg)")
    p_add.add_argument("--freq", default="qd", help="频率 (qd/bid/tid/prn/qw/qod, 默认qd)")
    p_add.add_argument("--timing", default="08:00", help="服用时间 (如 08:00, 默认08:00)")
    p_add.add_argument("--category", default="other",
                       help=f"类别 ({'/'.join(CATEGORIES)}, 默认other)")
    p_add.add_argument("--with-food", action="store_true", default=None,
                       help="随餐服用 (不指定则自动检测)")

    # log
    p_log = subparsers.add_parser("log", help="记录服用")
    p_log.add_argument("--name", required=True, help="补剂名称")
    p_log.add_argument("--skipped", action="store_true", help="标记为跳过")
    p_log.add_argument("--note", default="", help="备注")

    # list
    subparsers.add_parser("list", help="列出所有活跃补剂")

    # remove
    p_remove = subparsers.add_parser("remove", help="停用补剂")
    p_remove.add_argument("--name", required=True, help="补剂名称")

    # interactions
    subparsers.add_parser("interactions", help="检查补剂间交互")

    # adherence
    p_adh = subparsers.add_parser("adherence", help="查看依从率")
    p_adh.add_argument("--days", type=int, default=30, help="统计天数 (默认30)")

    # due
    subparsers.add_parser("due", help="查看当前应服用的补剂")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = SupplementManager()

    if args.command == "add":
        manager.add(
            name=args.name,
            dose=args.dose,
            frequency=args.freq,
            timing=args.timing,
            category=args.category,
            with_food=args.with_food,
        )
    elif args.command == "log":
        taken = not args.skipped
        manager.log(name=args.name, taken=taken, note=args.note)
    elif args.command == "list":
        manager.list_supplements()
    elif args.command == "remove":
        manager.remove(name=args.name)
    elif args.command == "interactions":
        manager.interactions()
    elif args.command == "adherence":
        manager.adherence(days=args.days)
    elif args.command == "due":
        manager.due()


if __name__ == "__main__":
    main()

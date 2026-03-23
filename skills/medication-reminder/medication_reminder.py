#!/usr/bin/env python3
"""用药提醒与依从性追踪工具 - 多药管理、服药记录、依从率统计。"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore


# ---------------------------------------------------------------------------
# Frequency mapping: frequency code -> expected doses per day
# ---------------------------------------------------------------------------
FREQUENCY_MAP = {
    "qd": 1,
    "bid": 2,
    "tid": 3,
    "qid": 4,
    "prn": 0,       # as needed
    "qw": 1 / 7,
    "q2w": 1 / 14,
}

FREQUENCY_LABELS = {
    "qd": "每日1次",
    "bid": "每日2次",
    "tid": "每日3次",
    "qid": "每日4次",
    "prn": "按需服用",
    "qw": "每周1次",
    "q2w": "每两周1次",
}


class MedicationReminder:
    """用药提醒与依从性管理器。"""

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("medication-reminder", data_dir=data_dir)

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def add_medication(
        self,
        drug_name: str,
        dose: str,
        frequency: str,
        timing: list,
        note: str = "",
    ) -> dict:
        """添加用药计划。"""
        freq = frequency.lower()
        if freq not in FREQUENCY_MAP:
            print(f"[-] 不支持的频率代码: {frequency}")
            print(f"    可用频率: {', '.join(FREQUENCY_MAP.keys())}")
            return {}

        data = {
            "drug_name": drug_name,
            "dose": dose,
            "frequency": freq,
            "timing": timing,
            "status": "active",
        }
        record = self.store.append("medication", data, note=note)
        freq_label = FREQUENCY_LABELS.get(freq, freq)
        print(f"[+] 已添加用药计划: {drug_name} {dose}")
        print(f"    频率: {freq_label} | 服药时间: {', '.join(timing)}")
        print(f"    ID: {record['id']}")
        return record

    def list_medications(self) -> str:
        """列出所有活跃的用药计划。"""
        meds = self._get_active_medications()
        if not meds:
            msg = "暂无活跃的用药计划。"
            print(msg)
            return msg

        lines = ["## 当前用药列表\n"]
        for m in meds:
            d = m["data"]
            freq_label = FREQUENCY_LABELS.get(d["frequency"], d["frequency"])
            lines.append(f"- **{d['drug_name']}** {d['dose']}")
            lines.append(f"  频率: {freq_label} | 时间: {', '.join(d['timing'])} | ID: {m['id']}")
            if m.get("note"):
                lines.append(f"  备注: {m['note']}")
        lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def remove_medication(self, med_id: str) -> bool:
        """停用一种药物。"""
        meds = self._get_active_medications()
        found = False
        for m in meds:
            if m["id"] == med_id:
                found = True
                break

        if not found:
            print(f"[-] 未找到ID为 {med_id} 的活跃用药计划。")
            return False

        self._update_medication_field(med_id, "status", "inactive")
        print(f"[x] 已停用药物 {med_id}。")
        return True

    def log_dose(self, drug_name: str, taken: bool = True, note: str = "") -> dict:
        """记录一次服药/漏服。"""
        status = "taken" if taken else "skipped"
        data = {
            "drug_name": drug_name,
            "taken": taken,
            "status": status,
            "log_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        record = self.store.append("dose", data, note=note)
        action = "已服用" if taken else "已跳过"
        print(f"[{'v' if taken else 'x'}] {drug_name} {action} ({data['log_time']})")
        if note:
            print(f"    备注: {note}")
        return record

    def due_now(self) -> str:
        """检查当前时间窗口（前后30分钟）应服用的药物。"""
        meds = self._get_active_medications()
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        window = 30  # minutes

        due_meds = []
        for m in meds:
            d = m["data"]
            for t in d["timing"]:
                try:
                    parts = t.split(":")
                    t_minutes = int(parts[0]) * 60 + int(parts[1])
                    if abs(current_minutes - t_minutes) <= window:
                        due_meds.append((m, t))
                except (ValueError, IndexError):
                    continue

        if not due_meds:
            msg = f"当前时间 ({now.strftime('%H:%M')}) 无需服药。"
            print(msg)
            return msg

        lines = [f"## 当前需服用的药物 ({now.strftime('%H:%M')})\n"]
        for m, t in due_meds:
            d = m["data"]
            lines.append(f"- **{d['drug_name']}** {d['dose']} (计划时间: {t})")
        lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def adherence(self, drug_name: str = None, days: int = 30) -> str:
        """计算指定时间段的用药依从率。"""
        meds = self._get_active_medications()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        doses = [r for r in self.store.query(record_type="dose") if r["timestamp"] >= cutoff]

        if drug_name:
            meds = [m for m in meds if m["data"]["drug_name"] == drug_name]

        if not meds:
            msg = f"未找到{'药物 ' + drug_name + ' 的' if drug_name else ''}活跃用药计划。"
            print(msg)
            return msg

        lines = [f"## 用药依从性报告 (过去{days}天)\n"]

        for m in meds:
            d = m["data"]
            name = d["drug_name"]
            freq = d["frequency"]
            daily_doses = FREQUENCY_MAP.get(freq, 0)

            if daily_doses == 0:
                # prn - just show count
                taken_count = len([dose for dose in doses if dose["data"]["drug_name"] == name and dose["data"].get("taken")])
                lines.append(f"### {name} {d['dose']} (按需)")
                lines.append(f"- 过去{days}天服用次数: {taken_count}")
                lines.append("")
                continue

            expected = int(daily_doses * days)
            taken_count = len([dose for dose in doses if dose["data"]["drug_name"] == name and dose["data"].get("taken")])
            skipped_count = len([dose for dose in doses if dose["data"]["drug_name"] == name and not dose["data"].get("taken")])
            rate = (taken_count / expected * 100) if expected > 0 else 0

            lines.append(f"### {name} {d['dose']}")
            lines.append(f"- 预期服药次数: {expected}")
            lines.append(f"- 实际服药次数: {taken_count}")
            lines.append(f"- 记录跳过次数: {skipped_count}")
            lines.append(f"- 未记录次数: {max(0, expected - taken_count - skipped_count)}")
            lines.append(f"- **依从率: {rate:.1f}%**")
            if rate < 80:
                lines.append(f"- **警告: 依从率低于80%，请注意按时服药**")
            lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def flag_missed(self, days: int = 1) -> str:
        """列出过去N天内漏服的药物。"""
        meds = self._get_active_medications()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        doses = [r for r in self.store.query(record_type="dose") if r["timestamp"] >= cutoff]

        missed = []
        for m in meds:
            d = m["data"]
            name = d["drug_name"]
            freq = d["frequency"]
            daily_doses = FREQUENCY_MAP.get(freq, 0)

            if daily_doses == 0:
                continue  # skip prn

            expected = int(daily_doses * days)
            taken_count = len([dose for dose in doses if dose["data"]["drug_name"] == name and dose["data"].get("taken")])

            if taken_count < expected:
                missed.append({
                    "drug": name,
                    "dose": d["dose"],
                    "expected": expected,
                    "taken": taken_count,
                    "missed": expected - taken_count,
                })

        if not missed:
            msg = f"过去{days}天内所有药物均已按时服用（或无活跃药物）。"
            print(msg)
            return msg

        lines = [f"## 过去{days}天漏服药物\n"]
        for m in missed:
            lines.append(f"- **{m['drug']}** {m['dose']}: 漏服 {m['missed']} 次 (预期 {m['expected']}次, 已服 {m['taken']}次)")
        lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def generate_medication_report(self, days: int = 30) -> str:
        """生成综合用药报告。"""
        meds = self._get_active_medications()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        doses = [r for r in self.store.query(record_type="dose") if r["timestamp"] >= cutoff]

        lines = [f"## 综合用药报告 (过去{days}天)\n"]
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

        # Active medications
        lines.append(f"### 活跃用药 ({len(meds)}种)\n")
        if not meds:
            lines.append("暂无活跃用药。\n")
        else:
            for m in meds:
                d = m["data"]
                freq_label = FREQUENCY_LABELS.get(d["frequency"], d["frequency"])
                lines.append(f"- **{d['drug_name']}** {d['dose']} | {freq_label} | 时间: {', '.join(d['timing'])}")
            lines.append("")

        # Adherence summary
        lines.append("### 依从性概览\n")
        total_expected = 0
        total_taken = 0
        for m in meds:
            d = m["data"]
            name = d["drug_name"]
            freq = d["frequency"]
            daily_doses = FREQUENCY_MAP.get(freq, 0)
            if daily_doses == 0:
                continue
            expected = int(daily_doses * days)
            taken = len([dose for dose in doses if dose["data"]["drug_name"] == name and dose["data"].get("taken")])
            rate = (taken / expected * 100) if expected > 0 else 0
            total_expected += expected
            total_taken += taken
            status = "good" if rate >= 80 else "warning"
            icon = "+" if status == "good" else "!"
            lines.append(f"- [{icon}] {name}: {rate:.1f}% ({taken}/{expected}次)")

        if total_expected > 0:
            overall_rate = total_taken / total_expected * 100
            lines.append(f"\n**总体依从率: {overall_rate:.1f}%**")
            if overall_rate >= 90:
                lines.append("评价: 依从性优秀")
            elif overall_rate >= 80:
                lines.append("评价: 依从性良好")
            elif overall_rate >= 60:
                lines.append("评价: 依从性一般，建议设置提醒")
            else:
                lines.append("评价: 依从性较差，请咨询医生或药师")
        lines.append("")

        # Missed doses in last 24h
        yesterday_cutoff = (datetime.now() - timedelta(days=1)).isoformat()
        recent_doses = [r for r in doses if r["timestamp"] >= yesterday_cutoff]
        lines.append("### 最近24小时服药情况\n")
        if recent_doses:
            for dose in sorted(recent_doses, key=lambda x: x["timestamp"]):
                d = dose["data"]
                status = "已服" if d.get("taken") else "跳过"
                lines.append(f"- {d.get('log_time', '?')} | {d['drug_name']} | {status}")
                if dose.get("note"):
                    lines.append(f"  备注: {dose['note']}")
        else:
            lines.append("无服药记录。")
        lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_active_medications(self) -> list:
        """获取所有活跃的用药计划。"""
        meds = self.store.query(record_type="medication")
        return [m for m in meds if m["data"].get("status") == "active"]

    def _update_medication_field(self, med_id: str, field: str, value) -> None:
        """通过重写文件更新指定药物记录的字段。"""
        if not os.path.exists(self.store.data_file):
            return
        lines = []
        with open(self.store.data_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec["id"] == med_id and rec["type"] == "medication":
                    rec["data"][field] = value
                lines.append(json.dumps(rec, ensure_ascii=False))
        with open(self.store.data_file, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="用药提醒与依从性追踪工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # add
    p_add = subparsers.add_parser("add", help="添加用药计划")
    p_add.add_argument("--drug", required=True, help="药物名称")
    p_add.add_argument("--dose", required=True, help="剂量 (如 500mg)")
    p_add.add_argument("--freq", required=True, help="频率 (qd/bid/tid/qid/prn/qw/q2w)")
    p_add.add_argument("--timing", nargs="+", required=True, help="服药时间 (如 08:00 20:00)")
    p_add.add_argument("--note", default="", help="备注")

    # list
    subparsers.add_parser("list", help="列出所有活跃用药")

    # remove
    p_remove = subparsers.add_parser("remove", help="停用药物")
    p_remove.add_argument("med_id", help="药物ID")

    # log
    p_log = subparsers.add_parser("log", help="记录服药")
    p_log.add_argument("--drug", required=True, help="药物名称")
    p_log.add_argument("--taken", action="store_true", default=True, help="已服用(默认)")
    p_log.add_argument("--skipped", action="store_true", help="跳过未服")
    p_log.add_argument("--note", default="", help="备注")

    # due
    subparsers.add_parser("due", help="查看当前应服药物")

    # adherence
    p_adh = subparsers.add_parser("adherence", help="查看依从率")
    p_adh.add_argument("--drug", default=None, help="药物名称(可选)")
    p_adh.add_argument("--days", type=int, default=30, help="统计天数(默认30)")

    # missed
    p_missed = subparsers.add_parser("missed", help="查看漏服药物")
    p_missed.add_argument("--days", type=int, default=1, help="查看天数(默认1)")

    # report
    p_report = subparsers.add_parser("report", help="生成综合用药报告")
    p_report.add_argument("--days", type=int, default=30, help="报告天数(默认30)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    reminder = MedicationReminder()

    if args.command == "add":
        reminder.add_medication(
            drug_name=args.drug,
            dose=args.dose,
            frequency=args.freq,
            timing=args.timing,
            note=args.note,
        )
    elif args.command == "list":
        reminder.list_medications()
    elif args.command == "remove":
        reminder.remove_medication(args.med_id)
    elif args.command == "log":
        taken = not args.skipped
        reminder.log_dose(drug_name=args.drug, taken=taken, note=args.note)
    elif args.command == "due":
        reminder.due_now()
    elif args.command == "adherence":
        reminder.adherence(drug_name=args.drug, days=args.days)
    elif args.command == "missed":
        reminder.flag_missed(days=args.days)
    elif args.command == "report":
        reminder.generate_medication_report(days=args.days)


if __name__ == "__main__":
    main()

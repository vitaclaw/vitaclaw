#!/usr/bin/env python3
"""复查提醒管理工具 - 按疾病设置复查项目、周期提醒、完成记录。"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore


# ---------------------------------------------------------------------------
# Built-in checklist templates
# ---------------------------------------------------------------------------
CHECKLIST_TEMPLATES = {
    "高血压": ["血压测量(每月)", "血脂检查(每半年)", "肾功能(每年)", "心电图(每年)"],
    "糖尿病": ["空腹血糖(每月)", "HbA1c(每3月)", "尿微量白蛋白(每半年)", "眼底检查(每年)", "足部检查(每半年)"],
    "肿瘤": ["CT/MRI(每3月)", "肿瘤标志物(每3月)", "血常规(每月)", "肝肾功能(每月)"],
}


class FollowUpReminder:
    """复查提醒管理器。"""

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("follow-up-reminder", data_dir=data_dir)

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def add(
        self,
        disease: str,
        item: str,
        interval_days: int,
        checklist: list = None,
        note: str = "",
    ) -> dict:
        """添加一条复查提醒。"""
        next_due = (datetime.now() + timedelta(days=interval_days)).strftime("%Y-%m-%d")
        data = {
            "disease": disease,
            "item": item,
            "interval_days": interval_days,
            "next_due": next_due,
            "checklist": checklist or [],
            "status": "active",
        }
        record = self.store.append("reminder", data, note=note)
        print(f"[+] 已添加复查提醒: {item} (疾病: {disease})")
        print(f"    周期: 每{interval_days}天 | 下次到期: {next_due}")
        if checklist:
            print(f"    检查清单: {', '.join(checklist)}")
        print(f"    ID: {record['id']}")
        return record

    def list_due(self, days_ahead: int = 7) -> str:
        """列出即将到期的提醒（默认7天内）。"""
        reminders = self._get_active_reminders()
        today = datetime.now().strftime("%Y-%m-%d")
        cutoff = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        due = []
        for r in reminders:
            next_due = r["data"]["next_due"]
            if next_due <= cutoff:
                due.append(r)

        if not due:
            msg = f"未来{days_ahead}天内没有到期的复查提醒。"
            print(msg)
            return msg

        due.sort(key=lambda x: x["data"]["next_due"])

        lines = [f"## 未来{days_ahead}天内到期的复查提醒\n"]
        for r in due:
            d = r["data"]
            overdue = d["next_due"] < today
            marker = " **[已过期]**" if overdue else ""
            lines.append(f"- **{d['item']}** ({d['disease']})")
            lines.append(f"  到期日: {d['next_due']}{marker} | 周期: 每{d['interval_days']}天 | ID: {r['id']}")
            if d.get("checklist"):
                for ci in d["checklist"]:
                    lines.append(f"  - [ ] {ci}")
            lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def list_all(self) -> str:
        """列出所有活跃的复查提醒。"""
        reminders = self._get_active_reminders()

        if not reminders:
            msg = "暂无活跃的复查提醒。"
            print(msg)
            return msg

        today = datetime.now().strftime("%Y-%m-%d")
        lines = ["## 所有活跃复查提醒\n"]
        # Group by disease
        by_disease: dict[str, list] = {}
        for r in reminders:
            disease = r["data"]["disease"]
            by_disease.setdefault(disease, []).append(r)

        for disease, items in sorted(by_disease.items()):
            lines.append(f"### {disease}\n")
            for r in items:
                d = r["data"]
                overdue = d["next_due"] < today
                marker = " **[已过期]**" if overdue else ""
                lines.append(f"- **{d['item']}** | 周期: 每{d['interval_days']}天 | 下次到期: {d['next_due']}{marker} | ID: {r['id']}")
                if d.get("checklist"):
                    for ci in d["checklist"]:
                        lines.append(f"  - [ ] {ci}")
            lines.append("")

        output = "\n".join(lines)
        print(output)
        return output

    def mark_done(self, reminder_id: str, result_note: str = "") -> dict | None:
        """标记一条提醒已完成，并自动计算下次到期日。"""
        reminders = self._get_active_reminders()
        target = None
        for r in reminders:
            if r["id"] == reminder_id:
                target = r
                break

        if target is None:
            print(f"[-] 未找到ID为 {reminder_id} 的活跃提醒。")
            return None

        # Log completion
        completion = self.store.append("completion", {
            "reminder_id": reminder_id,
            "disease": target["data"]["disease"],
            "item": target["data"]["item"],
            "completed_date": datetime.now().strftime("%Y-%m-%d"),
        }, note=result_note)

        # Update reminder's next_due by rewriting data file
        new_next_due = (datetime.now() + timedelta(days=target["data"]["interval_days"])).strftime("%Y-%m-%d")
        self._update_reminder_field(reminder_id, "next_due", new_next_due)

        print(f"[v] 已完成: {target['data']['item']} ({target['data']['disease']})")
        print(f"    下次到期日已更新为: {new_next_due}")
        if result_note:
            print(f"    备注: {result_note}")
        return completion

    def remove(self, reminder_id: str) -> bool:
        """停用一条提醒。"""
        reminders = self.store.query(record_type="reminder")
        found = False
        for r in reminders:
            if r["id"] == reminder_id and r["data"].get("status") == "active":
                found = True
                break

        if not found:
            print(f"[-] 未找到ID为 {reminder_id} 的活跃提醒。")
            return False

        self._update_reminder_field(reminder_id, "status", "inactive")
        print(f"[x] 已停用提醒 {reminder_id}。")
        return True

    def generate_checklist(self, disease: str = None) -> str:
        """生成疾病复查清单。"""
        if disease and disease in CHECKLIST_TEMPLATES:
            items = CHECKLIST_TEMPLATES[disease]
            lines = [f"## {disease} 复查清单\n"]
            for item in items:
                lines.append(f"- [ ] {item}")
            output = "\n".join(lines)
            print(output)
            return output

        if disease:
            print(f"[-] 未找到 {disease} 的内置清单模板。")
            print(f"    可用模板: {', '.join(CHECKLIST_TEMPLATES.keys())}")
            return ""

        # Show all templates
        lines = ["## 可用复查清单模板\n"]
        for d, items in CHECKLIST_TEMPLATES.items():
            lines.append(f"### {d}\n")
            for item in items:
                lines.append(f"- [ ] {item}")
            lines.append("")
        output = "\n".join(lines)
        print(output)
        return output

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_active_reminders(self) -> list:
        """获取所有活跃的提醒记录。"""
        reminders = self.store.query(record_type="reminder")
        return [r for r in reminders if r["data"].get("status") == "active"]

    def _update_reminder_field(self, reminder_id: str, field: str, value) -> None:
        """通过重写文件更新指定提醒的字段。"""
        if not os.path.exists(self.store.data_file):
            return
        lines = []
        with open(self.store.data_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec["id"] == reminder_id and rec["type"] == "reminder":
                    rec["data"][field] = value
                lines.append(json.dumps(rec, ensure_ascii=False))
        with open(self.store.data_file, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="复查提醒管理工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # add
    p_add = subparsers.add_parser("add", help="添加复查提醒")
    p_add.add_argument("--disease", required=True, help="疾病名称")
    p_add.add_argument("--item", required=True, help="复查项目")
    p_add.add_argument("--interval", type=int, required=True, help="复查周期（天）")
    p_add.add_argument("--checklist", nargs="*", default=None, help="检查清单项目")
    p_add.add_argument("--note", default="", help="备注")

    # due
    p_due = subparsers.add_parser("due", help="查看即将到期的提醒")
    p_due.add_argument("--days", type=int, default=7, help="提前天数（默认7天）")

    # done
    p_done = subparsers.add_parser("done", help="标记提醒已完成")
    p_done.add_argument("reminder_id", help="提醒ID")
    p_done.add_argument("--note", default="", help="结果备注")

    # remove
    p_remove = subparsers.add_parser("remove", help="停用提醒")
    p_remove.add_argument("reminder_id", help="提醒ID")

    # checklist
    p_checklist = subparsers.add_parser("checklist", help="生成复查清单")
    p_checklist.add_argument("--disease", default=None, help="疾病名称")

    # list
    subparsers.add_parser("list", help="列出所有活跃提醒")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    reminder = FollowUpReminder()

    if args.command == "add":
        reminder.add(
            disease=args.disease,
            item=args.item,
            interval_days=args.interval,
            checklist=args.checklist,
            note=args.note,
        )
    elif args.command == "due":
        reminder.list_due(days_ahead=args.days)
    elif args.command == "done":
        reminder.mark_done(args.reminder_id, result_note=args.note)
    elif args.command == "remove":
        reminder.remove(args.reminder_id)
    elif args.command == "checklist":
        reminder.generate_checklist(disease=args.disease)
    elif args.command == "list":
        reminder.list_all()


if __name__ == "__main__":
    main()

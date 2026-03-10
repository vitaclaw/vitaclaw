#!/usr/bin/env python3
"""肿瘤患者营养评估与饮食方案生成 - NRS-2002评分 + LLM营养建议。"""

import argparse
import json
import os
from datetime import datetime, timedelta

import sys as _sys

import requests

_sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '_shared'))
from health_data_store import HealthDataStore


# ---------------------------------------------------------------------------
# OpenRouter LLM Configuration
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.environ.get(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
)
LLM_MODEL = os.environ.get("LLM_MODEL", "google/gemini-2.5-flash")


def _llm_call(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Call LLM via OpenRouter API."""
    if not OPENROUTER_API_KEY:
        return "[错误] 未设置 OPENROUTER_API_KEY 环境变量"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        resp = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"[LLM调用失败] {e}"


# ---------------------------------------------------------------------------
# NRS-2002 评分标准
# ---------------------------------------------------------------------------
NRS_NUTRITION_CRITERIA = {
    0: "正常营养状态",
    1: "3个月内体重下降>5% 或近1周进食量减少25-50%",
    2: "2个月内体重下降>5% 或BMI 18.5-20.5+一般状况差 或近1周进食量减少50-75%",
    3: "1个月内体重下降>5% 或BMI<18.5+一般状况差 或近1周进食量减少75-100%",
}

NRS_DISEASE_CRITERIA = {
    0: "无",
    1: "慢性疾病急性发作/髋部骨折/糖尿病",
    2: "腹部大手术/脑卒中/肺炎/血液恶性肿瘤",
    3: "头部损伤/骨髓移植/ICU患者(APACHE>10)",
}

BMI_CATEGORIES_CN = [
    (0, 18.5, "偏瘦"),
    (18.5, 24.0, "正常"),
    (24.0, 28.0, "超重"),
    (28.0, float("inf"), "肥胖"),
]


# ---------------------------------------------------------------------------
# CancerNutritionCoach
# ---------------------------------------------------------------------------
class CancerNutritionCoach:
    """肿瘤患者营养教练，提供NRS-2002评分、体重监测、BMI计算、饮食方案生成和综合营养报告。"""

    def __init__(self, data_dir: str = None):
        self.store = HealthDataStore("cancer-nutrition-coach", data_dir=data_dir)

    # ------------------------------------------------------------------ #
    # record - 记录营养数据
    # ------------------------------------------------------------------ #
    def record(
        self,
        weight: float = None,
        height: float = None,
        albumin: float = None,
        prealbumin: float = None,
        daily_intake_kcal: float = None,
        treatment_phase: str = "",
        note: str = "",
    ) -> dict:
        """记录一次营养相关数据。

        Args:
            weight: 体重 (kg)
            height: 身高 (cm)
            albumin: 血清白蛋白 (g/L)
            prealbumin: 前白蛋白 (mg/L)
            daily_intake_kcal: 每日摄入热量 (kcal)
            treatment_phase: 治疗阶段，如 化疗期、放疗期、术后恢复期
            note: 备注
        Returns:
            保存的记录
        """
        data = {}
        if weight is not None:
            data["weight"] = weight
        if height is not None:
            data["height"] = height
        if albumin is not None:
            data["albumin"] = albumin
        if prealbumin is not None:
            data["prealbumin"] = prealbumin
        if daily_intake_kcal is not None:
            data["daily_intake_kcal"] = daily_intake_kcal
        if treatment_phase:
            data["treatment_phase"] = treatment_phase

        if not data:
            print("未提供任何营养数据，请至少输入一项指标")
            return {}

        rec = self.store.append("nutrition", data, note=note)

        # 打印确认信息
        print("已记录营养数据:")
        if weight is not None:
            print(f"  体重: {weight} kg")
        if height is not None:
            print(f"  身高: {height} cm")
        if albumin is not None:
            alb_status = "偏低" if albumin < 35 else "正常"
            print(f"  白蛋白: {albumin} g/L ({alb_status}, 参考: 35-55 g/L)")
        if prealbumin is not None:
            pa_status = "偏低" if prealbumin < 200 else "正常"
            print(f"  前白蛋白: {prealbumin} mg/L ({pa_status}, 参考: 200-400 mg/L)")
        if daily_intake_kcal is not None:
            print(f"  每日摄入热量: {daily_intake_kcal} kcal")
        if treatment_phase:
            print(f"  治疗阶段: {treatment_phase}")

        # 即时警告
        if albumin is not None and albumin < 30:
            print("  !! 白蛋白严重偏低 (<30 g/L)，建议及时营养干预")
        if prealbumin is not None and prealbumin < 150:
            print("  !! 前白蛋白严重偏低 (<150 mg/L)，提示近期营养状态差")

        return rec

    # ------------------------------------------------------------------ #
    # nrs_2002_screen - NRS-2002 营养风险筛查
    # ------------------------------------------------------------------ #
    def nrs_2002_screen(self, nutrition_score: int, disease_score: int, age: int) -> dict:
        """NRS-2002营养风险筛查评分。

        Args:
            nutrition_score: 营养状态评分 (0-3)
            disease_score: 疾病严重程度评分 (0-3)
            age: 年龄
        Returns:
            评分明细和风险等级
        """
        # 校验输入
        if not (0 <= nutrition_score <= 3):
            print(f"营养状态评分应为0-3，输入值 {nutrition_score} 无效")
            return {}
        if not (0 <= disease_score <= 3):
            print(f"疾病严重程度评分应为0-3，输入值 {disease_score} 无效")
            return {}

        age_adjustment = 1 if age >= 70 else 0
        total = nutrition_score + disease_score + age_adjustment

        has_risk = total >= 3
        risk_level = "有营养风险" if has_risk else "暂无营养风险"
        recommendation = "建议制定营养干预计划" if has_risk else "建议每周复筛"

        result = {
            "nutrition_score": nutrition_score,
            "nutrition_criteria": NRS_NUTRITION_CRITERIA.get(nutrition_score, ""),
            "disease_score": disease_score,
            "disease_criteria": NRS_DISEASE_CRITERIA.get(disease_score, ""),
            "age": age,
            "age_adjustment": age_adjustment,
            "total_score": total,
            "has_risk": has_risk,
            "risk_level": risk_level,
            "recommendation": recommendation,
        }

        # 保存筛查记录
        self.store.append("nrs_2002", result, note=f"NRS-2002评分: {total}分")

        # 输出
        print("=" * 50)
        print("  NRS-2002 营养风险筛查")
        print("=" * 50)
        print(f"  营养状态评分: {nutrition_score} 分")
        print(f"    标准: {NRS_NUTRITION_CRITERIA.get(nutrition_score, '')}")
        print(f"  疾病严重程度评分: {disease_score} 分")
        print(f"    标准: {NRS_DISEASE_CRITERIA.get(disease_score, '')}")
        print(f"  年龄: {age} 岁 (校正: +{age_adjustment} 分)")
        print("-" * 50)
        print(f"  总评分: {total} 分")
        risk_marker = "!!" if has_risk else "OK"
        print(f"  [{risk_marker}] {risk_level}")
        print(f"  建议: {recommendation}")
        print("=" * 50)

        if has_risk:
            print("\n  NRS-2002 评分 >= 3 分，存在营养风险。")
            print("  建议措施:")
            print("    1. 请营养科会诊，制定个体化营养方案")
            print("    2. 增加蛋白质摄入 (1.2-1.5 g/kg/天)")
            print("    3. 保证热量摄入 (25-30 kcal/kg/天)")
            if nutrition_score >= 3:
                print("    4. 考虑肠内/肠外营养支持")
            if disease_score >= 3:
                print("    4. ICU/重症患者需强化营养监测")

        return result

    # ------------------------------------------------------------------ #
    # weight_alert - 体重预警
    # ------------------------------------------------------------------ #
    def weight_alert(self, days: int = 30) -> dict:
        """检查近N天体重变化趋势，若下降超过5%则预警。

        Args:
            days: 监测天数窗口
        Returns:
            体重趋势分析结果
        """
        trend_data = self.store.trend("nutrition", "weight", window=days)
        values = trend_data.get("values", [])

        if len(values) < 2:
            print(f"近{days}天体重记录不足2次，无法进行趋势分析")
            return {"status": "insufficient_data", "values": values}

        first_val = values[0]
        last_val = values[-1]
        change_pct = ((last_val - first_val) / first_val) * 100 if first_val > 0 else 0
        abs_change = last_val - first_val

        direction_cn = {
            "rising": "上升",
            "falling": "下降",
            "stable": "稳定",
        }.get(trend_data["direction"], "未知")

        print(f"\n体重趋势分析 (近{days}天)")
        print(f"  记录次数: {len(values)}")
        print(f"  首次记录: {first_val} kg")
        print(f"  最近记录: {last_val} kg")
        print(f"  变化: {abs_change:+.1f} kg ({change_pct:+.1f}%)")
        print(f"  趋势: {direction_cn} (斜率: {trend_data['slope']})")

        is_alert = change_pct < -5
        is_consecutive_falling = self.store.consecutive_check("nutrition", "weight", "falling", count=3)

        result = {
            "status": "alert" if is_alert else "normal",
            "first_weight": first_val,
            "last_weight": last_val,
            "change_kg": round(abs_change, 2),
            "change_pct": round(change_pct, 1),
            "direction": trend_data["direction"],
            "slope": trend_data["slope"],
            "consecutive_falling": is_consecutive_falling,
            "count": len(values),
        }

        if is_alert:
            print(f"\n  !! 体重下降超过5% ({change_pct:.1f}%)，存在营养风险")
            print("  建议措施:")
            print("    1. 进行NRS-2002营养风险筛查")
            print("    2. 增加每日热量和蛋白质摄入")
            print("    3. 排查引起体重下降的原因（进食障碍、吸收不良等）")
            print("    4. 考虑营养科会诊")
        elif is_consecutive_falling:
            print(f"\n  注意: 体重连续3次下降，需密切关注")
        else:
            print(f"\n  体重变化在正常范围内")

        return result

    # ------------------------------------------------------------------ #
    # bmi_calculate - BMI 计算
    # ------------------------------------------------------------------ #
    def bmi_calculate(self, weight: float, height: float) -> dict:
        """计算BMI并按中国标准分级。

        Args:
            weight: 体重 (kg)
            height: 身高 (cm)
        Returns:
            BMI值及分类
        """
        if weight <= 0 or height <= 0:
            print("体重和身高必须为正数")
            return {}

        height_m = height / 100.0
        bmi = weight / (height_m ** 2)

        category = "未知"
        for low, high, cat in BMI_CATEGORIES_CN:
            if low <= bmi < high:
                category = cat
                break

        result = {
            "weight": weight,
            "height": height,
            "bmi": round(bmi, 1),
            "category": category,
        }

        print(f"\nBMI 计算结果")
        print(f"  体重: {weight} kg")
        print(f"  身高: {height} cm")
        print(f"  BMI: {bmi:.1f} kg/m2")
        print(f"  分类: {category}")
        print(f"\n  中国标准: 偏瘦<18.5 | 正常18.5-23.9 | 超重24-27.9 | 肥胖>=28")

        # 肿瘤患者特殊提示
        if bmi < 18.5:
            print("\n  !! BMI偏低，肿瘤患者低BMI与预后不良相关")
            print("  建议: 增加热量和蛋白质摄入，必要时营养支持")
            # 推荐每日热量目标
            target_kcal_low = int(weight * 30)
            target_kcal_high = int(weight * 35)
            print(f"  参考每日热量目标: {target_kcal_low}-{target_kcal_high} kcal")
        elif bmi >= 28:
            print("\n  BMI偏高。肿瘤患者仍需保证充足营养，不建议严格节食减重")

        return result

    # ------------------------------------------------------------------ #
    # generate_diet_plan - LLM生成个性化饮食方案
    # ------------------------------------------------------------------ #
    def generate_diet_plan(
        self,
        diagnosis: str,
        treatment_phase: str,
        allergies: str = "",
        preferences: str = "",
    ) -> str:
        """基于LLM生成肿瘤患者个性化饮食方案。

        Args:
            diagnosis: 诊断，如 结直肠癌、肺腺癌
            treatment_phase: 治疗阶段，如 FOLFOX化疗中、术后恢复期、放疗中
            allergies: 过敏食物，如 海鲜、牛奶
            preferences: 饮食偏好，如 素食、低盐
        Returns:
            饮食方案文本
        """
        # 获取最新营养数据作为上下文
        latest_records = self.store.get_latest(record_type="nutrition", n=3)
        nutrition_context = ""
        if latest_records:
            nutrition_context = "\n患者近期营养数据:\n"
            for r in latest_records:
                d = r["data"]
                parts = []
                if "weight" in d:
                    parts.append(f"体重{d['weight']}kg")
                if "albumin" in d:
                    parts.append(f"白蛋白{d['albumin']}g/L")
                if "prealbumin" in d:
                    parts.append(f"前白蛋白{d['prealbumin']}mg/L")
                if "daily_intake_kcal" in d:
                    parts.append(f"每日摄入{d['daily_intake_kcal']}kcal")
                if "treatment_phase" in d:
                    parts.append(f"阶段:{d['treatment_phase']}")
                nutrition_context += f"  [{r['timestamp'][:10]}] {', '.join(parts)}\n"

        # 获取最近NRS-2002记录
        nrs_records = self.store.get_latest(record_type="nrs_2002", n=1)
        nrs_context = ""
        if nrs_records:
            nrs = nrs_records[0]["data"]
            nrs_context = f"\nNRS-2002评分: {nrs.get('total_score', '未知')}分 ({nrs.get('risk_level', '')})\n"

        system_prompt = """你是一位专业的肿瘤营养师。请根据患者信息生成个性化的饮食方案。

要求:
1. 考虑癌症类型对营养代谢的特殊影响
2. 根据治疗阶段提供针对性建议:
   - 手术恢复期: 高蛋白促进伤口愈合
   - 化疗期: 应对恶心、口腔黏膜炎、味觉改变等副作用
   - 放疗期: 保护照射区域粘膜，维持摄入
   - 维持期: 均衡营养，预防复发
3. 热量目标: 25-30 kcal/kg/天 (低体重者可至30-35 kcal/kg/天)
4. 蛋白质目标: 1.2-1.5 g/kg/天 (手术后可至1.5-2.0 g/kg/天)
5. 明确列出推荐食物和应避免食物
6. 提供一日三餐+加餐的具体示例
7. 说明补充剂建议 (如鱼油、维生素D、乳清蛋白等)
8. 考虑患者过敏史和饮食偏好
9. 使用中文输出
10. 饮食方案需科学严谨，标注营养学依据"""

        user_prompt = f"""请为以下肿瘤患者生成个性化饮食方案:

诊断: {diagnosis}
治疗阶段: {treatment_phase}
过敏食物: {allergies or '无'}
饮食偏好: {preferences or '无特殊偏好'}
{nutrition_context}
{nrs_context}
请生成包含以下内容的完整饮食方案:
1. 营养目标 (每日热量和蛋白质目标)
2. 治疗阶段特殊注意事项
3. 推荐食物清单
4. 应避免/限制食物清单
5. 一日食谱示例 (早餐、午餐、晚餐、加餐)
6. 餐次与时间安排建议
7. 营养补充剂建议
8. 饮食管理小贴士"""

        print(f"\n正在为 {diagnosis}({treatment_phase}) 患者生成个性化饮食方案...")

        plan = _llm_call(system_prompt, user_prompt, max_tokens=4096)

        # 保存饮食方案
        self.store.append(
            "diet_plan",
            {
                "diagnosis": diagnosis,
                "treatment_phase": treatment_phase,
                "allergies": allergies,
                "preferences": preferences,
                "plan": plan,
            },
            note=f"饮食方案: {diagnosis} - {treatment_phase}",
        )

        print("\n" + "=" * 60)
        print("  个性化饮食方案")
        print("=" * 60)
        print(f"  诊断: {diagnosis}")
        print(f"  治疗阶段: {treatment_phase}")
        if allergies:
            print(f"  过敏食物: {allergies}")
        if preferences:
            print(f"  饮食偏好: {preferences}")
        print("-" * 60)
        print(plan)
        print("=" * 60)
        print("  注意: 此饮食方案由AI生成，仅供参考。请在专业营养师指导下实施。")
        print("=" * 60)

        return plan

    # ------------------------------------------------------------------ #
    # generate_nutrition_report - 综合营养报告
    # ------------------------------------------------------------------ #
    def generate_nutrition_report(self, days: int = 30) -> str:
        """生成综合营养报告。

        Args:
            days: 报告覆盖天数
        Returns:
            综合报告文本
        """
        lines = []
        lines.append("=" * 60)
        lines.append(f"  综合营养报告 (近{days}天)")
        lines.append("=" * 60)

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        records = [r for r in self.store.query(record_type="nutrition") if r["timestamp"] >= cutoff]

        if not records:
            msg = f"近{days}天无营养记录，无法生成报告"
            print(msg)
            return msg

        lines.append(f"  记录数量: {len(records)}")
        lines.append(f"  时间范围: {records[0]['timestamp'][:10]} ~ {records[-1]['timestamp'][:10]}")
        lines.append("")

        # ----- 体重趋势 -----
        weight_trend = self.store.trend("nutrition", "weight", window=days)
        weight_values = weight_trend.get("values", [])
        if weight_values:
            lines.append("-- 体重趋势 --")
            lines.append(f"  记录次数: {len(weight_values)}")
            lines.append(f"  最新体重: {weight_values[-1]} kg")
            if len(weight_values) >= 2:
                change = weight_values[-1] - weight_values[0]
                pct = (change / weight_values[0]) * 100 if weight_values[0] > 0 else 0
                direction_cn = {"rising": "上升", "falling": "下降", "stable": "稳定", "insufficient_data": "数据不足"}.get(weight_trend["direction"], "未知")
                lines.append(f"  均值: {weight_trend['mean']} kg")
                lines.append(f"  变化: {change:+.1f} kg ({pct:+.1f}%)")
                lines.append(f"  趋势: {direction_cn}")
                if pct < -5:
                    lines.append(f"  !! 体重下降超过5%，存在营养风险")
            lines.append("")

        # ----- BMI -----
        latest = self.store.get_latest(record_type="nutrition", n=1)
        if latest:
            ld = latest[0]["data"]
            if "weight" in ld and "height" in ld:
                h_m = ld["height"] / 100.0
                bmi = ld["weight"] / (h_m ** 2)
                category = "未知"
                for low, high, cat in BMI_CATEGORIES_CN:
                    if low <= bmi < high:
                        category = cat
                        break
                lines.append("-- BMI --")
                lines.append(f"  当前BMI: {bmi:.1f} kg/m2 ({category})")
                lines.append("")

        # ----- 白蛋白趋势 -----
        alb_trend = self.store.trend("nutrition", "albumin", window=days)
        alb_values = alb_trend.get("values", [])
        if alb_values:
            lines.append("-- 白蛋白趋势 --")
            lines.append(f"  记录次数: {len(alb_values)}")
            lines.append(f"  最新值: {alb_values[-1]} g/L (参考: 35-55 g/L)")
            if len(alb_values) >= 2:
                direction_cn = {"rising": "上升", "falling": "下降", "stable": "稳定", "insufficient_data": "数据不足"}.get(alb_trend["direction"], "未知")
                lines.append(f"  均值: {alb_trend['mean']} g/L")
                lines.append(f"  趋势: {direction_cn}")
            if alb_values[-1] < 35:
                lines.append(f"  !! 白蛋白偏低 ({alb_values[-1]} g/L < 35 g/L)")
            if alb_values[-1] < 30:
                lines.append(f"  !! 白蛋白严重偏低，建议营养干预")
            lines.append("")

        # ----- 前白蛋白趋势 -----
        pa_trend = self.store.trend("nutrition", "prealbumin", window=days)
        pa_values = pa_trend.get("values", [])
        if pa_values:
            lines.append("-- 前白蛋白趋势 --")
            lines.append(f"  记录次数: {len(pa_values)}")
            lines.append(f"  最新值: {pa_values[-1]} mg/L (参考: 200-400 mg/L)")
            if len(pa_values) >= 2:
                direction_cn = {"rising": "上升", "falling": "下降", "stable": "稳定", "insufficient_data": "数据不足"}.get(pa_trend["direction"], "未知")
                lines.append(f"  均值: {pa_trend['mean']} mg/L")
                lines.append(f"  趋势: {direction_cn}")
            if pa_values[-1] < 200:
                lines.append(f"  !! 前白蛋白偏低 ({pa_values[-1]} mg/L < 200 mg/L)")
            lines.append("")

        # ----- 热量摄入趋势 -----
        kcal_trend = self.store.trend("nutrition", "daily_intake_kcal", window=days)
        kcal_values = kcal_trend.get("values", [])
        if kcal_values:
            lines.append("-- 每日热量摄入趋势 --")
            lines.append(f"  记录次数: {len(kcal_values)}")
            lines.append(f"  最新值: {kcal_values[-1]} kcal")
            if len(kcal_values) >= 2:
                direction_cn = {"rising": "上升", "falling": "下降", "stable": "稳定", "insufficient_data": "数据不足"}.get(kcal_trend["direction"], "未知")
                lines.append(f"  均值: {kcal_trend['mean']} kcal")
                lines.append(f"  趋势: {direction_cn}")
            # 结合体重计算是否达标
            if weight_values:
                current_weight = weight_values[-1]
                target_low = int(current_weight * 25)
                target_high = int(current_weight * 30)
                lines.append(f"  目标范围: {target_low}-{target_high} kcal/天 (按体重{current_weight}kg计)")
                if kcal_values[-1] < target_low:
                    lines.append(f"  !! 热量摄入不足 ({kcal_values[-1]} < {target_low} kcal)")
            lines.append("")

        # ----- NRS-2002 最近评分 -----
        nrs_records = [r for r in self.store.query(record_type="nrs_2002") if r["timestamp"] >= cutoff]
        if nrs_records:
            latest_nrs = nrs_records[-1]["data"]
            lines.append("-- NRS-2002 最近评分 --")
            lines.append(f"  总评分: {latest_nrs.get('total_score', '未知')} 分")
            lines.append(f"  风险等级: {latest_nrs.get('risk_level', '未知')}")
            lines.append(f"  建议: {latest_nrs.get('recommendation', '')}")
            lines.append("")

        # ----- 综合建议 -----
        lines.append("-- 综合建议 --")
        alerts = []
        if weight_values and len(weight_values) >= 2:
            change_pct = ((weight_values[-1] - weight_values[0]) / weight_values[0]) * 100
            if change_pct < -5:
                alerts.append("体重下降超过5%，建议营养干预")
        if alb_values and alb_values[-1] < 35:
            alerts.append("白蛋白偏低，建议增加蛋白质摄入")
        if pa_values and pa_values[-1] < 200:
            alerts.append("前白蛋白偏低，提示近期营养状态欠佳")
        if kcal_values and weight_values:
            target_low = int(weight_values[-1] * 25)
            if kcal_values[-1] < target_low:
                alerts.append("每日热量摄入不足，建议增加进食量或考虑ONS(口服营养补充)")

        if alerts:
            for i, a in enumerate(alerts, 1):
                lines.append(f"  {i}. {a}")
        else:
            lines.append("  各项营养指标在正常范围内，继续保持良好的营养状态。")

        lines.append("")
        lines.append("=" * 60)
        lines.append("  注意: 本报告仅供参考，不替代专业营养评估。")
        lines.append("=" * 60)

        report = "\n".join(lines)
        print(report)

        # 保存报告
        self.store.append(
            "nutrition_report",
            {"days": days, "report": report},
            note=f"综合营养报告({days}天)",
        )

        return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="肿瘤患者营养教练 (NRS-2002 + LLM饮食方案)")
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # record
    p_rec = sub.add_parser("record", help="记录营养数据")
    p_rec.add_argument("--weight", type=float, default=None, help="体重 (kg)")
    p_rec.add_argument("--height", type=float, default=None, help="身高 (cm)")
    p_rec.add_argument("--albumin", type=float, default=None, help="白蛋白 (g/L)")
    p_rec.add_argument("--prealbumin", type=float, default=None, help="前白蛋白 (mg/L)")
    p_rec.add_argument("--intake", type=float, default=None, help="每日摄入热量 (kcal)")
    p_rec.add_argument("--phase", default="", help="治疗阶段")
    p_rec.add_argument("--note", default="", help="备注")

    # screen (NRS-2002)
    p_screen = sub.add_parser("screen", help="NRS-2002营养风险筛查")
    p_screen.add_argument("--ns", type=int, required=True, help="营养状态评分 (0-3)")
    p_screen.add_argument("--ds", type=int, required=True, help="疾病严重程度评分 (0-3)")
    p_screen.add_argument("--age", type=int, required=True, help="年龄")

    # weight-alert
    p_alert = sub.add_parser("weight-alert", help="体重预警")
    p_alert.add_argument("--days", type=int, default=30, help="监测天数 (默认30)")

    # bmi
    p_bmi = sub.add_parser("bmi", help="BMI计算")
    p_bmi.add_argument("--weight", type=float, required=True, help="体重 (kg)")
    p_bmi.add_argument("--height", type=float, required=True, help="身高 (cm)")

    # diet-plan
    p_diet = sub.add_parser("diet-plan", help="生成个性化饮食方案")
    p_diet.add_argument("--diagnosis", required=True, help="诊断")
    p_diet.add_argument("--phase", required=True, help="治疗阶段")
    p_diet.add_argument("--allergies", default="", help="过敏食物")
    p_diet.add_argument("--preferences", default="", help="饮食偏好")

    # report
    p_report = sub.add_parser("report", help="生成综合营养报告")
    p_report.add_argument("--days", type=int, default=30, help="报告天数 (默认30)")

    args = parser.parse_args()
    coach = CancerNutritionCoach()

    if args.command == "record":
        coach.record(
            weight=args.weight,
            height=args.height,
            albumin=args.albumin,
            prealbumin=args.prealbumin,
            daily_intake_kcal=args.intake,
            treatment_phase=args.phase,
            note=args.note,
        )
    elif args.command == "screen":
        coach.nrs_2002_screen(
            nutrition_score=args.ns,
            disease_score=args.ds,
            age=args.age,
        )
    elif args.command == "weight-alert":
        coach.weight_alert(days=args.days)
    elif args.command == "bmi":
        coach.bmi_calculate(weight=args.weight, height=args.height)
    elif args.command == "diet-plan":
        coach.generate_diet_plan(
            diagnosis=args.diagnosis,
            treatment_phase=args.phase,
            allergies=args.allergies,
            preferences=args.preferences,
        )
    elif args.command == "report":
        coach.generate_nutrition_report(days=args.days)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""Generate a realistic-looking Chinese annual checkup report PDF for testing."""

from pathlib import Path
from fpdf import FPDF

# Output path
OUTPUT = Path.home() / ".openclaw" / "skills" / "annual-checkup-advisor" / "test_sample.pdf"

# Font paths (Windows)
FONT_DIR = Path("C:/Windows/Fonts")
SIMHEI = str(FONT_DIR / "simhei.ttf")
SIMSUN = str(FONT_DIR / "simsun.ttc")

# Layout constants
TABLE_W4 = [60, 38, 42, 40]  # 4-col: 项目(60) 结果 参考范围 状态 = 180mm
TABLE_W3 = [60, 60, 60]       # 3-col: 项目 结果 状态 = 180mm
TABLE_WIDTH = 180
X_OFFSET = (210 - TABLE_WIDTH) / 2  # 15mm each side


class CheckupReport(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("simhei", "", SIMHEI)
        self.add_font("simsun", "", SIMSUN)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("simhei", size=9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, "仁和健康管理中心", align="L")
        self.cell(0, 6, "体检编号: TJ-2026-03-00587", align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 102, 153)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("simsun", size=7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "本报告仅供健康参考，不作为临床诊断依据。如有异常请及时就医。", align="L")
        self.cell(0, 5, f"第 {self.page_no()} 页", align="R")

    def section_title(self, title):
        self.ln(3)
        self.set_font("simhei", size=12)
        self.set_text_color(0, 80, 130)
        self.set_fill_color(230, 240, 250)
        self.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def info_row(self, label, value):
        self.set_font("simsun", size=10)
        self.set_text_color(80, 80, 80)
        self.cell(25, 6, label, new_x="RIGHT")
        self.set_text_color(0, 0, 0)
        self.cell(45, 6, value, new_x="RIGHT")

    def table_header(self, cols, widths):
        self.set_x(X_OFFSET)
        self.set_font("simhei", size=9)
        self.set_fill_color(0, 80, 130)
        self.set_text_color(255, 255, 255)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=True, align="C", new_x="RIGHT")
        self.ln()

    def table_row(self, cells, widths, status="normal"):
        self.set_x(X_OFFSET)
        self.set_font("simsun", size=9)
        for i, cell in enumerate(cells):
            if i == len(cells) - 1:  # status column
                if "偏高" in cell or "↑" in cell:
                    self.set_text_color(200, 50, 50)
                    self.set_font("simhei", size=9)
                elif "偏低" in cell or "↓" in cell:
                    self.set_text_color(200, 130, 0)
                    self.set_font("simhei", size=9)
                elif "边缘" in cell:
                    self.set_text_color(200, 130, 0)
                    self.set_font("simhei", size=9)
                else:
                    self.set_text_color(0, 130, 60)
            else:
                self.set_text_color(40, 40, 40)
                self.set_font("simsun", size=9)
            align = "C" if i >= 1 else "L"
            self.cell(widths[i], 6.5, cell, border=1, align=align, new_x="RIGHT")
        self.ln()

    def paragraph(self, text):
        self.set_font("simsun", size=10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 6, text)
        self.ln(1)

    def table_section(self, title, cols, widths, rows):
        """Draw a section title + table header + all rows."""
        self.section_title(title)
        self.table_header(cols, widths)
        for r in rows:
            self.table_row(r, widths)


def build_report():
    pdf = CheckupReport()
    pdf.add_page()

    # === Title block ===
    pdf.ln(5)
    pdf.set_font("simhei", size=20)
    pdf.set_text_color(0, 70, 120)
    pdf.cell(0, 12, "年度健康体检报告", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("simsun", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, "仁和健康管理中心", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_draw_color(0, 102, 153)
    pdf.set_line_width(0.8)
    pdf.line(30, pdf.get_y(), 180, pdf.get_y())
    pdf.ln(6)

    # === Personal info (centered two-column layout) ===
    pdf.section_title("基本信息")
    info_pairs = [
        ("姓  名:", "陈启明",    "性  别:", "男"),
        ("年  龄:", "35岁",      "体检日期:", "2026-03-10"),
        ("身  高:", "178 cm",    "体  重:", "85 kg"),
        ("BMI:",    "26.8 (超重)", "体检编号:", "TJ-2026-03-00587"),
    ]
    col_x1 = X_OFFSET          # left label
    col_x2 = X_OFFSET + 90     # right label
    for left_lbl, left_val, right_lbl, right_val in info_pairs:
        pdf.set_x(col_x1)
        pdf.info_row(left_lbl, left_val)
        pdf.set_x(col_x2)
        pdf.info_row(right_lbl, right_val)
        pdf.ln()
    pdf.ln(2)

    # === General exam ===
    w = TABLE_W4
    hdr4 = ["项目", "结果", "参考范围", "状态"]

    pdf.table_section("一般检查", hdr4, w, [
        ["血压", "135/88 mmHg", "<130/85 mmHg", "↑偏高"],
        ["静息心率", "82 bpm", "60-100 bpm", "正常"],
        ["视力(左/右)", "4.8 / 4.7", "5.0", "近视"],
        ["听力", "正常", "-", "正常"],
    ])

    # === Blood routine ===
    pdf.table_section("血常规", hdr4, w, [
        ["白细胞 WBC", "6.8 x10^9/L", "3.5-9.5", "正常"],
        ["红细胞 RBC", "5.2 x10^12/L", "4.3-5.8", "正常"],
        ["血红蛋白 Hb", "152 g/L", "130-175", "正常"],
        ["血小板 PLT", "218 x10^9/L", "125-350", "正常"],
        ["中性粒细胞%", "62.3%", "40-75%", "正常"],
        ["淋巴细胞%", "28.5%", "20-50%", "正常"],
    ])

    # === Liver function ===
    pdf.table_section("肝功能", hdr4, w, [
        ["谷丙转氨酶 ALT", "65 U/L", "9-50", "↑偏高"],
        ["谷草转氨酶 AST", "38 U/L", "15-40", "正常"],
        ["谷氨酰转肽酶 GGT", "72 U/L", "10-60", "↑偏高"],
        ["总胆红素 TBIL", "14.2 μmol/L", "3.4-20.5", "正常"],
        ["直接胆红素 DBIL", "4.1 μmol/L", "0-8.6", "正常"],
        ["白蛋白 ALB", "45.3 g/L", "40-55", "正常"],
    ])

    # === Kidney function ===
    pdf.table_section("肾功能", hdr4, w, [
        ["肌酐 Cr", "88 μmol/L", "57-111", "正常"],
        ["尿素氮 BUN", "5.6 mmol/L", "3.1-8.0", "正常"],
        ["尿酸 UA", "510 μmol/L", "208-428", "↑偏高"],
        ["eGFR", "98 mL/min/1.73m²", ">90", "正常"],
    ])

    # === Blood lipids ===
    pdf.table_section("血脂", hdr4, w, [
        ["总胆固醇 TC", "5.8 mmol/L", "<5.2", "↑偏高"],
        ["甘油三酯 TG", "2.4 mmol/L", "<1.7", "↑偏高"],
        ["低密度脂蛋白 LDL-C", "3.8 mmol/L", "<3.4", "↑偏高"],
        ["高密度脂蛋白 HDL-C", "0.95 mmol/L", ">1.04", "↓偏低"],
    ])

    # === Blood glucose ===
    pdf.table_section("血糖", hdr4, w, [
        ["空腹血糖 FPG", "6.0 mmol/L", "3.9-6.1", "边缘偏高"],
        ["糖化血红蛋白 HbA1c", "5.8%", "4.0-6.0%", "边缘偏高"],
    ])

    # === Thyroid ===
    pdf.table_section("甲状腺功能", hdr4, w, [
        ["TSH", "2.35 mIU/L", "0.27-4.20", "正常"],
        ["FT3", "4.8 pmol/L", "3.1-6.8", "正常"],
        ["FT4", "15.2 pmol/L", "12.0-22.0", "正常"],
    ])

    # === Tumor markers ===
    pdf.table_section("肿瘤标志物", hdr4, w, [
        ["CEA", "2.1 ng/mL", "0-5.0", "正常"],
        ["AFP", "3.5 ng/mL", "0-7.0", "正常"],
        ["PSA", "0.8 ng/mL", "0-4.0", "正常"],
    ])

    # === Imaging ===
    pdf.section_title("影像检查")
    pdf.set_font("simhei", size=10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 7, "腹部B超", new_x="LMARGIN", new_y="NEXT")
    pdf.paragraph(
        "肝脏体积增大，实质回声增强、细密，后方回声衰减。"
        "胆囊、胰腺、脾脏、双肾未见明显异常。\n"
        "诊断: 中度脂肪肝。"
    )
    pdf.set_font("simhei", size=10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 7, "心电图", new_x="LMARGIN", new_y="NEXT")
    pdf.paragraph(
        "窦性心律，心率82次/分。偶发室性早搏（约3次/分）。"
        "ST-T无明显改变。"
    )

    # === Urine ===
    pdf.table_section("尿常规", ["项目", "结果", "状态"], TABLE_W3, [
        ["尿蛋白", "阴性 (-)", "正常"],
        ["尿糖", "阴性 (-)", "正常"],
        ["尿潜血", "阴性 (-)", "正常"],
    ])

    # === Family history ===
    pdf.section_title("家族史")
    pdf.paragraph("父亲: 高血压病史15年，58岁时发生脑梗死。")
    pdf.paragraph("母亲: 2型糖尿病，55岁确诊，口服降糖药控制。")

    # === Summary ===
    pdf.section_title("异常指标汇总及建议")
    pdf.set_font("simsun", size=10)
    pdf.set_text_color(40, 40, 40)
    items = [
        "1. 中度脂肪肝（ALT↑、GGT↑ 提示肝脏损伤）——建议消化内科就诊，限酒、控制体重",
        "2. 血脂四项异常（TC↑、TG↑、LDL-C↑、HDL-C↓）——建议心内科就诊，低脂饮食，必要时药物干预",
        "3. 尿酸偏高 510 μmol/L（痛风风险）——建议限制高嘌呤食物及啤酒摄入，多饮水",
        "4. 血压边缘偏高 135/88 mmHg——建议家庭血压监测，低盐饮食，规律运动",
        "5. 血糖边缘偏高（FPG 6.0、HbA1c 5.8%）——建议3个月后复查OGTT，注意母亲糖尿病家族史",
        "6. 偶发室性早搏——建议必要时行24小时动态心电图及心脏超声检查",
        "7. BMI 26.8 超重——建议合理膳食，增加体力活动，目标BMI<24",
    ]
    for item in items:
        pdf.multi_cell(0, 6, item)
        pdf.ln(1)

    # === Signature block ===
    pdf.ln(8)
    pdf.set_font("simsun", size=10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(95, 7, "主检医师:  ________________", new_x="RIGHT")
    pdf.cell(95, 7, "审核医师:  ________________", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.cell(95, 7, "报告日期:  2026年03月10日", new_x="RIGHT")
    pdf.cell(95, 7, "盖章:", new_x="LMARGIN", new_y="NEXT")

    # Save
    pdf.output(str(OUTPUT))
    print(f"Generated: {OUTPUT}")


if __name__ == "__main__":
    build_report()

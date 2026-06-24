import os
import time
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ReportGenerator:
    def __init__(self, report_dir: str | Path) -> None:
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.font_name = self._register_font()

    def generate(self, payload: dict[str, Any]) -> tuple[str, str]:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_id = f"problem_optimization_report_{timestamp}.pdf"
        path = self.report_dir / report_id

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="Universal Problem Optimizer Agent Report",
        )
        styles = self._styles()
        story: list[Any] = []

        story.append(Paragraph("Universal Problem Optimizer Agent", styles["Title"]))
        story.append(Paragraph("通用问题优化智能体求解报告", styles["Subtitle"]))
        story.append(Spacer(1, 8))

        sections = [
            ("用户原始问题", payload["question"]),
            ("任务类型", payload["task_type"]),
            ("问题诊断结果", payload["analysis"]),
            ("优化后的提示词", payload["optimized_prompt"]),
            ("工具调用过程", "\n".join(payload["tool_logs"])),
            ("最终答案", payload["solution"]),
            ("总结与改进方向", "本报告展示了从问题诊断、提示词优化、任务拆解、工具整理到最终答案生成的完整流程。后续可接入更多公开模型、检索工具和领域模板，以提升复杂任务求解质量。"),
        ]

        for title, content in sections[:4]:
            story.extend(self._section(title, content, styles))

        story.extend(self._steps_section(payload["steps"], styles))

        for title, content in sections[4:]:
            story.extend(self._section(title, content, styles))

        doc.build(story)
        return report_id, str(path)

    def _section(self, title: str, content: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
        items: list[Any] = [Spacer(1, 8), Paragraph(title, styles["Heading"])]
        for block in str(content).split("\n"):
            if not block.strip():
                items.append(Spacer(1, 4))
                continue
            items.append(Paragraph(self._escape(block), styles["Body"]))
        return items

    def _steps_section(self, steps: list[dict[str, Any]], styles: dict[str, ParagraphStyle]) -> list[Any]:
        data = [["步骤", "标题", "说明"]]
        for item in steps:
            data.append([str(item.get("step", "")), item.get("title", ""), item.get("description", "")])
        table = Table(data, colWidths=[18 * mm, 42 * mm, 102 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return [Spacer(1, 8), Paragraph("任务拆解过程", styles["Heading"]), table]

    def _styles(self) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "Title": ParagraphStyle("Title", parent=base["Title"], fontName=self.font_name, fontSize=22, leading=28, textColor=colors.HexColor("#111827")),
            "Subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontName=self.font_name, fontSize=12, leading=18, textColor=colors.HexColor("#475569"), alignment=1),
            "Heading": ParagraphStyle("Heading", parent=base["Heading2"], fontName=self.font_name, fontSize=14, leading=20, textColor=colors.HexColor("#1d4ed8"), spaceAfter=6),
            "Body": ParagraphStyle("Body", parent=base["BodyText"], fontName=self.font_name, fontSize=9.5, leading=15, textColor=colors.HexColor("#1f2937")),
        }

    def _register_font(self) -> str:
        candidates = [
            os.getenv("CHINESE_FONT_PATH", ""),
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        ]
        for font_path in candidates:
            if font_path and Path(font_path).exists():
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                    return "ChineseFont"
                except Exception:
                    continue
        # Built-in CID font keeps Chinese reports readable on minimal Linux hosts such as Render.
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"

    @staticmethod
    def _escape(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("  ", "&nbsp;&nbsp;")
        )

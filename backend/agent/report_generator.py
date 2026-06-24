import os
import re
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
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


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

        for number, (title, content) in enumerate(sections[:4], start=1):
            story.extend(self._section(number, title, content, styles))

        story.extend(self._steps_section(5, payload["steps"], styles))

        for number, (title, content) in enumerate(sections[4:], start=6):
            story.extend(self._section(number, title, content, styles))

        doc.build(story)
        return report_id, str(path)

    def _section(self, number: int, title: str, content: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
        items: list[Any] = [Spacer(1, 11), Paragraph(f"{self._chinese_number(number)}、{title}", styles["Heading"])]
        items.extend(self._content_flowables(str(content), styles))
        return items

    def _steps_section(self, number: int, steps: list[dict[str, Any]], styles: dict[str, ParagraphStyle]) -> list[Any]:
        data: list[list[Any]] = [[
            Paragraph("序号", styles["TableHeader"]),
            Paragraph("子任务", styles["TableHeader"]),
            Paragraph("任务说明", styles["TableHeader"]),
        ]]
        for item in steps:
            data.append([
                Paragraph(str(item.get("step", "")), styles["TableCell"]),
                Paragraph(self._escape_plain(str(item.get("title", ""))), styles["TableCell"]),
                Paragraph(self._escape_plain(str(item.get("description", ""))), styles["TableCell"]),
            ])
        table = Table(data, colWidths=[18 * mm, 42 * mm, 102 * mm], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1ed")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1d4338")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c9d9d2")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        return [
            Spacer(1, 11),
            Paragraph(f"{self._chinese_number(number)}、任务拆解过程", styles["Heading"]),
            table,
        ]

    def _content_flowables(self, content: str, styles: dict[str, ParagraphStyle]) -> list[Any]:
        lines = content.replace("\r\n", "\n").split("\n")
        items: list[Any] = []
        bullet_index = 0
        heading_index = 0
        position = 0

        while position < len(lines):
            line = lines[position].strip()
            if not line:
                items.append(Spacer(1, 4))
                bullet_index = 0
                position += 1
                continue

            if self._is_markdown_table(lines, position):
                table_lines: list[str] = []
                while position < len(lines) and lines[position].strip().startswith("|"):
                    table_lines.append(lines[position])
                    position += 1
                items.append(self._markdown_table(table_lines, styles))
                bullet_index = 0
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = self._strip_markdown(heading_match.group(2))
                if level <= 2:
                    heading_index += 1
                    items.append(Paragraph(f"{heading_index}、{heading_text}", styles["Subheading"]))
                else:
                    items.append(Paragraph(f"（{max(heading_index, 1)}）{heading_text}", styles["Subsubheading"]))
                bullet_index = 0
                position += 1
                continue

            bullet_match = re.match(r"^(?:[-*•]\s+)(.+)$", line)
            if bullet_match:
                bullet_index += 1
                text = self._strip_markdown(bullet_match.group(1))
                items.append(Paragraph(f"（{bullet_index}）{text}", styles["Body"]))
                position += 1
                continue

            number_match = re.match(r"^(\d+)[.、]\s*(.+)$", line)
            if number_match:
                items.append(Paragraph(f"{number_match.group(1)}、{self._strip_markdown(number_match.group(2))}", styles["Body"]))
                bullet_index = 0
                position += 1
                continue

            items.append(Paragraph(self._strip_markdown(line), styles["Body"]))
            bullet_index = 0
            position += 1

        return items

    def _markdown_table(self, lines: list[str], styles: dict[str, ParagraphStyle]) -> Table:
        rows = [self._table_cells(line) for line in lines if not self._is_table_divider(line)]
        data = [
            [Paragraph(self._escape_plain(cell), styles["TableHeader" if row_index == 0 else "TableCell"]) for cell in row]
            for row_index, row in enumerate(rows)
        ]
        width = 162 * mm / max(len(data[0]), 1)
        table = Table(data, colWidths=[width] * len(data[0]), repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1ed")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#c9d9d2")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    def _styles(self) -> dict[str, ParagraphStyle]:
        base = getSampleStyleSheet()
        return {
            "Title": ParagraphStyle("Title", parent=base["Title"], fontName=self.font_name, fontSize=21, leading=30, textColor=colors.HexColor("#1d3830"), alignment=1),
            "Subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontName=self.font_name, fontSize=10.5, leading=17, textColor=colors.HexColor("#61736a"), alignment=1),
            "Heading": ParagraphStyle("Heading", parent=base["Heading2"], fontName=self.font_name, fontSize=14, leading=22, textColor=colors.HexColor("#1d5c4a"), spaceBefore=2, spaceAfter=8),
            "Subheading": ParagraphStyle("Subheading", parent=base["Heading3"], fontName=self.font_name, fontSize=11.5, leading=19, textColor=colors.HexColor("#284b3e"), spaceBefore=6, spaceAfter=5),
            "Subsubheading": ParagraphStyle("Subsubheading", parent=base["BodyText"], fontName=self.font_name, fontSize=10.5, leading=18, textColor=colors.HexColor("#284b3e"), spaceBefore=5, spaceAfter=3),
            "Body": ParagraphStyle("Body", parent=base["BodyText"], fontName=self.font_name, fontSize=10, leading=18, textColor=colors.HexColor("#2b3832"), spaceAfter=3),
            "TableHeader": ParagraphStyle("TableHeader", parent=base["BodyText"], fontName=self.font_name, fontSize=9.5, leading=14, textColor=colors.HexColor("#1d4338"), alignment=1),
            "TableCell": ParagraphStyle("TableCell", parent=base["BodyText"], fontName=self.font_name, fontSize=9.2, leading=14, textColor=colors.HexColor("#2b3832")),
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
    def _chinese_number(number: int) -> str:
        values = ["", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
        return values[number] if 0 < number < len(values) else str(number)

    @staticmethod
    def _is_markdown_table(lines: list[str], position: int) -> bool:
        return position + 1 < len(lines) and lines[position].strip().startswith("|") and ReportGenerator._is_table_divider(lines[position + 1])

    @staticmethod
    def _is_table_divider(line: str) -> bool:
        return bool(re.match(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$", line))

    @staticmethod
    def _table_cells(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip().strip("|").split("|")]

    def _strip_markdown(self, text: str) -> str:
        cleaned = re.sub(r"`([^`]+)`", r"\1", text)
        cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
        cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
        return self._escape_plain(cleaned)

    @staticmethod
    def _escape_plain(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("  ", "&nbsp;&nbsp;")
        )

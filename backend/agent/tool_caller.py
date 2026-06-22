import re
from typing import Any


class ToolCaller:
    """Lightweight local tools used by the agent workflow."""

    def summarize_text(self, text: str, max_chars: int = 500) -> str:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if len(cleaned) <= max_chars:
            return cleaned
        return f"{cleaned[:max_chars].rstrip()}..."

    def extract_keywords(self, text: str, top_k: int = 8) -> list[str]:
        tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", text)
        stop_words = {"一个", "关于", "需要", "输出", "问题", "方案", "步骤", "the", "and", "with"}
        scores: dict[str, int] = {}
        for token in tokens:
            if token.lower() in stop_words:
                continue
            scores[token] = scores.get(token, 0) + 1
        return [word for word, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]]

    def format_steps_markdown(self, steps: list[dict[str, Any]]) -> str:
        lines = []
        for item in steps:
            lines.append(f"{item.get('step')}. **{item.get('title')}**：{item.get('description')}")
        return "\n".join(lines)

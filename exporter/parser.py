import re
from logger import get_logger

logger = get_logger(__name__)

def parse_inline(text: str) -> list:
    """
    인라인 요소 파싱
    **볼드** → {"text": str, "bold": True}
    반환: [{"text": str, "bold": bool}, ...]
    """
    runs = []
    pattern = re.compile(r'\*\*(.+?)\*\*')
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            runs.append({"text": text[last:m.start()], "bold": False})
        runs.append({"text": m.group(1), "bold": True})
        last = m.end()
    if last < len(text):
        runs.append({"text": text[last:], "bold": False})
    return runs if runs else [{"text": text, "bold": False}]


def parse_markdown(text: str) -> list:
    """
    마크다운 텍스트를 블록 리스트로 파싱
    반환: [{"type": str, "runs": list, "raw": str}, ...]

    type 종류:
    - h1, h2, h3 : 소제목
    - bullet      : 불릿/체크리스트
    - hashtag     : 해시태그 줄
    - p           : 일반 문단
    - empty       : 빈 줄
    """
    blocks = []

    for line in text.split("\n"):
        s = line.rstrip()

        if s.startswith("### "):
            blocks.append({"type": "h3", "runs": parse_inline(s[4:]), "raw": s})

        elif s.startswith("## "):
            blocks.append({"type": "h2", "runs": parse_inline(s[3:]), "raw": s})

        elif s.startswith("# "):
            blocks.append({"type": "h1", "runs": parse_inline(s[2:]), "raw": s})

        elif s.startswith("#") and " #" in s:
            # 해시태그 줄 (#상표출원 #마크픽 ...)
            blocks.append({"type": "hashtag", "runs": [{"text": s, "bold": False}], "raw": s})

        elif re.match(r'^[-*]\s+', s):
            content = re.sub(r'^[-*]\s+', '', s)
            blocks.append({"type": "bullet", "runs": parse_inline(content), "raw": s})

        elif s.startswith("✔"):
            blocks.append({"type": "bullet", "runs": parse_inline(s), "raw": s})

        elif s == "":
            blocks.append({"type": "empty", "runs": [], "raw": ""})

        else:
            blocks.append({"type": "p", "runs": parse_inline(s), "raw": s})

    logger.debug(f"마크다운 파싱 완료 - {len(blocks)}개 블록")
    return blocks
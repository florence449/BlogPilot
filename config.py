from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

# API 키
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 서비스 정보
MARKPICK_INFO = """
- 서비스명: 마크픽(MarkPick)
- 서비스 내용: AI 기반 유사상표 검색
- 관련 브랜드: 마크픽, 마크뷰, 마크클라우드, 정상특허법률사무소
"""

EVENT_INFO = ""

# 경로
BASE_DIR = Path(__file__).parent
FILES_DIR = BASE_DIR / "files"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "log"
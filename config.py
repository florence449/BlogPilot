from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

# ========================
# GEMINI 설정
# ========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-lite"

# ========================
# 경로
# ========================
BASE_DIR = Path(__file__).parent
FILES_DIR = BASE_DIR / "files"
DATA_DIR = FILES_DIR / "data"
REFERENCE_DIR = FILES_DIR / "reference"
TEMPLATES_DIR = FILES_DIR / "templates"
IMAGES_DIR = FILES_DIR / "images"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "log"

# 필요한 폴더 자동 생성
for _dir in [DATA_DIR, REFERENCE_DIR, TEMPLATES_DIR, IMAGES_DIR, OUTPUT_DIR, LOG_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
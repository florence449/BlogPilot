import csv
import re
import json
from config import DATA_DIR, REFERENCE_DIR
from logger import get_logger
from generator.schema import BlogPost
from pydantic import ValidationError

logger = get_logger(__name__)


# ========================
# JSON 출력 프롬프트
# ========================

BLOG_PROMPT_TEMPLATE = """\
당신은 {blog_name}의 블로그 콘텐츠 작성 전문가입니다.

다음 주제로 네이버 블로그 포스트를 작성하고, 아래 JSON 스키마 형식으로만 출력하세요.

[입력 주제]
{topic}

{reference_section}
[서비스 정보]
{service_info}

{event_section}
---

[JSON 출력 스키마]
{{
  "title": "포스트 제목 (핵심 키워드 포함, 30자 이내)",
  "intro": "서문 전체 텍스트 (훅 3~4문장 + 지역/상황 소개 3~4문장, 줄바꿈은 \\\\n 사용)",
  "body": [
    {{
      "heading": "본론1 소제목",
      "content": "본론1 내용 (3~4문장 이상, 줄바꿈은 \\\\n 사용)"
    }},
    {{
      "heading": "본론2 소제목",
      "content": "본론2 내용 (3~4문장 이상, 줄바꿈은 \\\\n 사용)"
    }},
    {{
      "heading": "본론3 소제목",
      "content": "본론3 내용 (3~4문장 이상, 줄바꿈은 \\\\n 사용)"
    }}
  ],
  "conclusion": "결론 전체 텍스트 (상표출원 필요성 5~6문장, 줄바꿈은 \\\\n 사용)",
  "cta": "CTA 한 줄 (서비스 이점 + 행동 유도)",
  "event": "이벤트 문구 한 줄 (이벤트 없으면 빈 문자열 \\"\\")",
  "hashtags": ["#해시태그1", "#해시태그2", "... 15~20개"]
}}

[글 작성 규칙]

내용 규칙:
- 참조 정보가 있으면 반드시 근거로 활용하고 출처를 괄호로 표기 (예: (출처: 동남지방통계청 2025))
- 가상의 카페명, 브랜드명 등 증명 불가한 사례는 절대 포함하지 말 것
- 구체적 사례가 없으면 일반적인 상황 설명으로 대체
- 전체 800~1000자 내외, 서비스 홍보는 전체의 20% 이내

문체 규칙:
- 문장은 짧고 간결하게
- 한 줄 30자 내외 (\\\\n으로 분리)
- 친근하지만 전문적, 독자는 사업자/창업자

SEO 규칙:
- title에 핵심 키워드 포함
- intro 초반에 핵심 정의 포함
- body에 Q&A 형식 1개 이상 포함
- 이모지 적절히 활용 (✔ 📊 🛡 📌 등)
- 볼드 강조는 **텍스트** 형식 사용

출력 규칙:
- JSON만 출력하고 다른 설명, 마크다운 코드블록(```), 서문 없이 순수 JSON만 출력할 것
"""


# ========================
# CSV 로더
# ========================

def load_blog(blog_code: str) -> dict:
    path = DATA_DIR / "blog.csv"
    if not path.exists():
        logger.warning(f"블로그 정보 파일 없음: {path}")
        return {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["code"] == blog_code:
                logger.debug(f"블로그 로드: {row['name']}")
                return row
    logger.warning(f"블로그 코드 없음: {blog_code}")
    return {}


def load_service(service_code: str) -> str:
    path = DATA_DIR / "service.csv"
    if not path.exists():
        logger.warning(f"서비스 정보 파일 없음: {path}")
        return ""
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["code"] == service_code:
                logger.debug(f"서비스 로드: {row['name']}")
                return f"- {row['name']}: {row['description']}"
    logger.warning(f"서비스 코드 없음: {service_code}")
    return ""


def load_event(event_code: str) -> str:
    if not event_code or not event_code.strip():
        return ""
    path = DATA_DIR / "event.csv"
    if not path.exists():
        logger.warning(f"이벤트 정보 파일 없음: {path}")
        return ""
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["code"] == event_code:
                logger.debug(f"이벤트 로드: {row['code']}")
                return row["description"]
    logger.warning(f"이벤트 코드 없음: {event_code}")
    return ""


# ========================
# 섹션 빌더
# ========================

def build_reference_section(reference_info: str) -> str:
    if not reference_info.strip():
        return ""
    return f"[참조 정보 - 최신 뉴스/데이터 - 이 내용을 근거로 활용하세요]\n{reference_info}\n"


def build_event_section(event_info: str) -> str:
    if not event_info.strip():
        return ""
    return f"[현재 진행 중인 이벤트]\n{event_info}\nevent 필드에 한 줄로 작성하세요.\n"


# ========================
# JSON 파서 (Pydantic)
# ========================

def parse_blog_json(raw: str) -> BlogPost:
    """
    LLM 출력 문자열 → BlogPost (Pydantic 검증 포함)
    - 코드블록 자동 제거
    - ValidationError 발생 시 필드별 오류 상세 로깅
    """
    # 코드블록 제거
    cleaned = re.sub(r"^```[a-z]*\n?", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\n?```$", "", cleaned.strip(), flags=re.MULTILINE)
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패 (앞 300자):\n{cleaned[:300]}")
        raise ValueError(f"LLM 출력이 유효한 JSON이 아닙니다: {e}") from e

    try:
        post = BlogPost.model_validate(data)
    except ValidationError as e:
        logger.error(f"BlogPost 검증 실패:\n{e}")
        raise ValueError(f"BlogPost 스키마 검증 오류: {e}") from e

    return post


# ========================
# 프롬프트 빌더
# ========================

def build_prompt(topic: str, blog_code: str) -> str:
    blog = load_blog(blog_code)
    if not blog:
        raise ValueError(f"블로그 코드를 찾을 수 없습니다: {blog_code}")

    safe_topic = re.sub(r'[^\w가-힣]', '_', topic)
    ref_path = REFERENCE_DIR / f"{safe_topic}.txt"
    if ref_path.exists():
        reference_info = ref_path.read_text(encoding="utf-8")
        logger.info(f"참조 파일 로드: {ref_path.name}")
    else:
        logger.warning(f"참조 파일 없음: {ref_path.name}")
        reference_info = ""

    service_info = load_service(blog["service_code"])
    event_info   = load_event(blog.get("event_code", ""))

    prompt = BLOG_PROMPT_TEMPLATE.format(
        blog_name=blog["name"],
        topic=topic,
        reference_section=build_reference_section(reference_info),
        service_info=service_info,
        event_section=build_event_section(event_info),
    )

    logger.debug(f"프롬프트 생성 완료 - {blog['name']} / {topic} / {len(prompt)}자")
    return prompt
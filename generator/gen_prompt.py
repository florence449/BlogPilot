import csv
import re
from config import DATA_DIR,REFERENCE_DIR
from logger import get_logger

logger = get_logger(__name__)

BLOG_PROMPT_TEMPLATE = """
당신은 {blog_name}의 블로그 콘텐츠 작성 전문가입니다.

다음 주제로 네이버 블로그 포스트를 작성해주세요.

[입력 주제]
{topic}

{reference_section}

[서비스 정보]
{service_info}

{event_section}

[글 작성 규칙]

구조:
1. 도입부
   - 독자 공감을 끌어내는 훅 (3~4문장)
      - 도입부는 독자의 상황을 질문 형태로 시작할 것
   - 지역 및 지역 상권의 특징 (3~4문장)
2. 본론 - 주제 관련 정보 3~4가지
   - 참조 정보가 제공된 경우
      - 본문 내용은 반드시 참조 정보 기반으로 작성할 것
      - 참조 정보에 없는 수치나 정보를 생성하 않을 것
   - 가상의 카페명, 브랜드명 등 증명 불가한 사례는 절대 포함하지 말 것
   - 구체적 사례가 없으면 일반적인 상황 설명으로 대체할 것
   - 하나의 정보당 2개 이상 문단으로 작성할 것
3. 상표출원이 필요한 이유 - 본론과 자연스럽게 연결 (5~6문장)
4. 서비스 이점 소개 - 간결하게 3줄 이내
5. CTA - 2~3 줄로 간결하게
   - 서비스 행동을 유도하는 문장을 작성할 것
   - 서비스의 기능을 1개 이상 포함할 것
6. 해시태그 - 8~12개

길이:
- 전체 800~1000자 내외로 간결하게
- 서비스 홍보는 글 전체의 20% 이내로 제한

문체 규칙 (매우 중요):
- 문장을 짧고 간결하게 작성할 것
- 문장이 바뀐 경우 문장 줄바꿈을 할 것
- 한 문단은 2~3 문장으로 구성할 것
- 한 문단이 끝나면 한줄을 비울 것
- 한줄을 25~35자로 배치하며, 문장이 그보다 길어질 경우 중간에 줄바꿈을 통해 내용을 분리할 것

형식 규칙:
- 소제목은 ## 또는 ### 사용
- 볼드 강조는 **텍스트** 형식 사용
- 체크리스트는 ✔ 기호 사용
- 이모지 적절히 활용 (✔ 📊 🛡 📌 등)
- 해시태그는 마지막에 한 줄로 나열
- 각 섹션 사이 빈 줄 삽입
- 정확한 수치는 출처를 괄호로 표기할 것 (예: 사업체 수 76% 증가(출처: 동남지방통계청 2025))

톤:
- 친근하지만 전문적
- 독자가 사업자/창업자임을 가정
- 문제 제기 → 공감 → 해결책 순서
- 추상적인 표현 대신 구체적인 상황 설명을 사용할 것
- 독자가 바로 이해할 수 있는 현실적인 표현을 사용할 것
- 불필요한 가상의 사례나 브랜드는 만들지 말 것

SEO/AEO 최적화:
- 주제와 관련된 핵심 키워드 2~3개를 선정할 것
   - 제목에 핵심 키워드 포함
   - 핵심 키워드 중 1개는 본문 첫 문단에 포함할 것
   - 핵심 키워드를 본문 내에서 2~4회 자연스럽게 포함
- 본문 초반에 핵심 정의 포함
- Q&A 형식 1개 이상 포함
- 간결한 인용 가능한 문장 사용

추가정보:
- 올해는 2026년임.

마크다운 형식으로만 출력하세요. 다른 설명 없이 블로그 글만 작성하세요.
"""


# ========================
# CSV 로더
# ========================

def load_blog(blog_code: str) -> dict:
    """blog.csv에서 블로그 정보 로드"""
    path = DATA_DIR / "blog.csv"
    if not path.exists():
        logger.warning(f"블로그 정보 파일 없음: {path}")
        return {}

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["code"] == blog_code:
                logger.debug(f"블로그 로드: {row['name']}")
                return row

    logger.warning(f"블로그 코드 없음: {blog_code}")
    return {}


def load_service(service_code: str) -> str:
    """service.csv에서 특정 서비스 정보 로드"""
    path = DATA_DIR / "service.csv"
    if not path.exists():
        logger.warning(f"서비스 정보 파일 없음: {path}")
        return ""

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["code"] == service_code:
                logger.debug(f"서비스 로드: {row['name']}")
                return f"- {row['name']}: {row['description']}"

    logger.warning(f"서비스 코드 없음: {service_code}")
    return ""


def load_event(event_code: str) -> str:
    """event.csv에서 특정 이벤트 로드"""
    if not event_code or not event_code.strip():
        return ""

    path = DATA_DIR / "event.csv"
    if not path.exists():
        logger.warning(f"이벤트 정보 파일 없음: {path}")
        return ""

    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
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
    return f"[현재 진행 중인 이벤트]\n{event_info}\n이벤트 내용을 CTA 직전에 자연스럽게 한 줄로 삽입하세요.\n"


# ========================
# 프롬프트 빌더
# ========================

def build_prompt(topic: str, blog_code: str) -> str:
    blog = load_blog(blog_code)
    if not blog:
        raise ValueError(f"블로그 코드를 찾을 수 없습니다: {blog_code}")

    # 참조 정보가 없으면 주제명으로 reference 파일 자동 매핑
    safe_topic = re.sub(r'[^\w가-힣]', '_', topic)
    ref_path = REFERENCE_DIR / f"{safe_topic}.txt"
    if ref_path.exists():
        reference_info = ref_path.read_text(encoding="utf-8")
        logger.info(f"참조 파일 자동 로드: {ref_path.name}")
    else:
        logger.warning(f"참조 파일 없음: {ref_path.name}")
        reference_info= ""

    service_info = load_service(blog["service_code"])
    event_info = load_event(blog.get("event_code", ""))

    prompt = BLOG_PROMPT_TEMPLATE.format(
        blog_name=blog["name"],
        topic=topic,
        reference_section=build_reference_section(reference_info),
        service_info=service_info,
        event_section=build_event_section(event_info)
    )

    logger.debug(f"프롬프트 생성 완료 - 블로그: {blog['name']}, 주제: {topic}, 길이: {len(prompt)}자")
    return prompt
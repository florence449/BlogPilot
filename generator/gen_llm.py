from google import genai
from config import GEMINI_API_KEY, MODEL_NAME
from logger import get_logger
from generator.gen_prompt import build_prompt
import re

logger = get_logger(__name__)

def gen_blog(topic: str, blog_code: str) -> str:
    """
    주제, 블로그 코드, 참조 정보를 받아 블로그 마크다운 텍스트 반환
    """
    logger.info(f"블로그 생성 시작 - 주제: {topic}, 블로그: {blog_code}")

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = build_prompt(topic, blog_code)

    logger.debug(f"Gemini API 호출 - 모델: {MODEL_NAME}")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        content = response.text
        content = content.replace("\u200b", "")
        content = content.replace("\xa0", " ")
        content = re.sub(r'[ ]{2,}', ' ', content)
        logger.info(f"블로그 생성 완료 - {len(content)}자")
        return content

    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        raise
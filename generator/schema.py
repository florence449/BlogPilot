"""
BlogPost 스키마 (Pydantic v2)
- LLM JSON 출력과 1:1 대응
- model_validate()로 파싱 + 타입 검증 자동 처리
"""
from pydantic import BaseModel, Field, field_validator


class BodySection(BaseModel):
    """본론 1개 섹션"""
    heading: str = Field(..., description="소제목")
    content: str = Field(..., description="본문 (\\n으로 줄바꿈)")


class BlogPost(BaseModel):
    """
    구조화된 블로그 포스트 전체

    섹션 순서:
        title → intro → body(3) → conclusion → cta → event → hashtags
    """
    title:      str              = Field(..., description="포스트 제목")
    intro:      str              = Field(..., description="서문")
    body:       list[BodySection]= Field(..., min_length=1, description="본론 섹션 리스트")
    conclusion: str              = Field(..., description="결론 (상표출원 필요성)")
    cta:        str              = Field(..., description="CTA 한 줄")
    event:      str              = Field("",  description="이벤트 문구 (없으면 빈 문자열)")
    hashtags:   list[str]        = Field(..., min_length=1, description="해시태그 리스트")

    # 메타 — LLM 생성 이후 exporter에서 채움 (LLM 출력에 없는 필드)
    blog_code:  str              = Field("", exclude=True)
    topic:      str              = Field("", exclude=True)

    @field_validator("hashtags")
    @classmethod
    def ensure_hash_prefix(cls, tags: list[str]) -> list[str]:
        """# 없는 태그에 자동으로 # 붙임"""
        return [t if t.startswith("#") else f"#{t}" for t in tags]

    @field_validator("body")
    @classmethod
    def ensure_body_not_empty(cls, sections: list[BodySection]) -> list[BodySection]:
        for s in sections:
            if not s.heading.strip() or not s.content.strip():
                raise ValueError("body 섹션의 heading과 content는 비어있을 수 없습니다.")
        return sections
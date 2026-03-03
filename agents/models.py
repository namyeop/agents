from typing import List, Dict, Literal, Optional

from pydantic import BaseModel, Field, conint, HttpUrl


class ResearchSource(BaseModel):
    title: str = Field(..., min_length=1, description="Source page title")
    url: str
    snippet: str = Field(..., min_length=1, description="Short supporting excerpt")


class SubjectInsight(BaseModel):
    keyword: str = Field(..., min_length=1, description="Relevant keyword or subtopic")
    description: str = Field(
        ..., min_length=1, description="Why it matters for virality"
    )
    usage_suggestion: str = Field(
        ..., min_length=1, description="How to leverage in threads"
    )


class SubjectResearch(BaseModel):
    topic: str = Field(..., min_length=1)
    insights: List[SubjectInsight] = Field(
        default_factory=list, description="List of researched keywords/subtopics"
    )
    sources: List[ResearchSource] = Field(
        default_factory=list, description="Cited sources used during research"
    )
    language: str = Field("ko", description="Language of research output")
    summary: Optional[str] = Field(
        default=None, description="Concise summary of key takeaways"
    )


class MemeItem(BaseModel):
    meme: str = Field(..., min_length=1, description="Meme or cultural reference")
    description: str = Field(
        ..., min_length=1, description="Meaning/context of the meme"
    )
    usage_suggestion: str = Field(
        ..., min_length=1, description="Actionable way to use in thread"
    )
    example: Optional[str] = Field(
        default=None, description="Optional example line or phrasing"
    )


class MemeResearch(BaseModel):
    topic: str = Field(..., min_length=1)
    memes: List[MemeItem] = Field(
        default_factory=list, description="Collected memes/keywords with guidance"
    )
    sources: List[ResearchSource] = Field(
        default_factory=list, description="Cited sources used during research"
    )
    language: str = Field("ko", description="Language of research output")


class ViralBreakdown(BaseModel):
    hook: conint(ge=0, le=100)
    novelty: conint(ge=0, le=100)
    clarity: conint(ge=0, le=100)
    shareability: conint(ge=0, le=100)
    comment_bait: conint(ge=0, le=100)


class ViralScore(BaseModel):
    total: conint(ge=0, le=100)
    breakdown: ViralBreakdown
    rationale: str
    improvements: List[str]


class ThreadCandidate(BaseModel):
    id: Literal["conservative", "balanced", "aggressive"]
    title: str
    body: List[str] = Field(default_factory=list)
    memes: List[str] = Field(default_factory=list)
    cta: str
    platform: str


class Review(BaseModel):
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    rewrites: Dict[str, str]
    final_recommendation: str
    score_review: str


class FinalOutput(BaseModel):
    topic: str
    target_audience: str
    platform: str
    candidates: List[ThreadCandidate]
    scores: List[ViralScore]
    review: Review

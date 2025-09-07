from typing import List, Dict, Literal

from pydantic import BaseModel, Field, conint


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

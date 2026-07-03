from typing import Literal

from pydantic import BaseModel, Field


class AssetValidationIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    industry_category: str = Field("", max_length=100)
    domain_stems: list[str] = Field(default_factory=list, description="可选的自定义域名前缀")


class DomainCheck(BaseModel):
    domain: str
    source: Literal["full_pinyin", "initials", "custom"]
    status: Literal["available", "registered", "unknown"]
    status_text: str


class ExternalRiskCheck(BaseModel):
    provider: str
    status: Literal["not_configured", "pending", "completed", "error"]
    risk_level: Literal["unknown", "low", "medium", "high"] = "unknown"
    message: str


class AssetValidationOut(BaseModel):
    name: str
    domains: list[DomainCheck]
    trademark: ExternalRiskCheck
    social_media: ExternalRiskCheck
    disclaimer: str

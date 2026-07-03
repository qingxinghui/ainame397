import asyncio
import re
from dataclasses import dataclass

import settings
from schemas.validation_schemas import (
    AssetValidationIn,
    AssetValidationOut,
    DomainCheck,
    ExternalRiskCheck,
)


@dataclass(frozen=True)
class WhoisRule:
    host: str
    available_markers: tuple[str, ...]


WHOIS_RULES = {
    ".com": WhoisRule("whois.verisign-grs.com", ("no match for",)),
    ".cn": WhoisRule("whois.cnnic.cn", ("no matching record", "no entries found")),
    ".ai": WhoisRule("whois.nic.ai", ("domain not found", "not found")),
}


def _safe_stem(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9-]", "", value)
    return re.sub(r"-{2,}", "-", value).strip("-")[:55]


def build_domain_stems(name: str, custom: list[str]) -> list[tuple[str, str]]:
    """生成全拼和首字母；自定义前缀会一并去重。"""
    try:
        from pypinyin import Style, lazy_pinyin

        syllables = lazy_pinyin(name, style=Style.NORMAL, errors="ignore")
    except ImportError:
        syllables = []

    candidates: list[tuple[str, str]] = []
    full_pinyin = _safe_stem("".join(syllables))
    initials = _safe_stem("".join(part[0] for part in syllables if part))
    if full_pinyin:
        candidates.append((full_pinyin, "full_pinyin"))
    if initials and initials != full_pinyin:
        candidates.append((initials, "initials"))
    for value in custom:
        stem = _safe_stem(value)
        if stem:
            candidates.append((stem, "custom"))

    # 英文品牌名本身也可直接成为域名前缀。
    raw_stem = _safe_stem(name)
    if raw_stem:
        candidates.insert(0, (raw_stem, "custom"))

    seen: set[str] = set()
    return [(stem, source) for stem, source in candidates if not (stem in seen or seen.add(stem))][:4]


async def _query_whois(domain: str, rule: WhoisRule) -> tuple[str, str]:
    writer = None
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(rule.host, 43), timeout=4)
        writer.write(f"{domain}\r\n".encode("ascii"))
        await writer.drain()
        response = (await asyncio.wait_for(reader.read(200_000), timeout=7)).decode("utf-8", errors="ignore").lower()
        if any(marker in response for marker in rule.available_markers):
            return "available", "可注册"
        if response.strip():
            return "registered", "已注册"
        return "unknown", "未获得有效响应"
    except (asyncio.TimeoutError, OSError):
        return "unknown", "查询超时或注册局暂不可用"
    finally:
        if writer:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass


async def validate_assets(data: AssetValidationIn) -> AssetValidationOut:
    stems = build_domain_stems(data.name, data.domain_stems)
    jobs: list[tuple[str, str, asyncio.Task]] = []
    for stem, source in stems:
        for suffix, rule in WHOIS_RULES.items():
            domain = f"{stem}{suffix}"
            jobs.append((domain, source, asyncio.create_task(_query_whois(domain, rule))))

    domains = []
    for domain, source, task in jobs:
        status, status_text = await task
        domains.append(DomainCheck(domain=domain, source=source, status=status, status_text=status_text))

    trademark = ExternalRiskCheck(
        provider="企查查/天眼查",
        status="not_configured",
        message="尚未配置企业数据平台 API，当前不输出虚构的商标风险结论。",
    )
    social_media = ExternalRiskCheck(
        provider="第三方社交媒体数据平台",
        status="not_configured",
        message="尚未配置付费社交媒体数据接口，暂不执行公众号、抖音和小红书大 V 防重名查询。",
    )

    return AssetValidationOut(
        name=data.name,
        domains=domains,
        trademark=trademark,
        social_media=social_media,
        disclaimer="域名状态来自注册局 WHOIS 的即时响应，仅供初筛；购买前请在域名注册商再次确认。",
    )

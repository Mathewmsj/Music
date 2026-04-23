import json
import re

from app.http_client import get_json, get_text
from app.models import ChartPayload, ChartSong

# Apple Marketing Tools RSS（公开 JSON）
# most-played: 热门
# new-music: 新歌
RSS_HOT_CN = "https://rss.applemarketingtools.com/api/v2/cn/music/most-played/100/songs.json"
RSS_NEW_CN = "https://rss.applemarketingtools.com/api/v2/cn/music/new-music/100/songs.json"

# 你提供的网页（作为兜底/对照）
PLAYLIST_WEEKLY_CN = "https://music.apple.com/cn/playlist/%E6%AF%8F%E5%91%A8%E7%83%AD%E9%97%A8-100-%E9%A6%96-%E4%B8%AD%E5%9B%BD%E5%A4%A7%E9%99%86/pl.939cf56e73c44970b81fd9648f859223"


def _from_rss_payload(
    raw: object, *, chart_name: str, chart_type: str, limit: int = 100
) -> ChartPayload:
    platform = "Apple Music"
    # 当前 RSS URL 固定为 …/100/songs.json，单源最多 100 条
    cap = min(max(limit, 1), 100)
    if not isinstance(raw, dict):
        return ChartPayload(
            platform=platform,
            chart_name=chart_name,
            chart_type=chart_type,
            fetched_ok=False,
            error="RSS 响应格式异常",
        )
    feed = raw.get("feed") or {}
    results = feed.get("results") or []
    songs: list[ChartSong] = []
    for i, item in enumerate(results[:cap], start=1):
        if not isinstance(item, dict):
            continue
        title = (item.get("name") or "").strip()
        artist = (item.get("artistName") or "").strip()
        if title:
            songs.append(
                ChartSong(
                    rank=i,
                    title=title,
                    artist=artist or "未知艺人",
                    platform=platform,
                    chart_name=chart_name,
                )
            )
    if not songs:
        return ChartPayload(
            platform=platform,
            chart_name=chart_name,
            chart_type=chart_type,
            fetched_ok=False,
            error="RSS 结果为空",
        )
    return ChartPayload(
        platform=platform,
        chart_name=chart_name,
        chart_type=chart_type,
        fetched_ok=True,
        songs=songs,
    )


def _try_parse_ld_json(html: str) -> list[dict]:
    # 兜底：部分 Apple Music 页面包含 JSON-LD
    m = re.search(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return []
    blob = m.group(1).strip()
    try:
        data = json.loads(blob)
    except Exception:
        return []
    items = []
    if isinstance(data, dict):
        # 常见结构：itemListElement
        items = data.get("itemListElement") or []
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        inner = it.get("item") or {}
        if isinstance(inner, dict):
            out.append(inner)
    return out


async def _apple_playlist_fallback(chart_name: str, chart_type: str, *, limit: int = 100) -> ChartPayload:
    platform = "Apple Music"
    try:
        html = await get_text(PLAYLIST_WEEKLY_CN, headers={"Referer": "https://music.apple.com/"})
        items = _try_parse_ld_json(html)
        songs: list[ChartSong] = []
        cap = min(max(limit, 1), 100)
        for i, it in enumerate(items[:cap], start=1):
            title = (it.get("name") or "").strip()
            by = it.get("byArtist") or it.get("author") or {}
            artist = ""
            if isinstance(by, dict):
                artist = (by.get("name") or "").strip()
            if title:
                songs.append(
                    ChartSong(
                        rank=i,
                        title=title,
                        artist=artist or "未知艺人",
                        platform=platform,
                        chart_name=chart_name,
                        extra="playlist_fallback",
                    )
                )
        if songs:
            return ChartPayload(
                platform=platform,
                chart_name=chart_name,
                chart_type=chart_type,
                fetched_ok=True,
                songs=songs,
            )
        return ChartPayload(
            platform=platform,
            chart_name=chart_name,
            chart_type=chart_type,
            fetched_ok=False,
            error="页面兜底解析不到曲目（建议使用 RSS 方案）",
        )
    except Exception as e:
        return ChartPayload(
            platform=platform,
            chart_name=chart_name,
            chart_type=chart_type,
            fetched_ok=False,
            error=str(e),
        )


async def fetch_apple_hot(*, limit: int = 100) -> ChartPayload:
    try:
        raw = await get_json(RSS_HOT_CN, headers={"Referer": "https://music.apple.com/"})
        return _from_rss_payload(
            raw, chart_name="中国大陆 · 热门 100（RSS）", chart_type="hot", limit=limit
        )
    except Exception:
        return await _apple_playlist_fallback("中国大陆 · 每周热门 100（页面兜底）", "hot", limit=limit)


async def fetch_apple_new(*, limit: int = 100) -> ChartPayload:
    try:
        raw = await get_json(RSS_NEW_CN, headers={"Referer": "https://music.apple.com/"})
        return _from_rss_payload(
            raw, chart_name="中国大陆 · 新歌 100（RSS）", chart_type="new", limit=limit
        )
    except Exception as e:
        return ChartPayload(
            platform="Apple Music",
            chart_name="中国大陆 · 新歌 100（RSS）",
            chart_type="new",
            fetched_ok=False,
            error=str(e),
        )


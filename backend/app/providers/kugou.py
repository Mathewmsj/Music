import re

from app.http_client import get_text
from app.kugou_fetch import fetch_kugou_rank_songs
from app.models import ChartPayload, ChartSong

HOT_RANK_ID = 8888
# m 站「新歌榜」rankid（与 rank/list 一致）；旧 52766 在 rank/info 上常无数据
NEW_RANK_ID = 74534


async def _kugou_rank_html_fallback(
    rank_id: int, chart_name: str, chart_type: str, *, limit: int = 100
) -> ChartPayload:
    """网页兜底（首屏条目较少）。"""
    platform = "酷狗音乐"
    url = f"https://www.kugou.com/yy/rank/home/1-{rank_id}.html?from=rank"
    html = await get_text(url, headers={"Referer": "https://www.kugou.com/"})
    songs: list[ChartSong] = []
    titles = re.findall(r'<li[^>]+title="([^"]+)"', html)
    for i, t in enumerate(titles[:limit], start=1):
        t = (t or "").strip()
        if not t:
            continue
        if " - " in t:
            artist, name = t.split(" - ", 1)
        else:
            artist, name = "", t
        name = name.strip()
        artist = artist.strip()
        if not name:
            continue
        songs.append(
            ChartSong(
                rank=i,
                title=name,
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
            error="页面解析不到曲目（可能页面结构变更）",
        )
    return ChartPayload(
        platform=platform,
        chart_name=chart_name,
        chart_type=chart_type,
        fetched_ok=True,
        songs=songs[:limit],
    )


async def _kugou_rank(rank_id: int, chart_name: str, chart_type: str, *, limit: int = 100) -> ChartPayload:
    """优先 m 站 API 翻页，取前至多 limit 首（若接口中断则取已有）。"""
    platform = "酷狗音乐"
    need = max(1, limit)
    max_pages = max(1, min(200, (need + 29) // 30 + 5))
    try:
        songs, _meta = await fetch_kugou_rank_songs(
            str(rank_id),
            chart_name=chart_name,
            platform=platform,
            min_songs=need,
            max_pages=max_pages,
        )
        if songs:
            return ChartPayload(
                platform=platform,
                chart_name=chart_name,
                chart_type=chart_type,
                fetched_ok=True,
                songs=songs[:limit],
            )
    except Exception:
        pass
    return await _kugou_rank_html_fallback(rank_id, chart_name, chart_type, limit=limit)


async def fetch_kugou_hot(*, limit: int = 100) -> ChartPayload:
    return await _kugou_rank(HOT_RANK_ID, "TOP500（节选）", "hot", limit=limit)


async def fetch_kugou_new(*, limit: int = 100) -> ChartPayload:
    return await _kugou_rank(NEW_RANK_ID, "新歌榜", "new", limit=limit)

import asyncio
from datetime import datetime, timezone

from app.aggregate import fuse_charts
from app.models import ChartPayload, ChartSong, OverviewResponse
from app.providers import (
    fetch_apple_hot,
    fetch_apple_new,
    fetch_kugou_hot,
    fetch_kugou_new,
    fetch_migu_hot,
    fetch_migu_new,
    fetch_netease_hot,
    fetch_netease_new,
    fetch_qq_hot,
    fetch_qq_new,
)


def _clip_chart(c: ChartPayload, n: int) -> ChartPayload:
    """按榜单类型截取前 n 条并重排名次（不足 n 则全用）。"""
    if not c.fetched_ok:
        return c
    take = c.songs[:n]
    new_songs = [
        ChartSong(
            rank=i,
            title=s.title,
            artist=s.artist,
            platform=s.platform,
            chart_name=s.chart_name,
            extra=s.extra,
        )
        for i, s in enumerate(take, start=1)
    ]
    return ChartPayload(
        platform=c.platform,
        chart_name=c.chart_name,
        chart_type=c.chart_type,
        fetched_ok=True,
        error=None,
        songs=new_songs,
    )


def _clamp_fusion_n(n: int) -> int:
    return max(1, min(n, 500))


async def build_overview(hot_n: int, new_n: int) -> OverviewResponse:
    hot_n = _clamp_fusion_n(hot_n)
    new_n = _clamp_fusion_n(new_n)
    tasks = [
        fetch_apple_hot(limit=hot_n),
        fetch_apple_new(limit=new_n),
        fetch_netease_hot(limit=hot_n),
        fetch_netease_new(limit=new_n),
        fetch_qq_hot(limit=hot_n),
        fetch_qq_new(limit=new_n),
        fetch_kugou_hot(limit=hot_n),
        fetch_kugou_new(limit=new_n),
        fetch_migu_hot(limit=hot_n),
        fetch_migu_new(limit=new_n),
    ]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    charts: list[ChartPayload] = []
    fallback_names = [
        ("Apple Music", "中国大陆 · 热门 100（RSS）", "hot"),
        ("Apple Music", "中国大陆 · 新歌 100（RSS）", "new"),
        ("网易云音乐", "热歌榜", "hot"),
        ("网易云音乐", "新歌榜", "new"),
        ("QQ音乐", "巅峰榜 · 热歌", "hot"),
        ("QQ音乐", "巅峰榜 · 新歌", "new"),
        ("酷狗音乐", "TOP500（节选）", "hot"),
        ("酷狗音乐", "新歌榜", "new"),
        ("咪咕音乐", "尖叫热歌榜", "hot"),
        ("咪咕音乐", "尖叫新歌榜", "new"),
    ]
    for idx, item in enumerate(raw_results):
        if isinstance(item, Exception):
            platform, chart_name, chart_type = fallback_names[idx]
            charts.append(
                ChartPayload(
                    platform=platform,
                    chart_name=chart_name,
                    chart_type=chart_type,
                    fetched_ok=False,
                    error=str(item),
                    songs=[],
                )
            )
        else:
            charts.append(item)

    clipped: list[ChartPayload] = []
    for c in charts:
        if c.chart_type == "hot":
            clipped.append(_clip_chart(c, hot_n))
        elif c.chart_type == "new":
            clipped.append(_clip_chart(c, new_n))
        else:
            clipped.append(c)

    fused_hot = fuse_charts(clipped, "hot", fusion_top_n=hot_n)
    fused_new = fuse_charts(clipped, "new", fusion_top_n=new_n)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return OverviewResponse(
        updated_at=now,
        charts=clipped,
        fused_hot=fused_hot,
        fused_new=fused_new,
        fusion_hot_n=hot_n,
        fusion_new_n=new_n,
    )

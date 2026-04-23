from app.models import ChartPayload, ChartSong
from app.qq_toplist import fetch_qq_toplist_songs

# QQ 巅峰榜 topId（musicu.fcg）
HOT_TOP_ID = 26
NEW_TOP_ID = 27


async def _qq_top_detail(
    top_id: int, chart_name: str, chart_type: str, *, limit: int = 100
) -> ChartPayload:
    platform = "QQ音乐"
    try:
        songs = await fetch_qq_toplist_songs(top_id, chart_name, limit)
        if not songs:
            return ChartPayload(
                platform=platform,
                chart_name=chart_name,
                chart_type=chart_type,
                fetched_ok=False,
                error="曲目为空（接口可能已变）",
            )
        return ChartPayload(
            platform=platform,
            chart_name=chart_name,
            chart_type=chart_type,
            fetched_ok=True,
            songs=songs,
        )
    except Exception as e:
        return ChartPayload(
            platform=platform,
            chart_name=chart_name,
            chart_type=chart_type,
            fetched_ok=False,
            error=str(e),
        )


async def fetch_qq_hot(*, limit: int = 100) -> ChartPayload:
    return await _qq_top_detail(HOT_TOP_ID, "巅峰榜 · 热歌", "hot", limit=limit)


async def fetch_qq_new(*, limit: int = 100) -> ChartPayload:
    return await _qq_top_detail(NEW_TOP_ID, "巅峰榜 · 新歌", "new", limit=limit)

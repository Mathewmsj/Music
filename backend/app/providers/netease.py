from app.http_client import get_json
from app.models import ChartPayload, ChartSong

# 官方歌单 ID：热歌榜 / 新歌榜
HOT_ID = "3778678"
NEW_ID = "3779629"


async def _fetch_playlist(
    playlist_id: str, platform: str, chart_name: str, chart_type: str, *, limit: int = 100
) -> ChartPayload:
    url = "https://music.163.com/api/playlist/detail"
    n_req = min(max(limit, 1), 1000)
    try:
        raw = await get_json(url, params={"id": playlist_id, "n": str(n_req)})
        if not isinstance(raw, dict):
            return ChartPayload(
                platform=platform,
                chart_name=chart_name,
                chart_type=chart_type,
                fetched_ok=False,
                error="响应格式异常",
            )
        pl = raw.get("result") or {}
        tracks = pl.get("tracks") or []
        songs: list[ChartSong] = []
        for i, t in enumerate(tracks[:limit], start=1):
            name = (t.get("name") or "").strip()
            ar = t.get("ar") or t.get("artists") or []
            artist = ""
            if ar and isinstance(ar, list):
                artist = " / ".join((a.get("name") or "").strip() for a in ar if isinstance(a, dict))
            if name:
                songs.append(
                    ChartSong(
                        rank=i,
                        title=name,
                        artist=artist or "未知艺人",
                        platform=platform,
                        chart_name=chart_name,
                    )
                )
        return ChartPayload(
            platform=platform,
            chart_name=chart_name,
            chart_type=chart_type,
            fetched_ok=bool(songs),
            error=None if songs else "解析不到曲目",
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


async def fetch_netease_hot(*, limit: int = 100) -> ChartPayload:
    return await _fetch_playlist(HOT_ID, "网易云音乐", "热歌榜", "hot", limit=limit)


async def fetch_netease_new(*, limit: int = 100) -> ChartPayload:
    return await _fetch_playlist(NEW_ID, "网易云音乐", "新歌榜", "new", limit=limit)

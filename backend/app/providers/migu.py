import json

from app.http_client import get_json
from app.models import ChartPayload, ChartSong


async def _migu_rank(
    rank_id: str, chart_name: str, chart_type: str, *, limit: int = 100
) -> ChartPayload:
    platform = "咪咕音乐"
    # 适配你给的 rankDetail?id=xxxx：使用 app.c.nf.migu.cn 的榜单详情
    url = "https://app.c.nf.migu.cn/bmw/rank/rank-info/v1.0"
    try:
        raw = await get_json(url, params={"rankId": rank_id}, headers={"Referer": "https://music.migu.cn/"})
        if not isinstance(raw, dict):
            return ChartPayload(
                platform=platform,
                chart_name=chart_name,
                chart_type=chart_type,
                fetched_ok=False,
                error="响应格式异常",
            )
        code = str(raw.get("code") or "")
        if code not in ("200", "0", "000000"):
            return ChartPayload(
                platform=platform,
                chart_name=chart_name,
                chart_type=chart_type,
                fetched_ok=False,
                error=raw.get("info") or "接口返回非成功状态",
            )
        data = raw.get("data") or {}
        rows = data.get("contents") or []
        songs: list[ChartSong] = []
        for i, row in enumerate(rows[:limit], start=1):
            if not isinstance(row, dict):
                continue
            song_data = row.get("songData")
            if isinstance(song_data, str) and song_data.strip():
                try:
                    song_data = json.loads(song_data)
                except Exception:
                    song_data = {}
            if not isinstance(song_data, dict):
                song_data = {}
            name = (song_data.get("songName") or song_data.get("name") or "").strip()
            singer_list = song_data.get("singerList") or []
            artist = ""
            if isinstance(singer_list, list) and singer_list:
                artist = " / ".join(
                    (a.get("name") or "").strip()
                    for a in singer_list
                    if isinstance(a, dict) and (a.get("name") or "").strip()
                )
            if not artist:
                artist = (row.get("txt") or "").strip()
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
        if not songs:
            return ChartPayload(
                platform=platform,
                chart_name=chart_name,
                chart_type=chart_type,
                fetched_ok=False,
                error="解析不到曲目（接口结构可能变更）",
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


# 你提供的 rankDetail?id=27553319 对应“新歌榜”（从页面来看）
# 另一个常用热歌榜 id：27186466
HOT_RANK_ID = "27186466"
NEW_RANK_ID = "27553319"


async def fetch_migu_hot(*, limit: int = 100) -> ChartPayload:
    return await _migu_rank(HOT_RANK_ID, "尖叫热歌榜", "hot", limit=limit)


async def fetch_migu_new(*, limit: int = 100) -> ChartPayload:
    return await _migu_rank(NEW_RANK_ID, "尖叫新歌榜", "new", limit=limit)

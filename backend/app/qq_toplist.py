"""QQ 音乐巅峰榜 GetDetail 分页拉取，供 overview provider 使用。"""
from __future__ import annotations

import json
from urllib.parse import quote

from app.http_client import get_json
from app.models import ChartSong


def _musicu_url(payload: dict) -> str:
    return "https://u.y.qq.com/cgi-bin/musicu.fcg?format=json&data=" + quote(
        json.dumps(payload, separators=(",", ":"))
    )


async def fetch_qq_toplist_songs(top_id: int, chart_name: str, limit: int) -> list[ChartSong]:
    """拉取 top_id 榜单前至多 limit 条（接口每次最多 100，自动翻 offset）。"""
    headers = {"Referer": "https://y.qq.com/", "Origin": "https://y.qq.com"}
    page_size = 100
    offset = 0
    all_rows: list[dict] = []
    total_num: int | None = None

    while len(all_rows) < limit:
        payload = {
            "comm": {"ct": 24, "cv": 0},
            "toplist": {
                "module": "musicToplist.ToplistInfoServer",
                "method": "GetDetail",
                "param": {"topId": top_id, "offset": offset, "num": page_size, "period": ""},
            },
        }
        raw = await get_json(_musicu_url(payload), headers=headers)
        if not isinstance(raw, dict):
            break
        outer = (raw.get("toplist") or {}).get("data") or {}
        inner = outer.get("data") or {}
        if isinstance(inner, dict) and inner.get("totalNum") is not None:
            try:
                total_num = int(inner.get("totalNum"))
            except (TypeError, ValueError):
                pass

        rows = inner.get("song") if isinstance(inner, dict) else None
        if not isinstance(rows, list) or not rows:
            rows = outer.get("songInfoList") or []
        if not isinstance(rows, list) or not rows:
            break
        for x in rows:
            if isinstance(x, dict):
                all_rows.append(x)
        if len(rows) < page_size:
            break
        offset += page_size
        if total_num is not None and offset >= total_num:
            break
        if offset > 20000:
            break

    songs: list[ChartSong] = []
    for i, item in enumerate(all_rows[:limit], start=1):
        title = (item.get("title") or item.get("name") or item.get("songname") or "").strip()
        artist = (item.get("singerName") or item.get("singername") or "").strip()
        if not title:
            singers = item.get("singer") or []
            if isinstance(singers, list) and singers:
                artist = " / ".join(
                    (s.get("name") or "").strip() for s in singers if isinstance(s, dict)
                )
                title = (item.get("name") or "").strip()
        if not title:
            continue
        songs.append(
            ChartSong(
                rank=i,
                title=title,
                artist=artist or "未知艺人",
                platform="QQ音乐",
                chart_name=chart_name,
            )
        )
    return songs

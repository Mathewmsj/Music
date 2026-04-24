"""酷狗 m 站 rank/info 分页拉取（供 chart_api 与 providers 复用）。"""
from __future__ import annotations

from app.http_client import get_json
from app.models import ChartSong


def _row_to_song(row: dict, rank: int, *, chart_name: str, platform: str) -> ChartSong | None:
    title = (row.get("songname") or row.get("filename") or "").strip()
    authors = row.get("authors") or []
    artist = ""
    if isinstance(authors, list) and authors:
        artist = " / ".join(
            (a.get("author_name") or a.get("name") or "").strip()
            for a in authors
            if isinstance(a, dict) and ((a.get("author_name") or a.get("name") or "").strip())
        )
    if not artist and " - " in title:
        artist, title = title.split(" - ", 1)
    title = title.strip()
    artist = artist.strip()
    if not title:
        return None
    return ChartSong(
        rank=rank,
        title=title,
        artist=artist or "未知艺人",
        platform=platform,
        chart_name=chart_name,
    )


async def fetch_kugou_rank_page(
    rank_id: str,
    page: int,
    *,
    chart_name: str,
    platform: str = "酷狗音乐",
) -> tuple[list[ChartSong], dict]:
    """单页 rank/info。"""
    raw = await get_json(
        "https://m.kugou.com/rank/info/",
        params={"rankid": str(rank_id), "page": str(page), "json": "true"},
        headers={"Referer": "https://www.kugou.com/"},
    )
    songs_blob = raw.get("songs") if isinstance(raw, dict) else None
    meta: dict = {}
    if isinstance(songs_blob, dict):
        meta = {
            "total": songs_blob.get("total"),
            "page": songs_blob.get("page"),
            "pagesize": songs_blob.get("pagesize"),
        }
    rows = songs_blob.get("list") if isinstance(songs_blob, dict) else None
    songs: list[ChartSong] = []
    pagesize = int(meta.get("pagesize") or 0) if meta.get("pagesize") is not None else 0
    offset = (page - 1) * pagesize if pagesize > 0 else 0
    if isinstance(rows, list):
        for idx, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            s = _row_to_song(row, rank=offset + idx, chart_name=chart_name, platform=platform)
            if s:
                songs.append(s)
    return songs, meta


async def fetch_kugou_rank_songs(
    rank_id: str,
    *,
    chart_name: str,
    platform: str = "酷狗音乐",
    min_songs: int = 50,
    max_pages: int = 25,
) -> tuple[list[ChartSong], dict]:
    """
    连续请求 rank/info 直到凑满 min_songs 或没有更多数据。
    返回 (歌曲列表, meta)。
    """
    out: list[ChartSong] = []
    meta: dict = {"rankid": rank_id, "pages_fetched": 0, "requested_min": min_songs}
    last_total: int | None = None
    for page in range(1, max_pages + 1):
        chunk, pg = await fetch_kugou_rank_page(
            rank_id, page, chart_name=chart_name, platform=platform
        )
        if not chunk:
            break
        if pg.get("total") is not None:
            try:
                last_total = int(pg["total"])
            except (TypeError, ValueError):
                pass
        meta["pagesize"] = pg.get("pagesize")
        meta["total_reported"] = pg.get("total")
        for s in chunk:
            out.append(
                ChartSong(
                    rank=len(out) + 1,
                    title=s.title,
                    artist=s.artist,
                    platform=s.platform,
                    chart_name=s.chart_name,
                )
            )
        meta["pages_fetched"] = page
        if len(out) >= min_songs:
            break
    if last_total is not None and len(out) < last_total:
        meta["partial"] = True
        meta["note"] = "接口分页在部分页后中断，未拉满官方 total"
    return out, meta


async def fetch_kugou_rank_all_pages(
    rank_id: str,
    *,
    chart_name: str,
    platform: str = "酷狗音乐",
    max_pages: int = 200,
) -> tuple[list[ChartSong], dict]:
    """尽可能翻页直到空页或达到 max_pages。"""
    out: list[ChartSong] = []
    meta: dict = {"rankid": rank_id, "pages_fetched": 0}
    first_total: int | None = None
    pagesize: int | None = None
    for page in range(1, max_pages + 1):
        chunk, pg = await fetch_kugou_rank_page(
            rank_id, page, chart_name=chart_name, platform=platform
        )
        if not chunk:
            break
        if first_total is None and pg.get("total") is not None:
            try:
                first_total = int(pg["total"])
            except (TypeError, ValueError):
                first_total = None
        if pagesize is None and pg.get("pagesize") is not None:
            try:
                pagesize = int(pg["pagesize"])
            except (TypeError, ValueError):
                pagesize = None
        for s in chunk:
            out.append(
                ChartSong(
                    rank=len(out) + 1,
                    title=s.title,
                    artist=s.artist,
                    platform=s.platform,
                    chart_name=s.chart_name,
                )
            )
        meta["pages_fetched"] = page
        meta["pagesize"] = pg.get("pagesize")
        meta["total_reported"] = pg.get("total")
    meta["returned"] = len(out)
    if first_total is not None and len(out) < first_total:
        meta["partial"] = True
        meta["note"] = "酷狗 m.kugou.com/rank/info 分页在部分榜单上会中断，未拉满官方 total"
    return out, meta

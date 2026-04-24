from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import quote

from app.http_client import get_json, get_text
from app.kugou_fetch import fetch_kugou_rank_all_pages, fetch_kugou_rank_page
from app.models import ChartDetailResponse, ChartListResponse, ChartMeta, ChartSong


async def list_apple_charts() -> ChartListResponse:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    charts = [
        ChartMeta(
            platform_key="apple",
            platform="Apple Music",
            chart_id="cn-most-played-songs-100",
            chart_name="中国大陆 · 热门 100",
            chart_type="hot",
            source_url="https://rss.applemarketingtools.com/api/v2/cn/music/most-played/100/songs.json",
        ),
        ChartMeta(
            platform_key="apple",
            platform="Apple Music",
            chart_id="cn-new-music-songs-100",
            chart_name="中国大陆 · 新歌 100",
            chart_type="new",
            source_url="https://rss.applemarketingtools.com/api/v2/cn/music/new-music/100/songs.json",
        ),
    ]
    return ChartListResponse(updated_at=now, platform_key="apple", platform="Apple Music", charts=charts)


async def fetch_apple_chart(chart_id: str) -> ChartDetailResponse:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    if chart_id == "cn-most-played-songs-100":
        url = "https://rss.applemarketingtools.com/api/v2/cn/music/most-played/100/songs.json"
        chart_name, chart_type = "中国大陆 · 热门 100", "hot"
    elif chart_id == "cn-new-music-songs-100":
        url = "https://rss.applemarketingtools.com/api/v2/cn/music/new-music/100/songs.json"
        chart_name, chart_type = "中国大陆 · 新歌 100", "new"
    else:
        return ChartDetailResponse(
            updated_at=now,
            platform_key="apple",
            platform="Apple Music",
            chart_id=chart_id,
            chart_name="未知榜单",
            chart_type="unknown",
            source_url="",
            fetched_ok=False,
            error="chart_id 不支持",
        )
    try:
        raw = await get_json(url, headers={"Referer": "https://music.apple.com/cn/"})
        feed = (raw or {}).get("feed") if isinstance(raw, dict) else None
        results = (feed or {}).get("results") if isinstance(feed, dict) else None
        songs: list[ChartSong] = []
        if isinstance(results, list):
            for i, item in enumerate(results, start=1):
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
                            platform="Apple Music",
                            chart_name=chart_name,
                        )
                    )
        return ChartDetailResponse(
            updated_at=now,
            platform_key="apple",
            platform="Apple Music",
            chart_id=chart_id,
            chart_name=chart_name,
            chart_type=chart_type,
            source_url=url,
            fetched_ok=bool(songs),
            error=None if songs else "RSS 结果为空",
            songs=songs,
            meta={"returned": len(songs)},
        )
    except Exception as e:
        return ChartDetailResponse(
            updated_at=now,
            platform_key="apple",
            platform="Apple Music",
            chart_id=chart_id,
            chart_name=chart_name,
            chart_type=chart_type,
            source_url=url,
            fetched_ok=False,
            error=str(e),
            songs=[],
        )


async def list_netease_charts() -> ChartListResponse:
    """
    通过榜单页发现所有榜单：解析 /discover/toplist 的榜单入口。
    """
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    url = "https://music.163.com/discover/toplist"
    html = await get_text(url, headers={"Referer": "https://music.163.com/"})
    # 注意：HTML 里是 toplist?id= 而不是 toplist\?id=；之前正则写错会导致只能命中兜底两条。
    pairs = re.findall(
        r'<a[^>]+href="(?:https://music\.163\.com)?/discover/toplist\?id=(\d+)"[^>]*>([^<]+)</a>',
        html,
    )
    charts: list[ChartMeta] = []
    seen: set[str] = set()
    for chart_id, name in pairs:
        chart_id = chart_id.strip()
        if not chart_id or chart_id in seen:
            continue
        seen.add(chart_id)
        name = re.sub(r"\s+", " ", (name or "").strip())
        charts.append(
            ChartMeta(
                platform_key="netease",
                platform="网易云音乐",
                chart_id=chart_id,
                chart_name=name or f"榜单 {chart_id}",
                chart_type="unknown",
                source_url=f"https://music.163.com/#/discover/toplist?id={chart_id}",
            )
        )
    # 兜底：至少保证热歌/新歌存在
    if "3778678" not in seen:
        charts.insert(
            0,
            ChartMeta(
                platform_key="netease",
                platform="网易云音乐",
                chart_id="3778678",
                chart_name="热歌榜",
                chart_type="hot",
                source_url="https://music.163.com/#/discover/toplist?id=3778678",
            ),
        )
    if "3779629" not in seen:
        charts.insert(
            1,
            ChartMeta(
                platform_key="netease",
                platform="网易云音乐",
                chart_id="3779629",
                chart_name="新歌榜",
                chart_type="new",
                source_url="https://music.163.com/#/discover/toplist?id=3779629",
            ),
        )
    return ChartListResponse(updated_at=now, platform_key="netease", platform="网易云音乐", charts=charts)


async def fetch_netease_chart(chart_id: str) -> ChartDetailResponse:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    api = "https://music.163.com/api/playlist/detail"
    try:
        raw = await get_json(api, params={"id": chart_id, "n": "2000"}, headers={"Referer": "https://music.163.com/"})
        pl = (raw or {}).get("result") if isinstance(raw, dict) else None
        chart_name = (pl or {}).get("name") if isinstance(pl, dict) else None
        chart_name = (chart_name or f"榜单 {chart_id}").strip()
        track_count = (pl or {}).get("trackCount") if isinstance(pl, dict) else None
        tracks = (pl or {}).get("tracks") if isinstance(pl, dict) else None
        songs: list[ChartSong] = []
        if isinstance(tracks, list):
            for i, t in enumerate(tracks, start=1):
                if not isinstance(t, dict):
                    continue
                title = (t.get("name") or "").strip()
                ars = t.get("ar") or t.get("artists") or []
                artist = ""
                if isinstance(ars, list) and ars:
                    artist = " / ".join((a.get("name") or "").strip() for a in ars if isinstance(a, dict))
                if title:
                    songs.append(
                        ChartSong(
                            rank=i,
                            title=title,
                            artist=artist or "未知艺人",
                            platform="网易云音乐",
                            chart_name=chart_name,
                        )
                    )
        meta: dict = {}
        if track_count is not None:
            meta["trackCount"] = track_count
        meta["returned"] = len(songs)
        return ChartDetailResponse(
            updated_at=now,
            platform_key="netease",
            platform="网易云音乐",
            chart_id=chart_id,
            chart_name=chart_name,
            chart_type="unknown",
            source_url=f"https://music.163.com/#/discover/toplist?id={chart_id}",
            fetched_ok=bool(songs),
            error=None if songs else "tracks 为空",
            songs=songs,
            meta=meta,
        )
    except Exception as e:
        return ChartDetailResponse(
            updated_at=now,
            platform_key="netease",
            platform="网易云音乐",
            chart_id=chart_id,
            chart_name=f"榜单 {chart_id}",
            chart_type="unknown",
            source_url=f"https://music.163.com/#/discover/toplist?id={chart_id}",
            fetched_ok=False,
            error=str(e),
            songs=[],
        )


async def list_kugou_charts() -> ChartListResponse:
    """
    酷狗榜单列表：m.kugou.com/rank/list&json=true
    返回包含 rankid 与榜单名称。
    """
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    url = "https://m.kugou.com/rank/list"
    raw = await get_json(url, params={"json": "true"}, headers={"Referer": "https://www.kugou.com/"})
    charts: list[ChartMeta] = []
    if isinstance(raw, dict):
        rank = raw.get("rank") or raw.get("data") or {}
        lists = rank.get("list") if isinstance(rank, dict) else None
        if isinstance(lists, list):
            for it in lists:
                if not isinstance(it, dict):
                    continue
                rid = str(it.get("rankid") or it.get("id") or "").strip()
                name = str(it.get("rankname") or it.get("name") or "").strip()
                if not rid:
                    continue
                charts.append(
                    ChartMeta(
                        platform_key="kugou",
                        platform="酷狗音乐",
                        chart_id=rid,
                        chart_name=name or f"榜单 {rid}",
                        chart_type="unknown",
                        source_url=f"https://www.kugou.com/yy/rank/home/1-{rid}.html?from=rank",
                    )
                )
    # 兜底
    if not charts:
        charts = [
            ChartMeta(
                platform_key="kugou",
                platform="酷狗音乐",
                chart_id="8888",
                chart_name="酷狗TOP500",
                chart_type="hot",
                source_url="https://www.kugou.com/yy/rank/home/1-8888.html?from=rank",
            )
        ]
    return ChartListResponse(updated_at=now, platform_key="kugou", platform="酷狗音乐", charts=charts)


async def fetch_kugou_chart(chart_id: str, *, page: int = 1, all_pages: bool = False) -> ChartDetailResponse:
    """
    酷狗榜单详情：m.kugou.com/rank/info/?rankid=xxx&page=1&json=true
    all_pages=True 时按 total/pagesize 自动翻页拉全量。
    """
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    src = f"https://www.kugou.com/yy/rank/home/1-{chart_id}.html?from=rank"
    cname = f"榜单 {chart_id}"
    try:
        if not all_pages:
            songs, meta = await fetch_kugou_rank_page(chart_id, page, chart_name=cname)
            # 默认「单页」也尽量满足至少 50 条：首屏 30 条时自动再拉一页
            if page == 1 and len(songs) < 50:
                more, meta2 = await fetch_kugou_rank_page(chart_id, 2, chart_name=cname)
                if more:
                    base = len(songs)
                    for i, s in enumerate(more, start=1):
                        songs.append(
                            ChartSong(
                                rank=base + i,
                                title=s.title,
                                artist=s.artist,
                                platform=s.platform,
                                chart_name=s.chart_name,
                            )
                        )
                    meta = {**meta, "merged_page2": True, "page2_meta": meta2}
            return ChartDetailResponse(
                updated_at=now,
                platform_key="kugou",
                platform="酷狗音乐",
                chart_id=chart_id,
                chart_name=cname,
                chart_type="unknown",
                source_url=src,
                fetched_ok=bool(songs),
                error=None if songs else "songs 为空",
                songs=songs,
                meta={"page": page, **meta, "returned": len(songs), "min_target": 50},
            )

        all_songs, meta = await fetch_kugou_rank_all_pages(chart_id, chart_name=cname, max_pages=200)
        return ChartDetailResponse(
            updated_at=now,
            platform_key="kugou",
            platform="酷狗音乐",
            chart_id=chart_id,
            chart_name=cname,
            chart_type="unknown",
            source_url=src,
            fetched_ok=bool(all_songs),
            error=None if all_songs else "songs 为空",
            songs=all_songs,
            meta=meta,
        )
    except Exception as e:
        return ChartDetailResponse(
            updated_at=now,
            platform_key="kugou",
            platform="酷狗音乐",
            chart_id=chart_id,
            chart_name=f"榜单 {chart_id}",
            chart_type="unknown",
            source_url=src,
            fetched_ok=False,
            error=str(e),
            songs=[],
        )


async def list_migu_charts() -> ChartListResponse:
    """
    咪咕 v5 rankDetail 使用 rankId。官方「榜单列表」接口不稳定，这里内置常用 rankId（可继续补充）。
    """
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    charts = [
        ChartMeta(
            platform_key="migu",
            platform="咪咕音乐",
            chart_id="27186466",
            chart_name="尖叫热歌榜",
            chart_type="hot",
            source_url="https://music.migu.cn/v5/#/rankDetail?id=27186466&playlistType=charts",
        ),
        ChartMeta(
            platform_key="migu",
            platform="咪咕音乐",
            chart_id="27553319",
            chart_name="尖叫新歌榜",
            chart_type="new",
            source_url="https://music.migu.cn/v5/#/rankDetail?id=27553319&playlistType=charts",
        ),
        ChartMeta(
            platform_key="migu",
            platform="咪咕音乐",
            chart_id="27553408",
            chart_name="尖叫原创榜",
            chart_type="unknown",
            source_url="https://music.migu.cn/v5/#/rankDetail?id=27553408&playlistType=charts",
        ),
        ChartMeta(
            platform_key="migu",
            platform="咪咕音乐",
            chart_id="23189800",
            chart_name="港台榜",
            chart_type="unknown",
            source_url="https://music.migu.cn/v5/#/rankDetail?id=23189800&playlistType=charts",
        ),
    ]
    return ChartListResponse(updated_at=now, platform_key="migu", platform="咪咕音乐", charts=charts)


async def fetch_migu_chart(chart_id: str) -> ChartDetailResponse:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    url = "https://app.c.nf.migu.cn/bmw/rank/rank-info/v1.0"
    src = f"https://music.migu.cn/v5/#/rankDetail?id={chart_id}&playlistType=charts"
    try:
        raw = await get_json(url, params={"rankId": chart_id}, headers={"Referer": "https://music.migu.cn/"})
        code = str(raw.get("code") or "") if isinstance(raw, dict) else ""
        if code not in ("200", "0", "000000"):
            return ChartDetailResponse(
                updated_at=now,
                platform_key="migu",
                platform="咪咕音乐",
                chart_id=chart_id,
                chart_name=f"榜单 {chart_id}",
                chart_type="unknown",
                source_url=src,
                fetched_ok=False,
                error=(raw.get("info") if isinstance(raw, dict) else None) or "接口非成功",
                songs=[],
            )
        data = (raw.get("data") or {}) if isinstance(raw, dict) else {}
        chart_title = (data.get("title") or "").strip() or f"榜单 {chart_id}"
        rows = data.get("contents") or []
        songs: list[ChartSong] = []
        for i, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                continue
            sd = row.get("songData")
            if isinstance(sd, str) and sd.strip():
                try:
                    sd = json.loads(sd)
                except Exception:
                    sd = {}
            if not isinstance(sd, dict):
                sd = {}
            title = (sd.get("songName") or sd.get("name") or "").strip()
            singer_list = sd.get("singerList") or []
            artist = ""
            if isinstance(singer_list, list) and singer_list:
                artist = " / ".join(
                    (a.get("name") or "").strip()
                    for a in singer_list
                    if isinstance(a, dict) and (a.get("name") or "").strip()
                )
            if title:
                songs.append(
                    ChartSong(
                        rank=i,
                        title=title,
                        artist=artist or "未知艺人",
                        platform="咪咕音乐",
                        chart_name=chart_title,
                    )
                )
        return ChartDetailResponse(
            updated_at=now,
            platform_key="migu",
            platform="咪咕音乐",
            chart_id=chart_id,
            chart_name=chart_title,
            chart_type="unknown",
            source_url=src,
            fetched_ok=bool(songs),
            error=None if songs else "contents 为空",
            songs=songs,
            meta={
                "totalCount": data.get("totalCount"),
                "hasNextPage": data.get("hasNextPage"),
                "returned": len(songs),
            },
        )
    except Exception as e:
        return ChartDetailResponse(
            updated_at=now,
            platform_key="migu",
            platform="咪咕音乐",
            chart_id=chart_id,
            chart_name=f"榜单 {chart_id}",
            chart_type="unknown",
            source_url=src,
            fetched_ok=False,
            error=str(e),
            songs=[],
        )


def _qq_musicu_url(payload: dict) -> str:
    return "https://u.y.qq.com/cgi-bin/musicu.fcg?format=json&data=" + quote(
        json.dumps(payload, separators=(",", ":"))
    )


async def list_qq_charts() -> ChartListResponse:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    payload = {
        "comm": {"ct": 24, "cv": 0},
        "topList": {"module": "musicToplist.ToplistInfoServer", "method": "GetAll", "param": {}},
    }
    raw = await get_json(
        _qq_musicu_url(payload),
        headers={"Referer": "https://y.qq.com/", "Origin": "https://y.qq.com"},
    )
    charts: list[ChartMeta] = []
    data = (raw.get("topList") or {}).get("data") or {}
    groups = data.get("group") or []
    for g in groups:
        if not isinstance(g, dict):
            continue
        for it in g.get("toplist") or []:
            if not isinstance(it, dict):
                continue
            top_id = it.get("topId")
            if top_id is None:
                continue
            title = (it.get("title") or "").strip()
            charts.append(
                ChartMeta(
                    platform_key="qq",
                    platform="QQ音乐",
                    chart_id=str(int(top_id)),
                    chart_name=title or f"榜单 {top_id}",
                    chart_type="unknown",
                    source_url=f"https://y.qq.com/n/ryqq/toplist/{int(top_id)}",
                )
            )
    return ChartListResponse(updated_at=now, platform_key="qq", platform="QQ音乐", charts=charts)


async def fetch_qq_chart(chart_id: str, *, all_pages: bool = False) -> ChartDetailResponse:
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    top_id = int(chart_id)
    src = f"https://y.qq.com/n/ryqq/toplist/{top_id}"
    headers = {"Referer": "https://y.qq.com/", "Origin": "https://y.qq.com"}

    def _parse_rows(rows: list, *, chart_name: str, base_rank: int) -> list[ChartSong]:
        out: list[ChartSong] = []
        for idx, item in enumerate(rows, start=1):
            if not isinstance(item, dict):
                continue
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
            rk = int(item["rank"]) if str(item.get("rank") or "").isdigit() else base_rank + idx - 1
            out.append(
                ChartSong(
                    rank=rk,
                    title=title,
                    artist=artist or "未知艺人",
                    platform="QQ音乐",
                    chart_name=chart_name,
                )
            )
        return out

    try:
        page_size = 100
        offset = 0
        all_rows: list[dict] = []
        chart_name = f"榜单 {top_id}"
        total_num: int | None = None
        requests = 0

        while True:
            requests += 1
            payload = {
                "comm": {"ct": 24, "cv": 0},
                "toplist": {
                    "module": "musicToplist.ToplistInfoServer",
                    "method": "GetDetail",
                    "param": {"topId": top_id, "offset": offset, "num": page_size, "period": ""},
                },
            }
            raw = await get_json(_qq_musicu_url(payload), headers=headers)
            outer = (raw.get("toplist") or {}).get("data") or {}
            inner = outer.get("data") or {}
            if isinstance(inner, dict) and inner.get("title"):
                chart_name = str(inner.get("title")).strip() or chart_name
            if isinstance(inner, dict) and inner.get("totalNum") is not None:
                try:
                    total_num = int(inner.get("totalNum"))
                except (TypeError, ValueError):
                    total_num = None

            rows = inner.get("song") if isinstance(inner, dict) else None
            if not isinstance(rows, list) or not rows:
                rows = outer.get("songInfoList") or []
            if not isinstance(rows, list):
                rows = []

            if not rows:
                break
            all_rows.extend([x for x in rows if isinstance(x, dict)])
            if not all_pages or len(rows) < page_size:
                break
            offset += page_size
            if total_num is not None and offset >= total_num:
                break
            if offset > 20000:
                break

        songs = _parse_rows(all_rows, chart_name=chart_name, base_rank=1)
        meta = {
            "returned": len(songs),
            "totalNum": total_num,
            "requests": requests,
        }
        return ChartDetailResponse(
            updated_at=now,
            platform_key="qq",
            platform="QQ音乐",
            chart_id=str(top_id),
            chart_name=chart_name,
            chart_type="unknown",
            source_url=src,
            fetched_ok=bool(songs),
            error=None if songs else "曲目为空",
            songs=songs,
            meta=meta,
        )
    except Exception as e:
        return ChartDetailResponse(
            updated_at=now,
            platform_key="qq",
            platform="QQ音乐",
            chart_id=str(top_id),
            chart_name=f"榜单 {top_id}",
            chart_type="unknown",
            source_url=src,
            fetched_ok=False,
            error=str(e),
            songs=[],
        )

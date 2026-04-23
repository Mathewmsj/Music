import asyncio
import base64
import hashlib
import json
import random
import re
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Awaitable, Callable
from urllib.parse import quote

from app import config
from app.http_client import get_json
from app.models import OverviewResponse

_song_cache: dict[str, dict] = {}
_insight_jobs: dict[str, dict] = {}

_GENRE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "流行": ("流行", "pop"),
    "说唱": ("说唱", "rap", "hiphop", "trap"),
    "摇滚": ("摇滚", "rock", "朋克", "metal"),
    "电子": ("电子", "edm", "house", "techno"),
    "民谣": ("民谣", "folk", "acoustic"),
    "r&b": ("r&b", "rnb", "soul", "灵魂"),
    "古风": ("古风", "国风"),
    "情歌": ("情歌", "爱情", "恋爱"),
}


def _normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _qq_musicu_url(payload: dict) -> str:
    return "https://u.y.qq.com/cgi-bin/musicu.fcg?format=json&data=" + quote(
        json.dumps(payload, separators=(",", ":"))
    )


def _qq_openapi_sign(app_id: str, app_key: str, timestamp: int, opi_cmd: str) -> str:
    """
    QQ OpenAPI 签名（按常见拼接规则，若平台侧有定制规则可再调整）：
    md5(app_id + app_key + timestamp + opi_cmd)
    """
    base = f"{app_id}{app_key}{timestamp}{opi_cmd}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


async def _qq_search_song(title: str, artist: str) -> dict | None:
    query = _normalize_text(f"{title} {artist}")
    payload = {
        "comm": {"ct": "19", "cv": "1859"},
        "req_1": {
            "method": "DoSearchForQQMusicDesktop",
            "module": "music.search.SearchCgiService",
            "param": {
                "remoteplace": "txt.mqq.all",
                "searchid": str(random.randint(10**9, 10**10 - 1)),
                "search_type": 0,
                "query": query,
                "page_num": 1,
                "num_per_page": 10,
            },
        },
    }
    raw = await get_json(
        _qq_musicu_url(payload),
        headers={"Referer": "https://y.qq.com/", "Origin": "https://y.qq.com"},
    )
    body = (raw.get("req_1") or {}).get("data") if isinstance(raw, dict) else {}
    songs = ((body or {}).get("body") or {}).get("song") or {}
    rows = songs.get("list") if isinstance(songs, dict) else []
    if not isinstance(rows, list) or not rows:
        return None

    target_artist = artist.lower().replace(" ", "")
    best = None
    best_score = -1.0
    for it in rows:
        if not isinstance(it, dict):
            continue
        name = str(it.get("title") or it.get("name") or "")
        singers = it.get("singer") or []
        singer_text = " / ".join(
            str(x.get("name") or "") for x in singers if isinstance(x, dict)
        )
        score = 0.0
        if title and title.lower() in name.lower():
            score += 3
        if target_artist and target_artist in singer_text.lower().replace(" ", ""):
            score += 3
        score -= abs(len(name) - len(title)) * 0.02
        if score > best_score:
            best_score = score
            best = it
    return best


async def _qq_song_detail(song_mid: str) -> dict | None:
    payload = {
        "comm": {"ct": 24, "cv": 0},
        "songinfo": {
            "module": "music.pf_song_detail_svr",
            "method": "get_song_detail",
            "param": {"song_mid": song_mid, "song_type": 0},
        },
    }
    raw = await get_json(
        _qq_musicu_url(payload),
        headers={"Referer": "https://y.qq.com/", "Origin": "https://y.qq.com"},
    )
    info = (raw.get("songinfo") or {}).get("data") if isinstance(raw, dict) else {}
    track = (info or {}).get("track_info")
    return track if isinstance(track, dict) else None


async def _qq_song_lyric(song_mid: str) -> str:
    raw = await get_json(
        "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg",
        params={
            "songmid": song_mid,
            "format": "json",
            "nobase64": "1",
            "g_tk": "5381",
        },
        headers={"Referer": "https://y.qq.com/", "Origin": "https://y.qq.com"},
    )
    lyric = (raw or {}).get("lyric") if isinstance(raw, dict) else ""
    if isinstance(lyric, str) and lyric.strip():
        raw_lyric = lyric
        if not raw_lyric.startswith("["):
            try:
                raw_lyric = base64.b64decode(raw_lyric).decode("utf-8", errors="ignore")
            except Exception:
                pass
        lines = []
        for line in raw_lyric.splitlines():
            clean = re.sub(r"\[[^\]]+\]", "", line).strip()
            if clean:
                lines.append(clean)
        return "\n".join(lines)
    return ""


async def _qq_openapi_song_info_batch(song_mid: str) -> dict | None:
    """
    使用用户指定接口：
    fcg_music_custom_get_song_info_batch.fcg
    目标字段：genre(string, 流派)
    """
    app_id = config.qq_openapi_app_id
    app_key = config.qq_openapi_app_key
    if not app_id or not app_key or not song_mid:
        return None
    opi_cmd = "fcg_music_custom_get_song_info_batch.fcg"
    ts = int(time.time())
    sign = _qq_openapi_sign(app_id, app_key, ts, opi_cmd)
    raw = await get_json(
        "https://openrpc.music.qq.com/rpc_proxy/fcgi-bin/music_open_api.fcg",
        params={
            "opi_cmd": opi_cmd,
            "app_id": app_id,
            "app_key": app_key,
            "timestamp": str(ts),
            "sign": sign,
            "song_mid_list": json.dumps([song_mid], ensure_ascii=False),
        },
        headers={"Referer": "https://y.qq.com/"},
    )
    if not isinstance(raw, dict):
        return None
    data = raw.get("data")
    if isinstance(data, list) and data:
        row = data[0]
        return row if isinstance(row, dict) else None
    if isinstance(data, dict):
        # 兼容 data 为 map 的情况
        first = next(iter(data.values()), None)
        return first if isinstance(first, dict) else None
    # 少量实现会把列表放在 song_info_list
    rows = raw.get("song_info_list")
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


async def _netease_search_song(title: str, artist: str) -> dict | None:
    keyword = _normalize_text(f"{title} {artist}")
    raw = await get_json(
        "https://music.163.com/api/cloudsearch/pc",
        params={"s": keyword, "type": "1", "limit": "8", "offset": "0"},
        headers={"Referer": "https://music.163.com/"},
    )
    result = (raw or {}).get("result") if isinstance(raw, dict) else {}
    songs = result.get("songs") if isinstance(result, dict) else []
    if not isinstance(songs, list) or not songs:
        return None

    target_artist = artist.lower().replace(" ", "")
    best = None
    best_score = -1.0
    for it in songs:
        if not isinstance(it, dict):
            continue
        name = str(it.get("name") or "")
        singers = it.get("ar") or it.get("artists") or []
        singer_text = " / ".join(
            str(x.get("name") or "") for x in singers if isinstance(x, dict)
        )
        score = 0.0
        if title and title.lower() in name.lower():
            score += 3
        if target_artist and target_artist in singer_text.lower().replace(" ", ""):
            score += 3
        score -= abs(len(name) - len(title)) * 0.02
        if score > best_score:
            best_score = score
            best = it
    return best


async def _netease_song_detail(song_id: str) -> dict | None:
    raw = await get_json(
        "https://music.163.com/api/song/detail",
        params={"ids": f"[{song_id}]"},
        headers={"Referer": "https://music.163.com/"},
    )
    songs = (raw or {}).get("songs") if isinstance(raw, dict) else []
    if isinstance(songs, list) and songs and isinstance(songs[0], dict):
        return songs[0]
    return None


async def _mcsc_post_index(payload: dict[str, str]) -> dict | None:
    # 复用 httpx 客户端能力：直接用 get_json 不支持 POST，这里轻量实现一次 POST。
    import httpx

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        r = await client.post(
            "http://search.mcsc.com.cn/index",
            data=payload,
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "http://search.mcsc.com.cn/",
                "User-Agent": "Mozilla/5.0",
            },
        )
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return None


async def _mcsc_lookup_genre(title: str, artist: str) -> dict:
    obj = await _mcsc_post_index(
        {
            "page_index": "1",
            "singer_name": artist,
            "new_album_name": "",
            "new_song_name": title,
            "content_auther": "",
            "music_auther": "",
        }
    )
    rows = obj.get("data") if isinstance(obj, dict) else None
    if not isinstance(rows, list) or not rows:
        return {}
    # 取第一条最相关结果
    src = rows[0].get("_source") if isinstance(rows[0], dict) else None
    if not isinstance(src, dict):
        return {}
    out: dict = {}
    g = str(src.get("song_genre") or "").strip()
    if g:
        out["song_genre"] = g
    lang = str(src.get("song_language") or "").strip()
    if lang:
        out["song_language"] = lang
    return out


async def enrich_song(title: str, artist: str) -> dict:
    cache_key = f"{_normalize_text(title).lower()}::{_normalize_text(artist).lower()}"
    if cache_key in _song_cache:
        return _song_cache[cache_key]

    result: dict = {
        "title": title,
        "artist": artist,
        "found": False,
        "intro": "",
        "album": "",
        "duration_sec": None,
        "publish_time": None,
        "cover_url": "",
        "lyric_excerpt": "",
        "genres": [],
        "source": "qq-openapi",
    }
    try:
        hit = await _qq_search_song(title, artist)
        if not hit:
            _song_cache[cache_key] = result
            return result

        song_mid = str(hit.get("mid") or hit.get("songmid") or "")
        detail = await _qq_song_detail(song_mid) if song_mid else None
        lyric = await _qq_song_lyric(song_mid) if song_mid else ""
        if not detail:
            _song_cache[cache_key] = result
            return result

        name = str(detail.get("title") or detail.get("name") or title)
        singers = detail.get("singer") or []
        singer_text = " / ".join(
            str(x.get("name") or "") for x in singers if isinstance(x, dict)
        ) or artist
        album = detail.get("album") or {}
        album_name = str(album.get("title") or album.get("name") or "")
        cover = ""
        album_mid = str(album.get("mid") or "")
        if album_mid:
            cover = f"https://y.gtimg.cn/music/photo_new/T002R500x500M000{album_mid}.jpg"

        interval = detail.get("interval")
        duration_sec = int(interval) if isinstance(interval, int) else None

        genres: list[str] = []
        genre_obj = detail.get("genre")
        if isinstance(genre_obj, dict):
            g = str(genre_obj.get("name") or "").strip()
            if g:
                genres.append(g)
        elif isinstance(genre_obj, str):
            g = genre_obj.strip()
            if g and not g.isdigit():
                genres.append(g)
        info_rows = detail.get("info") or []
        if isinstance(info_rows, list):
            for row in info_rows:
                if not isinstance(row, dict):
                    continue
                title_text = str(row.get("title") or "")
                if title_text in ("流派", "风格", "语种"):
                    values = row.get("content") or []
                    if isinstance(values, list):
                        for v in values:
                            if isinstance(v, dict):
                                t = str(v.get("value") or "").strip()
                                if t:
                                    genres.append(t)
        # 1) 优先使用你指定的 QQ OpenAPI：fcg_music_custom_get_song_info_batch.fcg / genre
        try:
            qq_batch = await _qq_openapi_song_info_batch(song_mid)
            if isinstance(qq_batch, dict):
                g = str(qq_batch.get("genre") or "").strip()
                if g:
                    genres.append(g)
                lang = str(qq_batch.get("language") or "").strip()
                if lang:
                    result["language"] = lang
        except Exception:
            pass

        # 2) 其次使用网易云 songTag（你之前指定的曲风来源）
        try:
            ne_hit = await _netease_search_song(name, singer_text)
            ne_id = str((ne_hit or {}).get("id") or "")
            ne_detail = await _netease_song_detail(ne_id) if ne_id else None
            song_tag = (ne_detail or {}).get("songTag") if isinstance(ne_detail, dict) else None
            if isinstance(song_tag, list):
                for tag in song_tag:
                    if isinstance(tag, str):
                        t = tag.strip()
                        if t:
                            genres.append(t)
        except Exception:
            # 保持静默回退，避免单一数据源失败影响整体
            pass

        # 3) 若前两者都没有，再用 MCSC 的 song_genre
        if not genres:
            try:
                mc = await _mcsc_lookup_genre(name, singer_text)
                g = str(mc.get("song_genre") or "").strip()
                if g:
                    genres.append(g)
                if mc.get("song_language"):
                    result["language"] = mc["song_language"]
            except Exception:
                pass

        # 4) 关键词猜测（最后手段）
        if not genres:
            text_blob = " ".join([name, singer_text, album_name, lyric]).lower()
            for g, keys in _GENRE_KEYWORDS.items():
                if any(k.lower() in text_blob for k in keys):
                    genres.append(g)
        genres = sorted(set(genres))

        intro_parts = [f"《{name}》- {singer_text}"]
        if album_name:
            intro_parts.append(f"收录于专辑《{album_name}》")
        if duration_sec:
            intro_parts.append(f"时长约 {duration_sec} 秒")
        else:
            intro_parts.append("时长未知")

        result.update(
            {
                "title": name,
                "artist": singer_text,
                "found": True,
                "intro": "；".join(intro_parts),
                "album": album_name,
                "duration_sec": duration_sec,
                "cover_url": cover,
                "lyric_excerpt": lyric,
                "genres": genres,
                "song_id": song_mid,
                "song_url": f"https://y.qq.com/n/ryqq/songDetail/{song_mid}" if song_mid else "",
            }
        )
    except Exception as e:
        result["error"] = str(e)

    _song_cache[cache_key] = result
    return result


async def build_overview_insights(
    overview: OverviewResponse,
    *,
    chart_type: str = "hot",
    sample_size: int = 30,
    on_progress: Callable[[int, int], Awaitable[None]] | None = None,
) -> dict:
    fused = overview.fused_hot if chart_type == "hot" else overview.fused_new
    sample = fused[: max(1, min(sample_size, len(fused)))]

    artist_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    genre_counter: Counter[str] = Counter()
    song_insights: list[dict] = []

    for s in sample:
        artist_counter[s.artist] += 1
        for src in s.sources:
            source_counter[src] += 1

    sem = asyncio.Semaphore(8)
    progress = {"done": 0, "total": len(sample)}

    async def worker(song) -> dict:
        async with sem:
            detail = await enrich_song(song.title, song.artist)
            progress["done"] += 1
            if on_progress:
                await on_progress(progress["done"], progress["total"])
            return detail

    details = await asyncio.gather(*(worker(s) for s in sample))
    song_insights.extend(details)

    for d in song_insights:
        for g in d.get("genres") or []:
            genre_counter[g] += 1

    artist_cloud = [{"text": k, "weight": v} for k, v in artist_counter.most_common(40)]
    genre_cloud = [{"text": k, "weight": v} for k, v in genre_counter.most_common(20)]

    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    return {
        "updated_at": now,
        "chart_type": chart_type,
        "sample_size": len(sample),
        "summary": {
            "top_artists": artist_cloud[:10],
            "top_genres": genre_cloud[:10],
            "platform_heat": [{"text": k, "weight": v} for k, v in source_counter.most_common(30)],
        },
        "clouds": {
            "artist_cloud": artist_cloud,
            "genre_cloud": genre_cloud,
        },
        "songs": song_insights,
    }


def start_insight_job(overview: OverviewResponse, *, chart_type: str, sample_size: int) -> str:
    job_id = uuid.uuid4().hex
    _insight_jobs[job_id] = {
        "status": "running",
        "chart_type": chart_type,
        "sample_size": sample_size,
        "done": 0,
        "total": 0,
        "result": None,
        "error": None,
        "updated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }

    async def _run() -> None:
        async def _progress(done: int, total: int) -> None:
            st = _insight_jobs.get(job_id)
            if not st:
                return
            st["done"] = done
            st["total"] = total
            st["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        try:
            result = await build_overview_insights(
                overview,
                chart_type=chart_type,
                sample_size=sample_size,
                on_progress=_progress,
            )
            st = _insight_jobs.get(job_id)
            if st is not None:
                st["status"] = "done"
                st["result"] = result
                st["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        except Exception as e:
            st = _insight_jobs.get(job_id)
            if st is not None:
                st["status"] = "error"
                st["error"] = str(e)
                st["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    asyncio.create_task(_run())
    return job_id


def get_insight_job(job_id: str) -> dict | None:
    return _insight_jobs.get(job_id)

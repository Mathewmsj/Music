from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from app.chart_service import build_overview
from app.insights import (
    build_overview_insights,
    enrich_song,
    get_insight_job,
    start_insight_job,
)
from app.config import fusion_hot_n, fusion_new_n
from app.chart_api import (
    fetch_apple_chart,
    fetch_kugou_chart,
    fetch_migu_chart,
    fetch_netease_chart,
    fetch_qq_chart,
    list_apple_charts,
    list_kugou_charts,
    list_migu_charts,
    list_netease_charts,
    list_qq_charts,
)
from app.models import (
    ChartDetailResponse,
    ChartListResponse,
    OverviewResponse,
    chart_detail_to_json,
    chart_list_to_json,
    overview_to_json,
)
from app.platforms import PLATFORMS, get_platform

_cached: OverviewResponse | None = None
_cached_hot_n: int | None = None
_cached_new_n: int | None = None


def _fusion_n_param(request: Request, key: str, default: int) -> int:
    raw = request.query_params.get(key)
    if raw is None or raw.strip() == "":
        return max(1, min(default, 500))
    try:
        return max(1, min(int(raw), 500))
    except ValueError:
        return max(1, min(default, 500))


def _truthy(val: str | None) -> bool:
    if val is None:
        return False
    return val.strip().lower() in ("1", "true", "yes", "all")


@asynccontextmanager
async def lifespan(app: Starlette):
    global _cached, _cached_hot_n, _cached_new_n
    h = max(1, min(fusion_hot_n, 500))
    n = max(1, min(fusion_new_n, 500))
    try:
        _cached = await build_overview(h, n)
        _cached_hot_n = h
        _cached_new_n = n
    except Exception:
        _cached = None
        _cached_hot_n = None
        _cached_new_n = None
    yield


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def overview(request: Request) -> Response:
    global _cached, _cached_hot_n, _cached_new_n
    hn = _fusion_n_param(request, "hot_n", fusion_hot_n)
    nn = _fusion_n_param(request, "new_n", fusion_new_n)
    refresh = request.query_params.get("refresh", "").lower() in ("1", "true", "yes")
    if refresh or _cached is None or _cached_hot_n != hn or _cached_new_n != nn:
        try:
            _cached = await build_overview(hn, nn)
            _cached_hot_n = hn
            _cached_new_n = nn
        except Exception as e:
            if _cached is None:
                return JSONResponse({"error": f"拉取失败: {e}"}, status_code=500)
    return Response(
        content=json.dumps(overview_to_json(_cached), ensure_ascii=False),
        media_type="application/json; charset=utf-8",
    )


async def refresh(request: Request) -> Response:
    global _cached, _cached_hot_n, _cached_new_n
    hn = _fusion_n_param(request, "hot_n", fusion_hot_n)
    nn = _fusion_n_param(request, "new_n", fusion_new_n)
    try:
        _cached = await build_overview(hn, nn)
        _cached_hot_n = hn
        _cached_new_n = nn
    except Exception as e:
        if _cached is None:
            return JSONResponse({"error": f"刷新失败: {e}"}, status_code=500)
    return Response(
        content=json.dumps(overview_to_json(_cached), ensure_ascii=False),
        media_type="application/json; charset=utf-8",
    )


async def platforms(_: Request) -> JSONResponse:
    return JSONResponse({"platforms": [{"key": p.key, "name": p.name} for p in PLATFORMS]})


async def charts(request: Request) -> Response:
    key = (request.query_params.get("platform_key") or "").strip()
    p = get_platform(key)
    if not p:
        return JSONResponse({"error": "platform_key 无效"}, status_code=400)
    try:
        if key == "apple":
            resp: ChartListResponse = await list_apple_charts()
        elif key == "netease":
            resp = await list_netease_charts()
        elif key == "kugou":
            resp = await list_kugou_charts()
        elif key == "migu":
            resp = await list_migu_charts()
        elif key == "qq":
            resp = await list_qq_charts()
        else:
            return JSONResponse({"error": "该平台的榜单发现尚未实现"}, status_code=501)
        return Response(
            content=json.dumps(chart_list_to_json(resp), ensure_ascii=False),
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def chart_detail(request: Request) -> Response:
    key = (request.query_params.get("platform_key") or "").strip()
    chart_id = (request.query_params.get("chart_id") or "").strip()
    if not chart_id:
        return JSONResponse({"error": "chart_id 必填"}, status_code=400)
    p = get_platform(key)
    if not p:
        return JSONResponse({"error": "platform_key 无效"}, status_code=400)
    try:
        if key == "apple":
            resp: ChartDetailResponse = await fetch_apple_chart(chart_id)
        elif key == "netease":
            resp = await fetch_netease_chart(chart_id)
        elif key == "kugou":
            page_raw = (request.query_params.get("page") or "1").strip()
            try:
                page = max(1, int(page_raw))
            except ValueError:
                page = 1
            all_pages = _truthy(request.query_params.get("all_pages"))
            resp = await fetch_kugou_chart(chart_id, page=page, all_pages=all_pages)
        elif key == "migu":
            resp = await fetch_migu_chart(chart_id)
        elif key == "qq":
            all_pages = _truthy(request.query_params.get("all_pages"))
            resp = await fetch_qq_chart(chart_id, all_pages=all_pages)
        else:
            return JSONResponse({"error": "该平台的榜单详情尚未实现"}, status_code=501)
        return Response(
            content=json.dumps(chart_detail_to_json(resp), ensure_ascii=False),
            media_type="application/json; charset=utf-8",
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)




async def insights_overview(request: Request) -> Response:
    global _cached
    chart_type = (request.query_params.get("chart_type") or "hot").strip().lower()
    if chart_type not in ("hot", "new"):
        chart_type = "hot"
    size_raw = (request.query_params.get("sample_size") or "30").strip()
    try:
        sample_size = max(1, min(int(size_raw), 500))
    except ValueError:
        sample_size = 30
    if _cached is None:
        hn = max(1, min(fusion_hot_n, 500))
        nn = max(1, min(fusion_new_n, 500))
        _cached = await build_overview(hn, nn)
    data = await build_overview_insights(_cached, chart_type=chart_type, sample_size=sample_size)
    return Response(content=json.dumps(data, ensure_ascii=False), media_type="application/json; charset=utf-8")


async def insights_song(request: Request) -> Response:
    title = (request.query_params.get("title") or "").strip()
    artist = (request.query_params.get("artist") or "").strip()
    if not title:
        return JSONResponse({"error": "title 必填"}, status_code=400)
    data = await enrich_song(title, artist)
    return Response(content=json.dumps(data, ensure_ascii=False), media_type="application/json; charset=utf-8")


async def insights_start(request: Request) -> JSONResponse:
    global _cached
    chart_type = (request.query_params.get("chart_type") or "hot").strip().lower()
    if chart_type not in ("hot", "new"):
        chart_type = "hot"
    size_raw = (request.query_params.get("sample_size") or "30").strip()
    try:
        sample_size = max(1, min(int(size_raw), 500))
    except ValueError:
        sample_size = 30
    if _cached is None:
        hn = max(1, min(fusion_hot_n, 500))
        nn = max(1, min(fusion_new_n, 500))
        _cached = await build_overview(hn, nn)
    job_id = start_insight_job(_cached, chart_type=chart_type, sample_size=sample_size)
    return JSONResponse({"job_id": job_id, "status": "running"})


async def insights_status(request: Request) -> JSONResponse:
    job_id = (request.query_params.get("job_id") or "").strip()
    if not job_id:
        return JSONResponse({"error": "job_id 必填"}, status_code=400)
    data = get_insight_job(job_id)
    if not data:
        return JSONResponse({"error": "job 不存在"}, status_code=404)
    return JSONResponse(data)


routes: list[Route | Mount] = [
    Route("/api/health", endpoint=health, methods=["GET"]),
    Route("/api/overview", endpoint=overview, methods=["GET"]),
    Route("/api/refresh", endpoint=refresh, methods=["POST"]),
    Route("/api/platforms", endpoint=platforms, methods=["GET"]),
    Route("/api/charts", endpoint=charts, methods=["GET"]),
    Route("/api/chart", endpoint=chart_detail, methods=["GET"]),
    Route("/api/insights/overview", endpoint=insights_overview, methods=["GET"]),
    Route("/api/insights/song", endpoint=insights_song, methods=["GET"]),
    Route("/api/insights/start", endpoint=insights_start, methods=["POST"]),
    Route("/api/insights/status", endpoint=insights_status, methods=["GET"]),
]

_static = Path(__file__).resolve().parent / "static"
if _static.is_dir():
    routes.append(Mount("/", StaticFiles(directory=str(_static), html=True), name="static"))

app = Starlette(routes=routes, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

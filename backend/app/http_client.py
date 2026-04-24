from __future__ import annotations

import asyncio

import httpx

from app import config

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


async def get_json(url: str, *, params: dict | None = None, headers: dict | None = None) -> dict | list | None:
    if config.http_delay_ms > 0:
        await asyncio.sleep(config.http_delay_ms / 1000.0)
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        r = await client.get(url, params=params, headers=merged)
        r.raise_for_status()
        return r.json()


async def get_text(url: str, *, params: dict | None = None, headers: dict | None = None) -> str:
    if config.http_delay_ms > 0:
        await asyncio.sleep(config.http_delay_ms / 1000.0)
    merged = {**DEFAULT_HEADERS, **(headers or {})}
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        r = await client.get(url, params=params, headers=merged)
        r.raise_for_status()
        r.encoding = r.encoding or "utf-8"
        return r.text

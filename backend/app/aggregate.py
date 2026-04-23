from collections import defaultdict

from app.models import ChartPayload, ChartSong, FusedSong
from app.normalize import normalize_key


def _borda_points(rank: int, list_size: int) -> float:
    if list_size <= 0:
        return 0.0
    return float(list_size - rank + 1)


def fuse_charts(
    charts: list[ChartPayload], chart_type: str, *, fusion_top_n: int = 100
) -> list[FusedSong]:
    """
    Borda 计数融合：各平台榜单内排名越靠前得分越高；
    仅纳入 chart_type 匹配且 fetched_ok 的榜单。
    每平台已截取「目标长度」内歌曲；若某平台不足，则列表更短，Borda 分母 n 为该榜实际条数。
    融合结果输出前 fusion_top_n 名。
    """
    relevant: list[ChartPayload] = [
        c
        for c in charts
        if c.fetched_ok and c.chart_type == chart_type and len(c.songs) > 0
    ]
    scores: dict[str, float] = defaultdict(float)
    meta: dict[str, tuple[str, str, set[str]]] = {}
    for chart in relevant:
        n = len(chart.songs)
        for idx, s in enumerate(chart.songs, start=1):
            key = normalize_key(s.title, s.artist)
            if not key:
                continue
            scores[key] += _borda_points(idx, n)
            if key not in meta:
                meta[key] = (s.title, s.artist, set())
            meta[key][2].add(f"{chart.platform}:{chart.chart_name}")

    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    cap = max(1, min(fusion_top_n, 500))
    out: list[FusedSong] = []
    for i, (key, sc) in enumerate(ranked[:cap], start=1):
        title, artist, srcs = meta[key]
        out.append(
            FusedSong(
                fused_rank=i,
                title=title,
                artist=artist,
                score=round(sc, 2),
                appearances=len(srcs),
                sources=sorted(srcs),
            )
        )
    return out

from dataclasses import asdict, dataclass, field


@dataclass
class ChartSong:
    rank: int
    title: str
    artist: str
    platform: str
    chart_name: str
    extra: str | None = None


@dataclass
class ChartPayload:
    platform: str
    chart_name: str
    chart_type: str
    fetched_ok: bool
    error: str | None = None
    songs: list[ChartSong] = field(default_factory=list)


@dataclass
class FusedSong:
    fused_rank: int
    title: str
    artist: str
    score: float
    appearances: int
    sources: list[str]


@dataclass
class OverviewResponse:
    updated_at: str
    charts: list[ChartPayload]
    fused_hot: list[FusedSong]
    fused_new: list[FusedSong]
    fusion_hot_n: int = 100
    fusion_new_n: int = 100


@dataclass
class ChartMeta:
    platform_key: str
    platform: str
    chart_id: str
    chart_name: str
    chart_type: str
    source_url: str


@dataclass
class ChartListResponse:
    updated_at: str
    platform_key: str
    platform: str
    charts: list[ChartMeta]


@dataclass
class ChartDetailResponse:
    updated_at: str
    platform_key: str
    platform: str
    chart_id: str
    chart_name: str
    chart_type: str
    source_url: str
    fetched_ok: bool
    error: str | None = None
    songs: list[ChartSong] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def overview_to_json(obj: OverviewResponse) -> dict:
    def song_dict(s: ChartSong) -> dict:
        d = asdict(s)
        return d

    def chart_dict(c: ChartPayload) -> dict:
        return {
            "platform": c.platform,
            "chart_name": c.chart_name,
            "chart_type": c.chart_type,
            "fetched_ok": c.fetched_ok,
            "error": c.error,
            "songs": [song_dict(s) for s in c.songs],
        }

    def fused_dict(f: FusedSong) -> dict:
        return asdict(f)

    return {
        "updated_at": obj.updated_at,
        "charts": [chart_dict(c) for c in obj.charts],
        "fused_hot": [fused_dict(f) for f in obj.fused_hot],
        "fused_new": [fused_dict(f) for f in obj.fused_new],
        "fusion_hot_n": obj.fusion_hot_n,
        "fusion_new_n": obj.fusion_new_n,
    }


def chart_list_to_json(obj: ChartListResponse) -> dict:
    return {
        "updated_at": obj.updated_at,
        "platform_key": obj.platform_key,
        "platform": obj.platform,
        "charts": [asdict(c) for c in obj.charts],
    }


def chart_detail_to_json(obj: ChartDetailResponse) -> dict:
    d = {
        "updated_at": obj.updated_at,
        "platform_key": obj.platform_key,
        "platform": obj.platform,
        "chart_id": obj.chart_id,
        "chart_name": obj.chart_name,
        "chart_type": obj.chart_type,
        "source_url": obj.source_url,
        "fetched_ok": obj.fetched_ok,
        "error": obj.error,
        "songs": [asdict(s) for s in obj.songs],
    }
    if obj.meta:
        d["meta"] = obj.meta
    return d

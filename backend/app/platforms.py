from dataclasses import dataclass


@dataclass(frozen=True)
class Platform:
    key: str
    name: str


PLATFORMS: list[Platform] = [
    Platform("apple", "Apple Music"),
    Platform("netease", "网易云音乐"),
    Platform("qq", "QQ音乐"),
    Platform("kugou", "酷狗音乐"),
    Platform("migu", "咪咕音乐"),
]


def get_platform(key: str) -> Platform | None:
    for p in PLATFORMS:
        if p.key == key:
            return p
    return None

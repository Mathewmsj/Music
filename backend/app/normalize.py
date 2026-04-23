import re
import unicodedata


def normalize_key(title: str, artist: str) -> str:
    """用于跨平台去重：弱规范化歌名+艺人。"""
    t = unicodedata.normalize("NFKC", f"{title} {artist}")
    t = t.lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[\(\（].*?[\)\）]", " ", t)
    t = re.sub(r"[^\w\u4e00-\u9fff]", "", t)
    return t

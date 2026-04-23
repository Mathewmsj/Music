import os

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


spotify_client_id: str = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
spotify_client_secret: str = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
http_delay_ms: int = _int_env("HTTP_DELAY_MS", 200)

# 融合榜单：各平台参与 Borda 的条数上限（不足则按实际条数；融合输出长度同此）
fusion_hot_n: int = _int_env("FUSION_HOT_N", 100)
fusion_new_n: int = _int_env("FUSION_NEW_N", 100)

# QQ OpenAPI（可选，用于 fcg_music_custom_get_song_info_batch.fcg 流派字段）
qq_openapi_app_id: str = os.getenv("QQ_OPENAPI_APP_ID", "").strip()
qq_openapi_app_key: str = os.getenv("QQ_OPENAPI_APP_KEY", "").strip()

from app.providers.kugou import fetch_kugou_hot, fetch_kugou_new
from app.providers.migu import fetch_migu_hot, fetch_migu_new
from app.providers.netease import fetch_netease_hot, fetch_netease_new
from app.providers.qq import fetch_qq_hot, fetch_qq_new
from app.providers.apple_music import fetch_apple_hot, fetch_apple_new

__all__ = [
    "fetch_netease_hot",
    "fetch_netease_new",
    "fetch_qq_hot",
    "fetch_qq_new",
    "fetch_kugou_hot",
    "fetch_kugou_new",
    "fetch_migu_hot",
    "fetch_migu_new",
    "fetch_apple_hot",
    "fetch_apple_new",
]

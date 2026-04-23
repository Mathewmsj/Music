# API字段全量手册

> 本手册基于你给定的 QQ 音乐与网易云开发者文档实时整理。
> 重点覆盖：**调用方式、字段结构、用途、可扩展采集模板**。

## 1. 统一字段模板（每个接口按此记录）

| 字段 | 含义 |
|---|---|
| 平台 | QQ音乐 / 网易云 |
| 分类 | 如：歌曲API、搜索API、登录API |
| 接口名称 | 文档中的接口标题 |
| 请求路径 | `/openapi/...` 或 QQ `opi_cmd` |
| 请求方式 | GET / POST |
| 鉴权字段 | appId/appKey/accessToken/sign/timestamp 等 |
| 业务参数 | bizContent 或 query 参数 |
| 返回核心字段 | 业务 data 下关键字段 |
| 状态码 | code/subCode/错误码 |
| 用途 | 页面展示、播放、搜索、推荐、资产等 |

## 2. QQ音乐 OpenAPI（字段级）

### 2.1 调用方式
```text
GET https://openrpc.music.qq.com/rpc_proxy/fcgi-bin/music_open_api.fcg
  ?opi_cmd=<命令字>
  &app_id=<应用ID>
  &app_key=<应用Key>
  &timestamp=<秒级时间戳>
  &sign=<签名>
  &<业务参数>
```

### 2.2 接口：获取热词列表（4.17.1）
| 字段 | 内容 |
|---|---|
| 接口名称 | 获取热词列表 |
| 请求路径 | `music_open_api.fcg` + `opi_cmd=fcg_music_custom_get_hotkeylist.fcg` |
| 请求方式 | GET（文档示例） |
| 必要公共参数 | `app_id`, `app_key`, `timestamp`, `sign` |
| 业务参数 | `type`（不传或非法值返回热门搜索） |
| 返回 | 热词列表结构（含排序/类型等语义字段） |
| 用途 | 搜索框热词、运营热搜、推荐引导词 |

## 3. 网易云 OpenAPI（字段级）

### 3.1 调用方式
```text
GET/POST http://openapi.music.163.com/openapi/<path>
公共参数: appId, signType, accessToken, timestamp, device...
业务参数: bizContent={...}
```

### 3.2 代表接口：获取歌曲详情
| 字段 | 内容 |
|---|---|
| 请求路径 | `/openapi/music/basic/song/detail/get/v2` |
| 请求方式 | GET/POST |
| 业务参数（必填） | `songId:String`, `withUrl:Boolean` |
| 业务参数（可选） | `bitrate:Int`, `effects:String`, `qualityFlag:Boolean`, `languageFlag:Boolean`, `extFlags:String` |
| 返回字段（核心） | `id,name,duration,albumName,artists,playUrl,playFlag,downloadFlag,vipFlag,songFee,qualities,chorusMeta,visible` |
| 状态码 | `code=200`; `subCode=200` 有数据；`subCode=10007` 资源不存在 |
| 用途 | 歌曲详情页、播放器前置信息、版权与权限判断 |

### 3.3 枚举/结构体字段补充（来自官方示例）
- `songFee`: 0免费 / 1会员 / 4数字专辑 / 8限免码率 / 16付费下载 / 32付费播放
- 音质等级: `standard(128)`, `higher(192)`, `exhigh(320)`, `lossless(999)`, `hires(1999)` 等
- `originCoverType`: 0未知 / 1原唱 / 2翻唱
- `chorusMeta`: `startTime`, `endTime`（毫秒）

## 4. 网易云接口目录（已采集到的全量路径）

> 当前自动采集到接口路径 **190** 条。

| 序号 | 请求路径 | 主要用途（归纳） |
|---:|---|---|
| 1 | `/openapi/dj/program/collect/list` | 音乐业务能力（见分类） |
| 2 | `/openapi/dj/program/collect/status` | 音乐业务能力（见分类） |
| 3 | `/openapi/dj/program/info/list` | 音乐业务能力（见分类） |
| 4 | `/openapi/dj/program/news/fall/list` | 音乐业务能力（见分类） |
| 5 | `/openapi/dj/program/news/quick/ai/talk` | 音乐业务能力（见分类） |
| 6 | `/openapi/dj/program/news/quick/ai_talk` | 音乐业务能力（见分类） |
| 7 | `/openapi/dj/program/news/quick/paper/lastest` | 音乐业务能力（见分类） |
| 8 | `/openapi/dj/program/news/quick/timelength/voice` | 音乐业务能力（见分类） |
| 9 | `/openapi/dj/program/playurl/get` | 播放地址或播放行为 |
| 10 | `/openapi/dj/program/song/list` | 歌曲信息/播放相关 |
| 11 | `/openapi/djradio/play/progress/record/list` | 播放地址或播放行为 |
| 12 | `/openapi/music/banner/get` | 音乐业务能力（见分类） |
| 13 | `/openapi/music/basic/action/aidj/audio/get` | 音乐业务能力（见分类） |
| 14 | `/openapi/music/basic/aidj/audio/timbre/get` | 音乐业务能力（见分类） |
| 15 | `/openapi/music/basic/album/detail/get/v2` | 专辑信息/收藏 |
| 16 | `/openapi/music/basic/album/paid/get/v2` | 专辑信息/收藏 |
| 17 | `/openapi/music/basic/album/play/record/list` | 专辑信息/收藏 |
| 18 | `/openapi/music/basic/album/song/list/get/v2` | 歌曲信息/播放相关 |
| 19 | `/openapi/music/basic/album/song/list/get/v3` | 歌曲信息/播放相关 |
| 20 | `/openapi/music/basic/album/sub` | 专辑信息/收藏 |
| 21 | `/openapi/music/basic/album/subed/get/v2` | 专辑信息/收藏 |
| 22 | `/openapi/music/basic/album/unsub` | 专辑信息/收藏 |
| 23 | `/openapi/music/basic/artist/detail/get/v2` | 艺人信息 |
| 24 | `/openapi/music/basic/artist/list/get` | 艺人信息 |
| 25 | `/openapi/music/basic/artist/subed/get/v2` | 艺人信息 |
| 26 | `/openapi/music/basic/artist/zone/get/by/tab` | 艺人信息 |
| 27 | `/openapi/music/basic/artist/zone/tab/list` | 艺人信息 |
| 28 | `/openapi/music/basic/artists/album/list/bytype/get/v3` | 专辑信息/收藏 |
| 29 | `/openapi/music/basic/artists/hotsong/list/get/v2` | 艺人信息 |
| 30 | `/openapi/music/basic/artists/list/bytype/get/v2` | 艺人信息 |
| 31 | `/openapi/music/basic/artists/list/bytype/get/v3` | 艺人信息 |
| 32 | `/openapi/music/basic/artists/song/list/get` | 歌曲信息/播放相关 |
| 33 | `/openapi/music/basic/batch/play/data/record` | 播放地址或播放行为 |
| 34 | `/openapi/music/basic/batch/song/playurl/get` | 歌曲信息/播放相关 |
| 35 | `/openapi/music/basic/comment/calendar/get` | 音乐业务能力（见分类） |
| 36 | `/openapi/music/basic/comments/get/v2` | 音乐业务能力（见分类） |
| 37 | `/openapi/music/basic/complex/search` | 音乐业务能力（见分类） |
| 38 | `/openapi/music/basic/dolby/list/get/v2` | 音乐业务能力（见分类） |
| 39 | `/openapi/music/basic/dolby/list/get/v3` | 音乐业务能力（见分类） |
| 40 | `/openapi/music/basic/hi/res/get` | 音乐业务能力（见分类） |
| 41 | `/openapi/music/basic/httpdns/d` | 音乐业务能力（见分类） |
| 42 | `/openapi/music/basic/link/page/rcmd/resource/show` | 音乐业务能力（见分类） |
| 43 | `/openapi/music/basic/mix/recent/get` | 音乐业务能力（见分类） |
| 44 | `/openapi/music/basic/oauth2/device/login/qrcode/get` | 登录鉴权 |
| 45 | `/openapi/music/basic/oauth2/login/anonymous` | 登录鉴权 |
| 46 | `/openapi/music/basic/play/data/record` | 播放地址或播放行为 |
| 47 | `/openapi/music/basic/playlist/created/get/v2` | 歌单查询/维护 |
| 48 | `/openapi/music/basic/playlist/detail/get/v2` | 歌单查询/维护 |
| 49 | `/openapi/music/basic/playlist/detail/list` | 歌单查询/维护 |
| 50 | `/openapi/music/basic/playlist/oftag/get/v2` | 歌单查询/维护 |
| 51 | `/openapi/music/basic/playlist/play/record/list` | 歌单查询/维护 |
| 52 | `/openapi/music/basic/playlist/radar/get` | 歌单查询/维护 |
| 53 | `/openapi/music/basic/playlist/song/batch/delete` | 歌曲信息/播放相关 |
| 54 | `/openapi/music/basic/playlist/song/batch/like` | 歌曲信息/播放相关 |
| 55 | `/openapi/music/basic/playlist/song/like/v2` | 歌曲信息/播放相关 |
| 56 | `/openapi/music/basic/playlist/song/list/get/v2` | 歌曲信息/播放相关 |
| 57 | `/openapi/music/basic/playlist/song/list/get/v3` | 歌曲信息/播放相关 |
| 58 | `/openapi/music/basic/playlist/song/list/get/v4` | 歌曲信息/播放相关 |
| 59 | `/openapi/music/basic/playlist/square/tag/get` | 歌单查询/维护 |
| 60 | `/openapi/music/basic/playlist/star/get/v2` | 歌单查询/维护 |
| 61 | `/openapi/music/basic/playlist/sub/v2` | 歌单查询/维护 |
| 62 | `/openapi/music/basic/playlist/subed/get/v2` | 歌单查询/维护 |
| 63 | `/openapi/music/basic/playlist/tag/get/v2` | 歌单查询/维护 |
| 64 | `/openapi/music/basic/playlist/unsub/v2` | 歌单查询/维护 |
| 65 | `/openapi/music/basic/private/cloud/song/list/get` | 歌曲信息/播放相关 |
| 66 | `/openapi/music/basic/private/fm/roaming/category` | 音乐业务能力（见分类） |
| 67 | `/openapi/music/basic/private/fm/roaming/song/list` | 歌曲信息/播放相关 |
| 68 | `/openapi/music/basic/query/song/record/get` | 歌曲信息/播放相关 |
| 69 | `/openapi/music/basic/radio/fm/get/v2` | 音乐业务能力（见分类） |
| 70 | `/openapi/music/basic/radio/tag/fm/get/v2` | 音乐业务能力（见分类） |
| 71 | `/openapi/music/basic/recommend/daily/image` | 音乐业务能力（见分类） |
| 72 | `/openapi/music/basic/recommend/daily/mix` | 音乐业务能力（见分类） |
| 73 | `/openapi/music/basic/recommend/miyue/song/list/get` | 歌曲信息/播放相关 |
| 74 | `/openapi/music/basic/recommend/more/song` | 音乐业务能力（见分类） |
| 75 | `/openapi/music/basic/recommend/playlist/ge` | 歌单查询/维护 |
| 76 | `/openapi/music/basic/recommend/playlist/get` | 歌单查询/维护 |
| 77 | `/openapi/music/basic/recommend/songlist/get/v2` | 音乐业务能力（见分类） |
| 78 | `/openapi/music/basic/recommend/style/songlist/get` | 音乐业务能力（见分类） |
| 79 | `/openapi/music/basic/scene/radio/get` | 音乐业务能力（见分类） |
| 80 | `/openapi/music/basic/scene/radio/tags/get` | 音乐业务能力（见分类） |
| 81 | `/openapi/music/basic/search/album/get/v2` | 搜索/联想/召回 |
| 82 | `/openapi/music/basic/search/artists/get/v2` | 搜索/联想/召回 |
| 83 | `/openapi/music/basic/search/charts/list/get` | 搜索/联想/召回 |
| 84 | `/openapi/music/basic/search/hot/keyword/get/v2` | 搜索/联想/召回 |
| 85 | `/openapi/music/basic/search/playlist/bytag/get/v2` | 搜索/联想/召回 |
| 86 | `/openapi/music/basic/search/playlist/get/v2` | 搜索/联想/召回 |
| 87 | `/openapi/music/basic/search/song/by/album/artist/get/v2` | 搜索/联想/召回 |
| 88 | `/openapi/music/basic/search/song/by/artist/song/get/v2` | 搜索/联想/召回 |
| 89 | `/openapi/music/basic/search/song/byartist/get/v2` | 搜索/联想/召回 |
| 90 | `/openapi/music/basic/search/song/get/v2` | 搜索/联想/召回 |
| 91 | `/openapi/music/basic/search/song/get/v3` | 搜索/联想/召回 |
| 92 | `/openapi/music/basic/search/suggest/keyword/get/v2` | 搜索/联想/召回 |
| 93 | `/openapi/music/basic/song/aidj/audio/get` | 歌曲信息/播放相关 |
| 94 | `/openapi/music/basic/song/aidj/chat/rcmd` | 歌曲信息/播放相关 |
| 95 | `/openapi/music/basic/song/bpm/get` | 歌曲信息/播放相关 |
| 96 | `/openapi/music/basic/song/cio/detail/get` | 歌曲信息/播放相关 |
| 97 | `/openapi/music/basic/song/daily/style/get` | 歌曲信息/播放相关 |
| 98 | `/openapi/music/basic/song/detail/get/v2` | 歌曲信息/播放相关 |
| 99 | `/openapi/music/basic/song/download/count/get` | 歌曲信息/播放相关 |
| 100 | `/openapi/music/basic/song/downloadurl/get/v2` | 歌曲信息/播放相关 |
| 101 | `/openapi/music/basic/song/freely/sing/detail` | 歌曲信息/播放相关 |
| 102 | `/openapi/music/basic/song/freely/sing/get` | 歌曲信息/播放相关 |
| 103 | `/openapi/music/basic/song/list/get/v2` | 歌曲信息/播放相关 |
| 104 | `/openapi/music/basic/song/listen/type/get` | 歌曲信息/播放相关 |
| 105 | `/openapi/music/basic/song/lyric/get/v2` | 歌曲信息/播放相关 |
| 106 | `/openapi/music/basic/song/lyric/word/by/word/get` | 歌曲信息/播放相关 |
| 107 | `/openapi/music/basic/song/music/quality/sound/get` | 歌曲信息/播放相关 |
| 108 | `/openapi/music/basic/song/music/quality/sound/sp/get` | 歌曲信息/播放相关 |
| 109 | `/openapi/music/basic/song/paid/get` | 歌曲信息/播放相关 |
| 110 | `/openapi/music/basic/song/play/intelligence/get` | 歌曲信息/播放相关 |
| 111 | `/openapi/music/basic/song/play/record/list` | 歌曲信息/播放相关 |
| 112 | `/openapi/music/basic/song/playurl/get/v2` | 歌曲信息/播放相关 |
| 113 | `/openapi/music/basic/song/quality/interests/get` | 歌曲信息/播放相关 |
| 114 | `/openapi/music/basic/song/quality/interests/start` | 歌曲信息/播放相关 |
| 115 | `/openapi/music/basic/song/text/download/get/v2` | 歌曲信息/播放相关 |
| 116 | `/openapi/music/basic/song/text/play/get/v2` | 歌曲信息/播放相关 |
| 117 | `/openapi/music/basic/sound/effect/list` | 音乐业务能力（见分类） |
| 118 | `/openapi/music/basic/toplist/get/v2` | 音乐业务能力（见分类） |
| 119 | `/openapi/music/basic/user/id/info` | 音乐业务能力（见分类） |
| 120 | `/openapi/music/basic/user/oauth2/qrcodekey/get/v2` | 音乐业务能力（见分类） |
| 121 | `/openapi/music/basic/user/oauth2/token/get/v2` | 登录鉴权 |
| 122 | `/openapi/music/basic/user/oauth2/token/refresh/v2` | 登录鉴权 |
| 123 | `/openapi/music/basic/user/profile/get/v2` | 音乐业务能力（见分类） |
| 124 | `/openapi/music/basic/voice/assistant/multi/search` | 音乐业务能力（见分类） |
| 125 | `/openapi/music/basic/yida/hifi/get` | 音乐业务能力（见分类） |
| 126 | `/openapi/music/basic/yida/hifi/module/get` | 音乐业务能力（见分类） |
| 127 | `/openapi/music/basic/yida/page/get` | 音乐业务能力（见分类） |
| 128 | `/openapi/music/comment/get-best-comments-by-song` | 音乐业务能力（见分类） |
| 129 | `/openapi/music/comment/user/get-user-comments-by-song` | 音乐业务能力（见分类） |
| 130 | `/openapi/music/common/recently/heard/get` | 音乐业务能力（见分类） |
| 131 | `/openapi/music/heart/beat/widget/get` | 音乐业务能力（见分类） |
| 132 | `/openapi/music/interest/trial/card/get` | 音乐业务能力（见分类） |
| 133 | `/openapi/music/interest/trial/card/obtained` | 音乐业务能力（见分类） |
| 134 | `/openapi/music/multi/reconnect/play/info/get` | 播放地址或播放行为 |
| 135 | `/openapi/music/multi/reconnect/play/report` | 播放地址或播放行为 |
| 136 | `/openapi/music/orpheus/get/v2` | 音乐业务能力（见分类） |
| 137 | `/openapi/music/resource/comment/reply/list/asc` | 音乐业务能力（见分类） |
| 138 | `/openapi/music/resource/short/url/get` | 音乐业务能力（见分类） |
| 139 | `/openapi/music/search/` | 搜索/联想/召回 |
| 140 | `/openapi/music/song/simulation/get` | 歌曲信息/播放相关 |
| 141 | `/openapi/podcast/ai/custom/radio/produce/again` | 音乐业务能力（见分类） |
| 142 | `/openapi/podcast/ai/custom/radio/save` | 音乐业务能力（见分类） |
| 143 | `/openapi/podcast/ai/custom/radio/static/data/get` | 音乐业务能力（见分类） |
| 144 | `/openapi/podcast/ai/custom/radio/status/get` | 音乐业务能力（见分类） |
| 145 | `/openapi/podcast/ai/custom/radio/user/data/get` | 音乐业务能力（见分类） |
| 146 | `/openapi/podcast/block/content/list` | 音乐业务能力（见分类） |
| 147 | `/openapi/podcast/block/list` | 音乐业务能力（见分类） |
| 148 | `/openapi/podcast/block/module/content` | 音乐业务能力（见分类） |
| 149 | `/openapi/podcast/block/page` | 音乐业务能力（见分类） |
| 150 | `/openapi/podcast/block/page/modules` | 音乐业务能力（见分类） |
| 151 | `/openapi/podcast/download/url/get/v1` | 下载地址/下载权益 |
| 152 | `/openapi/podcast/fallspage/my/collect` | 音乐业务能力（见分类） |
| 153 | `/openapi/podcast/fallspage/my/page/list` | 音乐业务能力（见分类） |
| 154 | `/openapi/podcast/my/collect/count` | 音乐业务能力（见分类） |
| 155 | `/openapi/podcast/my/created/voicelist` | 音乐业务能力（见分类） |
| 156 | `/openapi/podcast/play/url/get/v1` | 播放地址或播放行为 |
| 157 | `/openapi/podcast/ranklist/charts/get` | 音乐业务能力（见分类） |
| 158 | `/openapi/podcast/ranklist/square/ranklist/get` | 音乐业务能力（见分类） |
| 159 | `/openapi/podcast/ranklist/voice/charts/get` | 音乐业务能力（见分类） |
| 160 | `/openapi/podcast/recommend/guess/like/radio/list` | 音乐业务能力（见分类） |
| 161 | `/openapi/podcast/scene/fm/list` | 音乐业务能力（见分类） |
| 162 | `/openapi/podcast/scene/fm/private/podcast/voices` | 音乐业务能力（见分类） |
| 163 | `/openapi/podcast/scene/fm/voice/list` | 音乐业务能力（见分类） |
| 164 | `/openapi/podcast/song/block` | 歌曲信息/播放相关 |
| 165 | `/openapi/podcast/subscribe` | 音乐业务能力（见分类） |
| 166 | `/openapi/podcast/unSubscribe` | 音乐业务能力（见分类） |
| 167 | `/openapi/podcast/unsubscribe` | 音乐业务能力（见分类） |
| 168 | `/openapi/radio/gold/sentences/query` | 音乐业务能力（见分类） |
| 169 | `/openapi/score/queryMonthReporPic` | 音乐业务能力（见分类） |
| 170 | `/openapi/search/multi/terminal/program` | 搜索/联想/召回 |
| 171 | `/openapi/search/multi/terminal/voicelist` | 搜索/联想/召回 |
| 172 | `/openapi/stream/common/ai/playlist/create` | 歌单查询/维护 |
| 173 | `/openapi/stream/common/ai/search` | 音乐业务能力（见分类） |
| 174 | `/openapi/v1/resource/comments/add` | 音乐业务能力（见分类） |
| 175 | `/openapi/v1/resource/comments/reply` | 音乐业务能力（见分类） |
| 176 | `/openapi/voice/category/rcmd/program` | 音乐业务能力（见分类） |
| 177 | `/openapi/voice/category/rcmd/voice` | 音乐业务能力（见分类） |
| 178 | `/openapi/voice/category/second` | 音乐业务能力（见分类） |
| 179 | `/openapi/voice/category/top` | 音乐业务能力（见分类） |
| 180 | `/openapi/voice/category/voice` | 音乐业务能力（见分类） |
| 181 | `/openapi/voice/fall/list` | 音乐业务能力（见分类） |
| 182 | `/openapi/voice/get/voicelist` | 音乐业务能力（见分类） |
| 183 | `/openapi/voice/list` | 音乐业务能力（见分类） |
| 184 | `/openapi/voice/play/record/list` | 播放地址或播放行为 |
| 185 | `/openapi/voice/sati/resource/list` | 音乐业务能力（见分类） |
| 186 | `/openapi/voice/sati/resource/query` | 音乐业务能力（见分类） |
| 187 | `/openapi/voice/sati/tag/list` | 音乐业务能力（见分类） |
| 188 | `/openapi/voice/similar` | 音乐业务能力（见分类） |
| 189 | `/openapi/voicebook/play/progress/record/list` | 播放地址或播放行为 |
| 190 | `/openapi/voicelist/bought/list` | 音乐业务能力（见分类） |

## 5. 网易云接口标题目录（按文档栏目抓取）

> 当前自动采集到接口/栏目标题 **217** 条。

- 音乐API文档
- 播客API文档
- 定制API文档
- CMAPI文档
- 用户登录API
- 匿名登录
- 获取登录二维码
- 轮询二维码状态
- 获取用户基本信息
- H5登录&唤端登录
- 刷新AccessToken
- 推荐-歌曲类API
- 每日推荐封面
- 获取相似歌曲（新）
- 推荐更多歌曲
- 获取场景音乐标签
- 获取场景音乐标签下的歌曲
- 每日推荐
- 推荐-歌单类API
- 获取推荐歌单列表
- 获取雷达歌单
- 获取榜单列表
- 获取banner资源
- 获取相似歌曲-歌曲列表（日推mix）
- 获取风格日推-歌曲列表（日推mix）
- 获取相似艺人-歌曲列表（日推mix）
- 私人漫游API
- 获取私人漫游场景模式
- 获取私人漫游(不建议使用)
- 获取私人漫游场景歌曲
- 歌单广场API
- 获取歌单标签
- 根据标签获取歌单
- 获取歌单指定标签（新版）
- 查询歌单及歌曲API
- 获取歌单详情
- 批量查询歌单详情
- 获取歌单里的歌曲列表
- 查询歌曲API
- 获取歌曲音质
- 批量获取歌曲信息
- 获取歌词
- 获取歌曲音质（新版）
- 获取逐字歌词
- 获取歌曲详情
- 获取播放地址API
- 获取歌曲播放url
- 批量获取歌曲播放url
- 获取歌曲无法播放toast文案
- 获取下载地址API
- 获取歌曲下载url
- 获取用户下载总数
- 获取歌曲无法下载toast文案
- 文字搜索API
- 获取热搜榜
- 获取搜索热词
- 获取搜索提示词
- 根据关键字综合搜索
- 根据关键字搜索歌曲
- 根据关键字搜索歌单
- 根据关键字搜索专辑
- 根据关键字搜索歌手
- 根据标签搜索歌单
- 根据艺人关键字搜索歌曲（不建议使用）
- 根据艺人名、歌曲名搜索歌曲信息（不建议使用）
- 根据艺人、专辑关键字搜索专辑列表(不建议使用)
- 语音搜索API
- 根据多槽位搜索歌曲
- AI原文搜索（不拆槽）
- 获取播放记录API
- 获取最近播放歌单列表
- 获取最近播放专辑列表
- 获取听歌排行数据
- 获取近期内容推荐
- 获取最近播放歌曲列表
- 用户资产API
- 获取用户已购歌曲
- 获取用户已购专辑
- 获取用户网盘歌曲
- 播放数据回传API
- 音乐/长音频播放数据回传
- 艺人API
- 获取用户收藏的艺人
- 获取艺人详情
- 批量查询艺人详情
- 分页获取艺人下的热门歌曲列表
- 获取艺人下的热门歌曲列表
- 获取艺人下的专辑列表
- 根据分类获取艺人列表v2（不建议使用）
- 根据分类获取艺人列表v3（不建议使用）
- 专辑API
- 收藏专辑
- 取消收藏专辑
- 获取专辑详情
- 分页获取专辑下的歌曲列表
- 获取专辑下的歌曲列表
- 获取用户收藏的专辑列表
- 高品质专区
- 获取Vivid歌单
- 获取Suno Ai内容
- 获取HiFi专区指定模块
- 获取杜比内容v3
- 获取杜比内容v2
- 获取hires内容
- 获取首页混搭页面
- 获取HiFi专区
- 收藏&创建API
- 用户取消收藏歌单
- 添加或删除红心歌曲
- 获取用户收藏的歌单列表
- 批量删除歌单内歌曲
- 获取用户红心歌单
- 获取用户创建的歌单列表
- 用户收藏歌单
- 批量添加歌曲到歌单
- 会员API
- H5收银台
- 二维码弹窗收银台
- 开放平台智能搜推
- 开放平台一句话歌单
- 跨端续播API
- 跨端续播-查询
- 跨端续播-上报
- 获取歌单里的歌曲列表v4
- 随心唱API
- 随心唱-歌曲是否支持干声（人声）
- 随心唱-歌曲获取音频详情
- 获取音色列表
- 获取歌曲口播信息
- 获取行为口播信息（暂不支持）
- 评论API
- 获取歌曲热门评论
- 音质体验卡API
- 获取体验卡
- 领取和使用体验卡
- 音质限免API
- 音质限免开启
- 音质限免查询
- API错误码
- 登录相关
- 推荐
- 艺人
- 搜索
- 评论
- HiFi专区
- 歌单
- 专辑
- 播放器
- 音质&音效
- 杜比专区
- CMAPI申请
- CMAPI接口文档
- API调用
- 播客付费能力API
- 搜索API
- 搜索播客
- 搜索声音
- 播客分类API
- 获取一级分类
- 获取二级分类
- 查询分类下的推荐的播单
- 播客模块资源API
- 获取模块下资源列表
- 获取模块列表
- 获取页面模块列表
- 获取播客模块列表与资源
- 播客推荐API
- 获取本周上新模块资源
- 获取音乐电台模块资源
- 获取播单的相关推荐
- 根据歌曲id获取音乐播客声音推荐
- 获取猜你喜欢的播单
- 查询播单及单集（声音）API
- 查询单集（声音）API
- 获取声音播放地址（不建议使用）
- 获取声音播放地址（新版）
- 获取声音下载地址
- 获取播客播放记录
- 获取单集（声音）播放记录
- 获取有声书播放记录
- 跨端续播查询
- 跨端续播上报
- 播客播放数据回传API
- 播放数据回传（type：dj）
- 查询用户资产API
- 获取用户已购播客/有声书
- 故事推荐语API
- 获取故事金句列表
- 播客收藏API
- 用户收藏播客
- 用户取消收藏播客
- 获取我创建的播客
- 获取我的播客(分类获取)
- 查询我收藏的播客个数
- 收藏的播客list(瀑布流获取)
- 查询播客单集收藏列表
- 批量判断声音收藏状态
- 助眠解压API
- 根据tag获取助眠解压资源
- 获取助眠解压分类标签
- 根据ids批量获取助眠解压资源
- 播客榜单API
- 获取播客排行榜列表（播单/声音）
- 播客AI快讯API
- 根据声音id获取快讯播放地址
- 获取最近的每日早晚报
- 获取AI对谈资讯节目
- 根据分类获取AI快讯
- 播客个性化日报API
- 播客随心听FM电台API
- 获取私人播客场景fm
- 获取推荐场景列表
- 获取推荐声音资源
- 歌曲物料推送
- 移动端评论API
- 歌曲用户评论
- 获取评论

## 6. 后续补全脚本说明（将每条接口展开到字段级）

下一步可按以下流程自动补全：
1. 先从分类接口拿每个文档 `docId`。
2. 对每个 `docId` 调 `.../apidoc/get?docId=...`。
3. 解析 `extInfo` 的参数表，落盘到本手册的接口章节。
4. 生成“可调用样例（curl/JS）+ 错误码索引 + 字段字典”。

## 7. 参考链接

- https://developer.y.qq.com/docs/openapi#/feature/hotkey
- https://developer.music.163.com/st/developer/document?docId=8e96f389dfc74fcb97af35d1597be77e
- https://interface.music.163.com/api/openplatform/developer/apidoc/get?docId=8e96f389dfc74fcb97af35d1597be77e
- https://interface.music.163.com/api/openplatform/developer/api/doc/category
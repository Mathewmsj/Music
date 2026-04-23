# QQ音乐 & 网易云开发者文档 API 调用方式与用途总结（完整版）

> 阅读来源：
> - https://developer.y.qq.com/docs/openapi#/feature/hotkey
> - https://developer.music.163.com/st/developer/document?docId=8e96f389dfc74fcb97af35d1597be77e
> - https://interface.music.163.com/api/openplatform/developer/apidoc/get?docId=8e96f389dfc74fcb97af35d1597be77e
> - https://interface.music.163.com/api/openplatform/developer/api/doc/category

---

## 1. QQ音乐开发者平台（OpenAPI）

## 1.1 API 调用方式（总则）

从文档可见，QQ OpenAPI 的调用以 HTTP 请求为主，示例风格为：

- 基础网关：`https://openrpc.music.qq.com/rpc_proxy/fcgi-bin/music_open_api.fcg`
- 通过 `opi_cmd` 指定具体能力
- 常见公共参数：`app_id`、`app_key`、`timestamp`、`sign`
- 业务参数按接口追加（例如 `type`）

示例（文档中的热词接口）：

`https://openrpc.music.qq.com/rpc_proxy/fcgi-bin/music_open_api.fcg?opi_cmd=fcg_music_custom_get_hotkeylist.fcg&app_id=xxxxxxxxxxx&app_key=xxxxxxxxxxx&timestamp=1555067641&sign=xxxxxxxxx&type=1`

## 1.2 当前文档中可见的功能分类（用于“调用用途”归纳）

- 会员类
- MV类
- 搜索类
- 歌单类
- 歌曲类
- 榜单类
- 专辑类
- 歌手类
- 推荐类
- 长音频
- 最近播放
- 获取搜索热词
- 运营专区
- 电台类
- 工具类
- AI类
- 不建议使用列表
- 上报与监控

## 1.3 代表接口：获取搜索热词（4.17.1）

- 接口用途：根据 `type` 获取对应搜索热词列表
- 命令字（`opi_cmd`）：`fcg_music_custom_get_hotkeylist.fcg`
- 业务参数：`type`（文档说明不传或不在指定范围时返回热门搜索）
- 返回用途：提供热词结构（用于搜索入口推荐、热榜展示、引导词）

---

## 2. 网易云开发者平台（音乐 API）

## 2.1 API 调用方式（总则）

从官方文档页与接口详情可确认：

- 统一域名风格：`http://openapi.music.163.com/openapi/...`
- 请求方式：大量接口支持 `GET/POST`
- 调用模型：
  - 公共参数（文档称 IOT 公共参数）
  - `bizContent` 作为业务参数 JSON
- 鉴权与签名字段在示例中出现：`appId`、`signType`、`accessToken`、`timestamp`、`device` 等

## 2.2 代表接口（完整参数级）：获取歌曲详情

- 接口：`/openapi/music/basic/song/detail/get/v2`
- 请求方式：`GET/POST`
- 核心用途：按歌曲 ID 查询歌曲详情，可选返回播放 URL、音质、语种、副歌信息

业务参数（节选）：

- `songId`（必填，String）：歌曲 ID
- `withUrl`（必填，Boolean）：是否返回播放 URL
- `bitrate`（选填，Int）：码率（128/192/320/999/1999）
- `effects`（选填，String）：音效（如杜比）
- `qualityFlag`（选填，Boolean）：是否返回音质信息
- `languageFlag`（选填，Boolean）：是否返回语种
- `extFlags`（选填，String）：是否返回副歌起止点（固定字段）

返回用途（节选）：

- 版权与可播判断：`playFlag`、`visible`
- 会员与付费判断：`vipFlag`、`songFee`、`payed`
- 音频能力：`br`、`qualities`、`effects`
- 内容展示：`name`、`albumName`、`artists/fullArtists`、`coverImgUrl`

状态语义（文档示例）：

- `code=200`：请求正常
- `subCode=200`：有数据
- `subCode=10007`：资源不存在

---

## 3. 网易云 API 分类与用途总表（按文档目录整理）

> 以下为你要求的“API 调取方式和用途”中的“全量能力目录”。
> 调取方式统一采用网易云 OpenAPI（`GET/POST + 公共参数 + bizContent`），每条给出用途归纳。

| 分类 | 典型接口 | 用途 |
|---|---|---|
| 公共 | 访问方式、HTTPDNS接入、公共错误码、IOT端公共参数 | 提供调用规范、网络接入、错误处理与公共参数标准 |
| 用户登录API | 匿名登录、获取登录二维码、轮询二维码状态、H5登录、回调code换token、刷新AccessToken | 完成用户身份建立、授权换票据、token续期 |
| 推荐-歌曲类API | 每日推荐、相似歌曲、推荐更多歌曲、场景音乐标签 | 构建个性化/场景化歌曲推荐 |
| 推荐-歌单类API | 获取推荐歌单、雷达歌单、榜单列表、banner资源 | 首页推荐流、运营位与榜单分发 |
| 日推MIX | 日推mix、相似歌曲列表、风格日推、相似艺人歌曲 | 构建连续推荐播放流 |
| 私人漫游API | 获取私人漫游场景模式、场景歌曲 | 按场景持续推荐 |
| 歌单广场API | 获取歌单标签、按标签取歌单 | 歌单发现页与分类浏览 |
| 查询歌单及歌曲API | 获取歌单详情、歌单歌曲列表、批量歌单详情 | 歌单详情页与批量数据拉取 |
| 查询歌曲API | 获取歌曲音质、歌词、逐字歌词、歌曲详情、批量歌曲信息 | 歌曲详情展示与播放前信息准备 |
| 获取播放地址API | 获取歌曲播放url、批量播放url、不可播toast文案 | 播放链路核心能力 |
| 获取下载地址API | 下载url、下载总数、不可下载toast文案 | 下载能力与限制提示 |
| 文字搜索API | 热搜榜、热词、提示词、综合搜索、按类型搜索（歌/单/专/人） | 搜索入口联想、召回与结果页 |
| 语音搜索API | 多槽位搜索、AI原文搜索 | 语音输入/自然语言搜索 |
| 获取播放记录API | 最近播放（歌单/专辑/歌曲）、听歌排行、近期内容推荐 | 个人历史与再推荐 |
| 用户资产API | 已购歌曲、已购专辑、网盘歌曲 | 资产同步与权益展示 |
| 播放数据回传API | 音乐/长音频播放数据回传 | 行为上报与统计 |
| 艺人API | 艺人详情、艺人列表、热门歌曲、专辑列表、收藏艺人 | 艺人页与艺人关系数据 |
| 专辑API | 收藏/取消收藏专辑、专辑详情、专辑歌曲列表 | 专辑页与收藏能力 |
| 高品质专区 | Vivid/HiFi/杜比/Hi-Res 内容接口 | 高音质专区内容分发 |
| 收藏&创建API | 收藏歌单、取消收藏、红心歌曲、批量增删歌单歌曲 | 用户收藏与歌单维护 |
| 会员API | H5收银台、二维码收银台、三方通知 | 会员购买与支付回调 |
| AI互动 | 智能搜推、一句话歌单 | 生成式/智能推荐入口 |
| 跨端续播API | 跨端续播查询、上报 | 多设备播放进度衔接 |
| 随心唱API | 干声支持判断、音频详情 | K歌/人声相关能力 |
| AIDJ | 获取音色列表、歌曲口播信息 | 语音播报与音色驱动场景 |
| 评论API | 精选乐评、热门评论、乐评日历 | 评论内容消费与互动氛围 |
| 音质体验卡API | 获取体验卡、领取使用体验卡 | 音质权益运营 |
| 音质限免API | 音质限免开启、限免查询 | 限时权益活动 |

---

## 4. 可直接复用的调用模板

## 4.1 QQ OpenAPI 模板

```text
GET https://openrpc.music.qq.com/rpc_proxy/fcgi-bin/music_open_api.fcg
  ?opi_cmd=<命令字>
  &app_id=<应用ID>
  &app_key=<应用Key>
  &timestamp=<秒级时间戳>
  &sign=<签名>
  &<业务参数...>
```

## 4.2 网易云 OpenAPI 模板

```text
GET/POST http://openapi.music.163.com/openapi/<具体路径>
  公共参数: appId, accessToken, signType, timestamp, device ...
  业务参数: bizContent={...}
```

---

## 5. 备注

- 本文是基于你给定链接及其实际可访问数据整理；其中网易云的分类与接口项来自官方接口返回。
- 若你需要“逐接口参数字典版”（把上表每一项都展开到字段级），我可以继续自动批量拉取每个 `docId` 并生成第二份 `API字段全量手册.md`。

---

## 6. 参考链接

- [QQ音乐开发者平台 OpenAPI / 热词章节](https://developer.y.qq.com/docs/openapi#/feature/hotkey)
- [网易云开发者文档页面（docId）](https://developer.music.163.com/st/developer/document?docId=8e96f389dfc74fcb97af35d1597be77e)
- [网易云接口详情（docId对应 JSON）](https://interface.music.163.com/api/openplatform/developer/apidoc/get?docId=8e96f389dfc74fcb97af35d1597be77e)
- [网易云 API 分类树](https://interface.music.163.com/api/openplatform/developer/api/doc/category)

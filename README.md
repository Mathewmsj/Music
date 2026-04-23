# 音乐榜单聚合系统

中文简约站点：对比 [网易云音乐](https://music.163.com/)、[QQ 音乐](https://y.qq.com/)、[酷狗](https://www.kugou.com/)、[咪咕](https://music.migu.cn/)、[Apple Music](https://music.apple.com/cn/) 的热歌 / 新歌信号，使用 **Borda 计分**生成「融合热歌榜」「融合新歌榜」，适合作为「网页数据采集」课程项目。

## 功能概览

- **分平台榜单**：各源独立拉取，失败时单独标红，不影响其他平台。
- **融合榜单**：对每个平台榜单，第 `r` 名获得 `N−r+1` 分（`N` 为榜单长度），跨平台累加；歌名 + 艺人经弱规范化后去重合并。
- **合规**：请求间隔默认200ms（`HTTP_DELAY_MS`）；请勿高频调用。上线前请自行查阅各站 `robots.txt` 与服务条款，本项目仅用于学习展示。

## 技术栈

- 后端：Python 3.11+（已在 3.14 验证）、Starlette、httpx、uvicorn  
- 前端：Vite 6、React 18、TypeScript  

## 本地运行

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> 说明：`main.py` 中的 ASGI 实例名为 `app`，与 uvicorn 约定一致。

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

开发时 Vite 将 `/api` 代理到 `http://127.0.0.1:8000`。

### 一键启动前后端（开发模式）

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

脚本会自动：
- 创建 `backend/.venv`（如不存在）并按 `requirements.txt` 安装依赖（仅在依赖变更时重装）
- 首次安装前端依赖（`frontend/node_modules`）
- 同时启动后端 `uvicorn`（8000）与前端 `vite`（5173）

按 `Ctrl+C` 会同时停止两个服务。

前端顶部 **「榜单浏览」** 可切换平台、选择榜单，并一键拉取（酷狗 / QQ 支持 `all_pages` 多页合并）。

### 全榜单 / 全曲扩展 API

| 接口 | 说明 |
|------|------|
| `GET /api/platforms` | 支持的平台列表 |
| `GET /api/charts?platform_key=netease` | 网易云：从 `/discover/toplist` 解析，约 **62** 个官方榜入口 |
| `GET /api/charts?platform_key=qq` | QQ：`musicu` `GetAll`，约 **30** 个巅峰榜 |
| `GET /api/charts?platform_key=kugou` | 酷狗：`m.kugou.com/rank/list`，约 **55** 个榜单 |
| `GET /api/charts?platform_key=migu` | 咪咕：内置常用 `rankId`（可在 `backend/app/chart_api.py` 的 `list_migu_charts` 继续补充） |
| `GET /api/charts?platform_key=apple` | Apple：RSS 热门 / 新歌两条 |
| `GET /api/chart?platform_key=...&chart_id=...` | 拉取该榜歌曲；**酷狗 / QQ** 可加 `all_pages=true` 自动翻页合并 |

说明：酷狗 **TOP500** 等榜单在 `m.kugou.com/rank/info` 上分页不完整（常见约 5 页、150 条后 `total` 变 0），全量合并时响应里会带 `meta.partial` 与说明，写报告时可作为「数据源局限」。

### 一键静态部署（单端口）

构建前端后把产物拷入 `backend/static`，再启动 uvicorn，即可同域访问页面与 API：

```bash
cd frontend && npm run build
rm -rf ../backend/static && cp -r dist ../backend/static
cd ../backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

浏览器打开 `http://127.0.0.1:8000/`。

## 环境变量

| 变量 | 说明 |
|------|------|
| `HTTP_DELAY_MS` | 请求间隔（毫秒），默认 `200` |

**切勿**将 `.env` 提交到 GitHub。

## 合规与伦理（报告可引用）

1. **robots.txt**：上线前对各数据源域名检查 `robots.txt`，评估是否允许自动化访问；课堂项目建议在报告中写明查阅时间与结论。  
2. **频率**：通过 `HTTP_DELAY_MS` 限速，避免对第三方站点造成压力。  
3. **数据用途**：不声称与各官方榜单一致；融合榜为算法合成结果，非官方排名。  
4. **Apple Music**：使用公开 RSS JSON（Apple Marketing Tools）获取榜单，避免对网页做高频抓取。  
5. **咪咕 / QQ 等**：若接口变更导致失败，可在 `backend/app/providers/` 中调整歌单 ID 或接口，并记录于报告「局限与改进」。

## 课程提交清单对应

- **报告**：背景、数据源、合规、架构、截图、反思 — 可直接扩展本节与代码注释。  
- **演示视频**：展示「分平台」「融合榜单」切换与「重新拉取」。  
- **公网部署**：可将本仓库部署到 Render / Fly.io / 云主机等，注意环境变量与 HTTPS。  
- **代码**：本仓库含 `requirements.txt` 与 `frontend/package.json`。

## 目录结构

```
backend/ Starlette API、各平台 providers、融合算法
frontend/    React 界面
```

## 许可

仅供学习使用；使用第三方数据时遵守其服务条款。

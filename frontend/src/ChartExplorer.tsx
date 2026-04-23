import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchChartDetail,
  fetchChartList,
  fetchPlatforms,
  type ChartDetailResponse,
  type ChartListResponse,
  type ChartMeta,
  type ChartSong,
  type PlatformInfo,
} from "./api";

function SongTable({ rows }: { rows: ChartSong[] }) {
  return (
    <div className="table-wrap explorer-table">
      <table className="chart-table">
        <thead>
          <tr>
            <th>#</th>
            <th>曲目</th>
            <th>艺人</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr key={`${s.rank}-${s.title}-${s.artist}`}>
              <td className="num">{s.rank}</td>
              <td>{s.title}</td>
              <td className="muted">{s.artist}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ChartExplorer() {
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [plat, setPlat] = useState("");
  const [list, setList] = useState<ChartListResponse | null>(null);
  const [chartId, setChartId] = useState("");
  const [page, setPage] = useState(1);
  const [detail, setDetail] = useState<ChartDetailResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const r = await fetchPlatforms();
        setPlatforms(r.platforms);
        if (r.platforms.length) setPlat(r.platforms[0].key);
      } catch (e) {
        setErr(e instanceof Error ? e.message : "加载平台失败");
      }
    })();
  }, []);

  const loadCharts = useCallback(async (key: string) => {
    setErr(null);
    setList(null);
    setDetail(null);
    setChartId("");
    if (!key) return;
    setBusy(true);
    try {
      const r = await fetchChartList(key);
      setList(r);
      if (r.charts.length) setChartId(r.charts[0].chart_id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "加载榜单列表失败");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (plat) void loadCharts(plat);
  }, [plat, loadCharts]);

  const selectedMeta: ChartMeta | undefined = useMemo(
    () => list?.charts.find((c) => c.chart_id === chartId),
    [list, chartId]
  );

  const loadDetail = async (allPages: boolean) => {
    if (!plat || !chartId) return;
    setErr(null);
    setBusy(true);
    setDetail(null);
    try {
      const d = await fetchChartDetail(plat, chartId, {
        allPages,
        page: plat === "kugou" && !allPages ? page : undefined,
      });
      setDetail(d);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "加载详情失败");
    } finally {
      setBusy(false);
    }
  };

  const showKugouPage = plat === "kugou";
  const showAllPagesBtn = plat === "kugou" || plat === "qq";

  return (
    <section className="panel explorer">
      <h2>榜单浏览（全平台 · 全榜单 · 全曲尽量拉取）</h2>
      <p className="muted small">
        后端接口：<code>/api/platforms</code>、<code>/api/charts</code>、
        <code>/api/chart?all_pages=true</code>（酷狗/QQ 会多次请求合并分页）。
      </p>

      <div className="explorer-bar">
        <label className="field">
          <span>平台</span>
          <select value={plat} onChange={(e) => setPlat(e.target.value)}>
            {platforms.map((p) => (
              <option key={p.key} value={p.key}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <label className="field grow">
          <span>榜单</span>
          <select value={chartId} onChange={(e) => setChartId(e.target.value)}>
            {(list?.charts || []).map((c) => (
              <option key={c.chart_id} value={c.chart_id}>
                {c.chart_name}（{c.chart_id}）
              </option>
            ))}
          </select>
        </label>
        {showKugouPage && (
          <label className="field narrow">
            <span>页码</span>
            <input
              type="number"
              min={1}
              value={page}
              onChange={(e) => setPage(Math.max(1, Number(e.target.value) || 1))}
            />
          </label>
        )}
      </div>

      <div className="explorer-actions">
        {showAllPagesBtn && (
          <button
            type="button"
            className="btn primary"
            disabled={busy || !chartId}
            onClick={() => void loadDetail(true)}
          >
            {busy ? "请求中…" : "拉取全量（多页合并）"}
          </button>
        )}
        <button
          type="button"
          className="btn"
          disabled={busy || !chartId}
          onClick={() => void loadDetail(false)}
        >
          {showAllPagesBtn ? "仅单页 / 单次" : "拉取榜单"}
        </button>
        {selectedMeta?.source_url && (
          <a className="source-link" href={selectedMeta.source_url} target="_blank" rel="noreferrer">
            来源页
          </a>
        )}
      </div>

      {err && (
        <p className="card-err" role="alert">
          {err}
        </p>
      )}

      {list && (
        <p className="muted small">
          已发现 <strong>{list.charts.length}</strong> 个榜单（{list.platform}）。
        </p>
      )}

      {detail && (
        <>
          <div className="explorer-head">
            <h3>{detail.chart_name}</h3>
            <span className={`pill ${detail.fetched_ok ? "pill-ok" : "pill-bad"}`} title={detail.error || ""}>
              {detail.fetched_ok ? `共 ${detail.songs.length} 条` : "未获取"}
            </span>
          </div>
          {detail.meta && Object.keys(detail.meta).length > 0 && (
            <pre className="meta-block">{JSON.stringify(detail.meta, null, 2)}</pre>
          )}
          {!detail.fetched_ok && detail.error && (
            <p className="card-err">{detail.error}</p>
          )}
          {detail.fetched_ok && <SongTable rows={detail.songs} />}
        </>
      )}
    </section>
  );
}

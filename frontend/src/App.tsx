import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useState,
  type CSSProperties,
} from "react";
import {
  fetchOverview,
  fetchSongInsight,
  getOverviewInsightsJobStatus,
  postRefresh,
  startOverviewInsightsJob,
  type ChartPayload,
  type CloudItem,
  type FusedSong,
  type InsightJobStatus,
  type OverviewResponse,
  type OverviewInsightResponse,
  type SongInsight,
} from "./api";
import { ChartExplorer } from "./ChartExplorer";
import "./App.css";

type Tab = "platform" | "fused" | "explorer" | "insights";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`pill ${ok ? "pill-ok" : "pill-bad"}`} title={label}>
      {ok ? "已获取" : "未获取"}
    </span>
  );
}

function ChartTable({ rows }: { rows: ChartPayload["songs"] }) {
  return (
    <div className="table-wrap">
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
            <tr key={`${s.rank}-${s.title}`}>
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

function FusedTable({
  rows,
  onSelect,
}: {
  rows: FusedSong[];
  onSelect?: (song: FusedSong) => void;
}) {
  return (
    <div className="table-wrap">
      <table className="chart-table fused">
        <thead>
          <tr>
            <th>#</th>
            <th>曲目</th>
            <th>艺人</th>
            <th>得分</th>
            <th>出现</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((s) => (
            <tr
              key={`${s.fused_rank}-${s.title}`}
              className={onSelect ? "row-clickable" : ""}
              onClick={() => onSelect?.(s)}
            >
              <td className="num">{s.fused_rank}</td>
              <td>{s.title}</td>
              <td className="muted">{s.artist}</td>
              <td className="score">{s.score}</td>
              <td>
                <span className="appear">{s.appearances}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const PIE_COLORS = [
  "#6b8cae",
  "#c49a6c",
  "#8f7aad",
  "#6ba292",
  "#b0707a",
  "#a89f4e",
  "#7a9ab8",
  "#5c8f8f",
];

type PieSlice = { text: string; weight: number; color: string };

function buildGenrePieSlices(items: CloudItem[]): PieSlice[] {
  const raw = items.filter((x) => x.weight > 0);
  if (!raw.length) return [];
  const maxSlices = 8;
  if (raw.length <= maxSlices) {
    return raw.map((it, i) => ({
      text: it.text,
      weight: it.weight,
      color: PIE_COLORS[i % PIE_COLORS.length],
    }));
  }
  const head = raw.slice(0, maxSlices - 1);
  const tailWeight = raw.slice(maxSlices - 1).reduce((s, x) => s + x.weight, 0);
  const out: PieSlice[] = head.map((it, i) => ({
    text: it.text,
    weight: it.weight,
    color: PIE_COLORS[i % PIE_COLORS.length],
  }));
  out.push({
    text: "其他",
    weight: tailWeight,
    color: PIE_COLORS[(maxSlices - 1) % PIE_COLORS.length],
  });
  return out;
}

function GenrePieChart({ items }: { items: CloudItem[] }) {
  const slices = useMemo(() => buildGenrePieSlices(items), [items]);
  const total = useMemo(() => slices.reduce((s, x) => s + x.weight, 0), [slices]);
  const pieStyle: CSSProperties = useMemo(() => {
    if (!total) return { background: "color-mix(in srgb, var(--line) 85%, var(--ink) 15%)" };
    let acc = 0;
    const stops = slices.map((sl) => {
      const start = (acc / total) * 100;
      acc += sl.weight;
      const end = (acc / total) * 100;
      return `${sl.color} ${start}% ${end}%`;
    });
    return { background: `conic-gradient(${stops.join(", ")})` };
  }, [slices, total]);

  return (
    <article className="insight-card">
      <h3>风格占比</h3>
      {!total ? (
        <p className="muted small">暂无风格标签数据</p>
      ) : (
        <div className="pie-row">
          <div className="pie-disc" style={pieStyle} aria-hidden />
          <ul className="pie-legend">
            {slices.map((sl) => (
              <li key={sl.text}>
                <span className="pie-swatch" style={{ background: sl.color }} />
                <span className="pie-label">{sl.text}</span>
                <span className="pie-pct muted">
                  {Math.round((sl.weight / total) * 1000) / 10}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

function ArtistTopRank({ items, title, limit }: { items: CloudItem[]; title: string; limit: number }) {
  const rows = items.slice(0, limit);
  return (
    <article className="insight-card">
      <h3>{title}</h3>
      {rows.length === 0 ? (
        <p className="muted small">暂无数据</p>
      ) : (
        <ol className="rank-list">
          {rows.map((it, idx) => (
            <li key={`${it.text}-${idx}`}>
              <span className="rank-num">{idx + 1}</span>
              <span className="rank-name">{it.text}</span>
              <span className="rank-count muted">{it.weight} 首</span>
            </li>
          ))}
        </ol>
      )}
    </article>
  );
}

/** 直方图区间上的平滑曲线（加权滑动平均），便于看出单峰/拖尾形态 */
function smoothHistogramCounts(counts: number[], radius = 2): number[] {
  const n = counts.length;
  return counts.map((_, i) => {
    let s = 0;
    let w = 0;
    for (let j = i - radius; j <= i + radius; j++) {
      if (j < 0 || j >= n) continue;
      const wt = radius + 1 - Math.abs(j - i);
      s += counts[j] * wt;
      w += wt;
    }
    return w > 0 ? s / w : 0;
  });
}

function binIndexDuration(sec: number, binSec: number, regularBins: number): number {
  const hi = regularBins * binSec;
  if (sec >= hi) return regularBins;
  return Math.min(regularBins - 1, Math.floor(sec / binSec));
}

function DistributionHistogramSvg({
  counts,
  xAxisTicks,
  yMaxHint,
  ariaLabel,
}: {
  counts: number[];
  xAxisTicks: { binIndex: number; label: string }[];
  yMaxHint?: number;
  ariaLabel: string;
}) {
  const gradId = `histFill-${useId().replace(/:/g, "")}`;
  const smooth = useMemo(() => smoothHistogramCounts(counts, 2), [counts]);
  const maxCount = useMemo(
    () => Math.max(1, ...counts, ...smooth, yMaxHint ?? 0),
    [counts, smooth, yMaxHint]
  );
  const yTicks = useMemo(() => {
    if (maxCount <= 1) return [0, maxCount];
    const mid = Math.round(maxCount / 2);
    return [...new Set([0, mid, maxCount])].sort((a, b) => a - b);
  }, [maxCount]);

  const W = 420;
  const H = 168;
  const pad = { l: 34, r: 10, t: 10, b: 30 };
  const innerW = W - pad.l - pad.r;
  const innerH = H - pad.t - pad.b;
  const n = counts.length;
  const barGap = 0.15;
  const barW = (innerW / n) * (1 - barGap);
  const step = innerW / n;

  const barRects = counts.map((c, i) => {
    const h = (c / maxCount) * innerH;
    const x = pad.l + i * step + (step - barW) / 2;
    const y = pad.t + innerH - h;
    return { x, y, h, c, i };
  });

  const curvePoints = smooth.map((v, i) => {
    const x = pad.l + (i + 0.5) * step;
    const y = pad.t + innerH - (v / maxCount) * innerH;
    return `${x},${y}`;
  });
  const curvePathD =
    curvePoints.length > 0
      ? `M ${pad.l},${pad.t + innerH} L ${curvePoints.join(" L ")} L ${pad.l + innerW},${pad.t + innerH} Z`
      : "";

  return (
    <svg
      className="hist-svg"
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label={ariaLabel}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.22" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      {yTicks.map((yt) => {
        const y = pad.t + innerH - (yt / maxCount) * innerH;
        return (
          <g key={yt}>
            <line
              x1={pad.l}
              y1={y}
              x2={pad.l + innerW}
              y2={y}
              className="hist-grid-line"
            />
            <text x={4} y={y + 4} className="hist-axis-text">
              {yt}
            </text>
          </g>
        );
      })}
      {barRects.map(({ x, y, h, i }) => (
        <rect
          key={i}
          x={x}
          y={y}
          width={barW}
          height={Math.max(h, 0)}
          className="hist-bar"
          rx={1.5}
        />
      ))}
      {curvePathD ? (
        <>
          <path d={curvePathD} fill={`url(#${gradId})`} stroke="none" />
          <polyline
            fill="none"
            className="hist-curve"
            points={smooth
              .map((v, i) => {
                const x = pad.l + (i + 0.5) * step;
                const y = pad.t + innerH - (v / maxCount) * innerH;
                return `${x},${y}`;
              })
              .join(" ")}
          />
        </>
      ) : null}
      <line
        x1={pad.l}
        y1={pad.t + innerH}
        x2={pad.l + innerW}
        y2={pad.t + innerH}
        className="hist-axis-line"
      />
      {xAxisTicks.map(({ binIndex, label }) => {
        const x = pad.l + binIndex * step;
        return (
          <text
            key={`${binIndex}-${label}`}
            x={x}
            y={H - 6}
            className="hist-axis-text hist-x-tick"
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}

const DURATION_BIN_SEC = 10;
const DURATION_REGULAR_BINS = 42; // [0, 420) 秒
const DURATION_OVERFLOW_BIN = 42; // >= 420 秒，共 43 柱

function DurationDistribution({ songs }: { songs: SongInsight[] }) {
  const { counts, unknown, known } = useMemo(() => {
    const counts = Array.from({ length: DURATION_OVERFLOW_BIN + 1 }, () => 0);
    let unknown = 0;
    let known = 0;
    for (const s of songs) {
      const d = s.duration_sec;
      if (d == null || d < 0) {
        unknown += 1;
        continue;
      }
      known += 1;
      const idx = binIndexDuration(d, DURATION_BIN_SEC, DURATION_REGULAR_BINS);
      counts[idx] += 1;
    }
    return { counts, unknown, known };
  }, [songs]);

  const xTicks = useMemo(() => {
    const stepSec = 60;
    const out: { binIndex: number; label: string }[] = [];
    for (let sec = 0; sec <= 360; sec += stepSec) {
      out.push({ binIndex: sec / DURATION_BIN_SEC, label: `${sec / 60}` });
    }
    out.push({ binIndex: DURATION_OVERFLOW_BIN, label: "7+" });
    return out;
  }, []);

  const hasData = known > 0;

  return (
    <article className="insight-card insight-card-wide">
      <h3>歌曲时长分布</h3>
      <p className="muted small">
        直方图（柱）+ 平滑曲线示意分布形态；横轴为时长（分钟刻度），柱宽 {DURATION_BIN_SEC}{" "}
        秒。样本中有明确时长 {known}/{songs.length} 首
        {unknown > 0 ? `；时长未知 ${unknown} 首未计入图中` : ""}。
      </p>
      {hasData ? (
        <div className="hist-wrap">
          <DistributionHistogramSvg
            counts={counts}
            xAxisTicks={xTicks}
            ariaLabel="歌曲时长直方图与分布曲线"
          />
        </div>
      ) : (
        <p className="muted small">暂无有效时长数据，无法绘制分布图。</p>
      )}
    </article>
  );
}

/** 去掉行首 LRC 时间标签 [mm:ss.xx] 与常见 [ti:]/[ar:] 等信息标签，避免冒号误伤正文 */
function stripLrcLinePrefix(line: string): string {
  let s = line.trim();
  s = s.replace(/^\[\d{1,3}:\d{2}(?:\.\d{2,3})?\]\s*/, "");
  s = s.replace(/^\[[a-z]{2,8}:[^\]]+\]\s*/i, "");
  return s;
}

const LYRIC_META_PREFIX =
  /^(词|曲|编曲|填词|作词|作曲|制作人|監製|监制|出品|吉他|鼓|和声|混音|录音|企划|出品人|发行|版权)\s*[：:]/;

/** 典型制作信息行；不再用「行里只要有冒号就丢」，否则会误丢带 [mm:ss] 的正文行 */
function isLyricMetadataLine(line: string): boolean {
  const t = stripLrcLinePrefix(line).trim();
  if (!t) return true;
  if (LYRIC_META_PREFIX.test(t)) return true;
  const raw = line.trim();
  if (/^\[[a-z]{2,8}:[^\]]+\]$/i.test(raw) && raw.length <= 64) return true;
  return false;
}

function countLatinWords(s: string): number {
  const m = s.match(/[A-Za-z]+(?:['’-][A-Za-z]+)*/g);
  return m ? m.length : 0;
}

/** 汉字/扩展 A/假名/韩文等：每码点 1；英文连续字母按「单词」计 1（不按字母计） */
function countCjkKanaHangulUnits(s: string): number {
  let n = 0;
  for (let i = 0; i < s.length; ) {
    const c = s.codePointAt(i)!;
    if (
      (c >= 0x4e00 && c <= 0x9fff) ||
      (c >= 0x3400 && c <= 0x4dbf) ||
      (c >= 0x3040 && c <= 0x30ff) ||
      (c >= 0x31f0 && c <= 0x31ff) ||
      (c >= 0xac00 && c <= 0xd7af) ||
      (c >= 0x20000 && c <= 0x2a6df)
    ) {
      n += 1;
    }
    i += c > 0xffff ? 2 : 1;
  }
  return n;
}

/** 与中文「字数」习惯对齐：中文等按字、英文按词；忽略标点、空白、数字 */
function countValidLyricUnits(lyric: string): number {
  const body = lyric
    .split(/\r?\n/)
    .map((ln) => stripLrcLinePrefix(ln))
    .filter((ln) => !isLyricMetadataLine(ln))
    .join("\n");
  return countCjkKanaHangulUnits(body) + countLatinWords(body);
}

const LYRIC_BIN_CHARS = 40;
const LYRIC_REGULAR_BINS = 20; // [0, 800)
const LYRIC_OVERFLOW_INDEX = 20; // 共 21 柱

function binIndexLyricChars(n: number): number {
  const hi = LYRIC_REGULAR_BINS * LYRIC_BIN_CHARS;
  if (n >= hi) return LYRIC_OVERFLOW_INDEX;
  return Math.min(LYRIC_REGULAR_BINS - 1, Math.floor(n / LYRIC_BIN_CHARS));
}

function LyricLengthDistribution({ songs }: { songs: SongInsight[] }) {
  const { counts, withLyric, noLyric, emptyValid } = useMemo(() => {
    const counts = Array.from({ length: LYRIC_OVERFLOW_INDEX + 1 }, () => 0);
    let noLyric = 0;
    let emptyValid = 0;
    let withLyric = 0;
    for (const s of songs) {
      const raw = (s.lyric_excerpt || "").trim();
      if (!raw) {
        noLyric += 1;
        continue;
      }
      withLyric += 1;
      const n = countValidLyricUnits(raw);
      if (n === 0) {
        emptyValid += 1;
        continue;
      }
      counts[binIndexLyricChars(n)] += 1;
    }
    return { counts, withLyric, noLyric, emptyValid };
  }, [songs]);

  const xTicks = useMemo(() => {
    const out: { binIndex: number; label: string }[] = [];
    for (let c = 0; c < 800; c += 160) {
      out.push({ binIndex: c / LYRIC_BIN_CHARS, label: String(c) });
    }
    out.push({ binIndex: LYRIC_OVERFLOW_INDEX, label: "≥800" });
    return out;
  }, []);

  const plotted = withLyric - emptyValid;

  return (
    <article className="insight-card insight-card-wide">
      <h3>歌词有效字数分布</h3>
      <p className="muted small">
        统计口径与中文习惯一致：汉字、假名、韩文音节各计 1；连续英文字母按「单词」计 1（不再按字母逐个计，否则会严重高估英词歌）。
        已去掉行首 LRC 时间戳与常见 [ti:]/[ar:] 标签，并跳过词/曲/编曲等制作信息行；不含标点、空白、数字。
        有正文 {withLyric}/{songs.length} 首，其中有效量为 0 的 {emptyValid} 首；无歌词文本 {noLyric} 首。横轴为「等价字数」，柱宽每档{" "}
        {LYRIC_BIN_CHARS}。
      </p>
      {plotted > 0 ? (
        <div className="hist-wrap">
          <DistributionHistogramSvg
            counts={counts}
            xAxisTicks={xTicks}
            ariaLabel="歌词有效字数直方图与分布曲线"
          />
        </div>
      ) : (
        <p className="muted small">暂无可用歌词样本，无法绘制字数分布。</p>
      )}
    </article>
  );
}

function SongDetailModal({
  song,
  loading,
  onClose,
}: {
  song: SongInsight | null;
  loading: boolean;
  onClose: () => void;
}) {
  return (
    <div className="modal-mask" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="modal-close" onClick={onClose}>
          关闭
        </button>
        {loading && <p className="muted">加载歌曲简介中…</p>}
        {!loading && song && (
          <>
            <h3>{song.title}</h3>
            <p className="muted">{song.artist}</p>
            {song.cover_url && <img className="cover" src={song.cover_url} alt={song.title} />}
            <p>{song.intro || "暂无简介"}</p>
            {song.genres.length > 0 && (
              <p className="muted">风格标签：{song.genres.join(" / ")}</p>
            )}
            {song.lyric_excerpt && (
              <pre className="lyric-preview">{song.lyric_excerpt}</pre>
            )}
            {song.song_url && (
              <p>
                <a href={song.song_url} target="_blank" rel="noreferrer">
                  打开原始歌曲页
                </a>
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>("fused");
  const [sub, setSub] = useState<"hot" | "new">("hot");
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [hotN, setHotN] = useState(100);
  const [newN, setNewN] = useState(100);
  const [insight, setInsight] = useState<OverviewInsightResponse | null>(null);
  const [insightLoading, setInsightLoading] = useState(false);
  const [insightProgress, setInsightProgress] = useState<InsightJobStatus | null>(null);
  const [selectedSong, setSelectedSong] = useState<SongInsight | null>(null);
  const [songLoading, setSongLoading] = useState(false);

  const loadInitial = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const o = await fetchOverview(false);
      setData(o);
      setHotN(o.fusion_hot_n);
      setNewN(o.fusion_new_n);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  const doRefresh = useCallback(async () => {
    setErr(null);
    setRefreshing(true);
    try {
      const o = await postRefresh({ hotN, newN });
      setData(o);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "加载失败");
    } finally {
      setRefreshing(false);
    }
  }, [hotN, newN]);

  useEffect(() => {
    void loadInitial();
  }, [loadInitial]);

  const chartsForSub = useMemo(() => {
    if (!data) return [];
    return data.charts.filter((c) => c.chart_type === sub);
  }, [data, sub]);

  const fused = useMemo(() => {
    if (!data) return [];
    return sub === "hot" ? data.fused_hot : data.fused_new;
  }, [data, sub]);

  const loadInsights = useCallback(async () => {
    setInsightLoading(true);
    try {
      if (!data) {
        setErr("请先加载榜单后再进行洞察分析");
        return;
      }
      const targetN = sub === "hot" ? hotN : newN;
      const fusedLen =
        data == null
          ? 0
          : sub === "hot"
            ? data.fused_hot.length
            : data.fused_new.length;
      if (fusedLen < 1) {
        setErr("当前融合榜单为空，请先刷新或检查各站抓取是否成功");
        return;
      }
      // 与当前融合榜单条数对齐：分析前 N 首（N 为热歌/新歌条数设置，且不超过已返回的融合长度）
      const sampleSize = Math.min(Math.max(1, targetN), Math.max(1, fusedLen));
      const start = await startOverviewInsightsJob({
        chartType: sub,
        sampleSize,
      });
      let status = await getOverviewInsightsJobStatus(start.job_id);
      setInsightProgress(status);
      while (status.status === "running") {
        await new Promise((r) => setTimeout(r, 800));
        status = await getOverviewInsightsJobStatus(start.job_id);
        setInsightProgress(status);
      }
      if (status.status === "done" && status.result) {
        setInsight(status.result);
      } else if (status.status === "error") {
        throw new Error(status.error || "分析失败");
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "洞察加载失败");
    } finally {
      setInsightLoading(false);
    }
  }, [sub, hotN, newN, data]);

  const openSongDetail = useCallback(async (song: FusedSong) => {
    setSelectedSong(null);
    setSongLoading(true);
    try {
      const detail = await fetchSongInsight(song.title, song.artist);
      setSelectedSong(detail);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "单曲简介加载失败");
    } finally {
      setSongLoading(false);
    }
  }, []);

  return (
    <div className="app">
      <header className="hero">
        <p className="eyebrow">实时榜单 · 合规采集</p>
        <h1>
          音乐榜单聚合系统
        </h1>
        <p className="lede">
          聚合网易云音乐、QQ音乐、酷狗、咪咕与 Apple Music 的热歌与新歌信号，使用 Borda
          计分融合为一张「跨平台共识榜」。界面仅作课程展示与个人学习用途。
        </p>
        <div className="hero-actions">
          <label className="fusion-len">
            热歌条数
            <input
              type="number"
              min={1}
              max={500}
              value={hotN}
              onChange={(e) => setHotN(Number(e.target.value) || 1)}
            />
          </label>
          <label className="fusion-len">
            新歌条数
            <input
              type="number"
              min={1}
              max={500}
              value={newN}
              onChange={(e) => setNewN(Number(e.target.value) || 1)}
            />
          </label>
          <button
            type="button"
            className="btn primary"
            disabled={refreshing}
            onClick={() => void doRefresh()}
          >
            {refreshing ? "刷新中…" : "重新拉取榜单"}
          </button>
          {data && (
            <span className="updated">
              最近更新：<time>{data.updated_at}</time>
              （当前融合：热 {data.fusion_hot_n} / 新 {data.fusion_new_n}）
            </span>
          )}
        </div>
      </header>

      {err && (
        <div className="banner error" role="alert">
          {err}（请确认后端 <code>uvicorn main:app</code> 已启动）
        </div>
      )}

      {loading && !data && <p className="center muted">载入中…</p>}

      {data && (
        <>
          <nav className="tabs">
            <button
              type="button"
              className={tab === "fused" ? "active" : ""}
              onClick={() => setTab("fused")}
            >
              融合榜单
            </button>
            <button
              type="button"
              className={tab === "platform" ? "active" : ""}
              onClick={() => setTab("platform")}
            >
              分平台
            </button>
            <button
              type="button"
              className={tab === "explorer" ? "active" : ""}
              onClick={() => setTab("explorer")}
            >
              榜单浏览
            </button>
            <button
              type="button"
              className={tab === "insights" ? "active" : ""}
              onClick={() => {
                setTab("insights");
                void loadInsights();
              }}
            >
              数据洞察
            </button>
            <div className="spacer" />
            {tab !== "explorer" && (
              <div className="toggle">
                <button
                  type="button"
                  className={sub === "hot" ? "on" : ""}
                  onClick={() => setSub("hot")}
                >
                  热歌
                </button>
                <button
                  type="button"
                  className={sub === "new" ? "on" : ""}
                  onClick={() => setSub("new")}
                >
                  新歌
                </button>
              </div>
            )}
          </nav>

          {tab === "fused" && (
            <section className="panel">
              <div className="algo">
                <h2>算法说明</h2>
                <p>
                  对每个平台榜单单独计算 Borda 分：在长度为 N 的榜单中，第 r 名获得 (N−r+1)
                  分（N 为该平台实际参与条数，若某站不足你设定的条数则按更短的列表计）。
                  同一首歌在不同平台重复出现时分数累加。歌名与艺人经弱规范化后合并（去标点、统一空白），以减少「同一歌不同写法」带来的重复。
                  Apple Music RSS 源单次最多 100 条。
                </p>
                <p className="sources">
                  数据来源（请遵守各站服务条款与 robots）：
                  <a href="https://music.163.com/" target="_blank" rel="noreferrer">
                    网易云音乐
                  </a>
                  、
                  <a href="https://y.qq.com/" target="_blank" rel="noreferrer">
                    QQ音乐
                  </a>
                  、
                  <a href="https://www.kugou.com/" target="_blank" rel="noreferrer">
                    酷狗
                  </a>
                  、
                  <a href="https://music.migu.cn/" target="_blank" rel="noreferrer">
                    咪咕
                  </a>
                  、
                  <a href="https://music.apple.com/cn/" target="_blank" rel="noreferrer">
                    Apple Music
                  </a>
                  。
                </p>
              </div>
              <FusedTable rows={fused} onSelect={(song) => void openSongDetail(song)} />
            </section>
          )}

          {tab === "explorer" && <ChartExplorer />}

          {tab === "insights" && (
            <section className="panel insights-panel">
              <div className="insight-head">
                <h2>{sub === "hot" ? "热歌" : "新歌"}洞察分析</h2>
                <button
                  type="button"
                  className="btn"
                  onClick={() => void loadInsights()}
                  disabled={insightLoading}
                >
                  {insightLoading ? "分析中…" : "重新分析"}
                </button>
              </div>
              {insight && (
                <>
                  <p className="muted small">
                    样本数：{insight.sample_size}，更新时间：{insight.updated_at}
                  </p>
                  <div className="insights-viz-grid">
                    <ArtistTopRank
                      title="热门歌手 TOP5"
                      limit={5}
                      items={insight.summary.top_artists}
                    />
                    <GenrePieChart items={insight.clouds.genre_cloud} />
                    <DurationDistribution songs={insight.songs} />
                    <LyricLengthDistribution songs={insight.songs} />
                  </div>
                </>
              )}
              {insightLoading && insightProgress && (
                <p className="muted small">
                  分析进度：{insightProgress.done}/{insightProgress.total || insightProgress.sample_size}
                  {insightProgress.total > 0
                    ? `（${Math.min(
                        100,
                        Math.round((insightProgress.done / insightProgress.total) * 100)
                      )}%）`
                    : ""}
                </p>
              )}
            </section>
          )}

          {tab === "platform" && (
            <section className="grid-platforms">
              {chartsForSub.map((c) => (
                <article key={`${c.platform}-${c.chart_name}`} className="card">
                  <div className="card-head">
                    <div>
                      <h2>{c.platform}</h2>
                      <p className="muted small">{c.chart_name}</p>
                    </div>
                    <StatusPill ok={c.fetched_ok} label={c.error || ""} />
                  </div>
                  {!c.fetched_ok && c.error && (
                    <p className="card-err">{c.error}</p>
                  )}
                  {c.fetched_ok && <ChartTable rows={c.songs} />}
                </article>
              ))}
            </section>
          )}
        </>
      )}

      <footer className="foot">
        <p>
          项目说明：请求已做限速与错误隔离；请勿高频调用或对第三方站点造成压力。部署时请使用环境变量保存密钥。
        </p>
      </footer>
      {(songLoading || selectedSong) && (
        <SongDetailModal
          song={selectedSong}
          loading={songLoading}
          onClose={() => {
            setSelectedSong(null);
            setSongLoading(false);
          }}
        />
      )}
    </div>
  );
}

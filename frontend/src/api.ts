export type ChartSong = {
  rank: number;
  title: string;
  artist: string;
  platform: string;
  chart_name: string;
  extra: string | null;
};

export type ChartPayload = {
  platform: string;
  chart_name: string;
  chart_type: "hot" | "new";
  fetched_ok: boolean;
  error: string | null;
  songs: ChartSong[];
};

export type FusedSong = {
  fused_rank: number;
  title: string;
  artist: string;
  score: number;
  appearances: number;
  sources: string[];
};

export type OverviewResponse = {
  updated_at: string;
  charts: ChartPayload[];
  fused_hot: FusedSong[];
  fused_new: FusedSong[];
  fusion_hot_n: number;
  fusion_new_n: number;
};

export type CloudItem = {
  text: string;
  weight: number;
};

export type SongInsight = {
  title: string;
  artist: string;
  found: boolean;
  intro: string;
  album: string;
  duration_sec: number | null;
  publish_time: number | null;
  cover_url: string;
  lyric_excerpt: string;
  genres: string[];
  source: string;
  song_id?: string;
  song_url?: string;
  error?: string;
};

export type OverviewInsightResponse = {
  updated_at: string;
  chart_type: "hot" | "new";
  sample_size: number;
  summary: {
    top_artists: CloudItem[];
    top_genres: CloudItem[];
    platform_heat: CloudItem[];
  };
  clouds: {
    artist_cloud: CloudItem[];
    genre_cloud: CloudItem[];
  };
  songs: SongInsight[];
};

export async function fetchOverview(
  refresh = false,
  opts?: { hotN?: number; newN?: number }
): Promise<OverviewResponse> {
  const p = new URLSearchParams();
  if (refresh) p.set("refresh", "true");
  if (opts?.hotN != null) p.set("hot_n", String(opts.hotN));
  if (opts?.newN != null) p.set("new_n", String(opts.newN));
  const q = p.toString();
  const r = await fetch(q ? `/api/overview?${q}` : "/api/overview");
  if (!r.ok) throw new Error(`请求失败 ${r.status}`);
  return r.json();
}

export async function postRefresh(opts?: {
  hotN?: number;
  newN?: number;
}): Promise<OverviewResponse> {
  const p = new URLSearchParams();
  if (opts?.hotN != null) p.set("hot_n", String(opts.hotN));
  if (opts?.newN != null) p.set("new_n", String(opts.newN));
  const q = p.toString();
  const r = await fetch(`/api/refresh${q ? `?${q}` : ""}`, { method: "POST" });
  if (!r.ok) throw new Error(`刷新失败 ${r.status}`);
  return r.json();
}

export type PlatformInfo = { key: string; name: string };

export type ChartMeta = {
  platform_key: string;
  platform: string;
  chart_id: string;
  chart_name: string;
  chart_type: string;
  source_url: string;
};

export type ChartListResponse = {
  updated_at: string;
  platform_key: string;
  platform: string;
  charts: ChartMeta[];
};

export type ChartDetailResponse = {
  updated_at: string;
  platform_key: string;
  platform: string;
  chart_id: string;
  chart_name: string;
  chart_type: string;
  source_url: string;
  fetched_ok: boolean;
  error: string | null;
  songs: ChartSong[];
  meta?: Record<string, unknown>;
};

export async function fetchPlatforms(): Promise<{ platforms: PlatformInfo[] }> {
  const r = await fetch("/api/platforms");
  if (!r.ok) throw new Error(`platforms ${r.status}`);
  return r.json();
}

export async function fetchChartList(platformKey: string): Promise<ChartListResponse> {
  const r = await fetch(`/api/charts?platform_key=${encodeURIComponent(platformKey)}`);
  if (!r.ok) throw new Error(`charts ${r.status}`);
  return r.json();
}

export async function fetchChartDetail(
  platformKey: string,
  chartId: string,
  opts?: { page?: number; allPages?: boolean }
): Promise<ChartDetailResponse> {
  const p = new URLSearchParams({ platform_key: platformKey, chart_id: chartId });
  if (opts?.page != null) p.set("page", String(opts.page));
  if (opts?.allPages) p.set("all_pages", "true");
  const r = await fetch(`/api/chart?${p.toString()}`);
  if (!r.ok) throw new Error(`chart ${r.status}`);
  return r.json();
}

export async function fetchOverviewInsights(opts?: {
  chartType?: "hot" | "new";
  sampleSize?: number;
}): Promise<OverviewInsightResponse> {
  const p = new URLSearchParams();
  if (opts?.chartType) p.set("chart_type", opts.chartType);
  if (opts?.sampleSize != null) p.set("sample_size", String(opts.sampleSize));
  const r = await fetch(`/api/insights/overview?${p.toString()}`);
  if (!r.ok) throw new Error(`insights ${r.status}`);
  return r.json();
}

export type InsightJobStatus = {
  status: "running" | "done" | "error";
  chart_type: "hot" | "new";
  sample_size: number;
  done: number;
  total: number;
  result: OverviewInsightResponse | null;
  error: string | null;
  updated_at: string;
};

export async function startOverviewInsightsJob(opts?: {
  chartType?: "hot" | "new";
  sampleSize?: number;
}): Promise<{ job_id: string; status: "running" }> {
  const p = new URLSearchParams();
  if (opts?.chartType) p.set("chart_type", opts.chartType);
  if (opts?.sampleSize != null) p.set("sample_size", String(opts.sampleSize));
  const r = await fetch(`/api/insights/start?${p.toString()}`, { method: "POST" });
  if (!r.ok) throw new Error(`insights start ${r.status}`);
  return r.json();
}

export async function getOverviewInsightsJobStatus(
  jobId: string
): Promise<InsightJobStatus> {
  const r = await fetch(`/api/insights/status?job_id=${encodeURIComponent(jobId)}`);
  if (!r.ok) throw new Error(`insights status ${r.status}`);
  return r.json();
}

export async function fetchSongInsight(
  title: string,
  artist: string
): Promise<SongInsight> {
  const p = new URLSearchParams({ title, artist });
  const r = await fetch(`/api/insights/song?${p.toString()}`);
  if (!r.ok) throw new Error(`song insight ${r.status}`);
  return r.json();
}

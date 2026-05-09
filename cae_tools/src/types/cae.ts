// =============================================================================
// cae.ts — TypeScript type definitions for CAE System List
// Project: CAE System List
// =============================================================================

// ── Domain categories ────────────────────────────────────────────────────────
export type CAEDomain =
  | "Crash Safety"    // クラッシュ安全性
  | "NVH"             // 騒音・振動・ハーシュネス
  | "Handling"        // ハンドリング
  | "Ride"            // 乗り心地
  | "Durability"      // 耐久性
  | "CFD"             // 流体解析
  | "Thermal"         // 熱解析
  | "Multibody"       // マルチボディ
  | "General";        // 汎用

// ── Solver type ───────────────────────────────────────────────────────────────
export type SolverType =
  | "FEA"             // Finite Element Analysis (有限要素法)
  | "MBD"             // Multi-Body Dynamics (マルチボディダイナミクス)
  | "CFD"             // Computational Fluid Dynamics (数値流体力学)
  | "BEM"             // Boundary Element Method (境界要素法)
  | "SEA"             // Statistical Energy Analysis
  | "FEA+MBD"
  | "FEA+CFD"
  | "Other";

// ── License type ──────────────────────────────────────────────────────────────
export type LicenseType =
  | "Commercial"      // 商用ライセンス
  | "Open Source"     // オープンソース
  | "Academic"        // アカデミックライセンス
  | "Freemium";       // 無料＋有料

// ── OS support ────────────────────────────────────────────────────────────────
export type OSSupport = "Windows" | "Linux" | "macOS";

// ── Update status (for cron-fetched news) ────────────────────────────────────
export type UpdateStatus = "Latest" | "Updated" | "No update" | "Unknown";

// ── Main CAE system interface ─────────────────────────────────────────────────
export interface CAESystem {
  id: string;                   // unique slug e.g. "ls-dyna", "openfoam"
  name: string;                 // display name e.g. "LS-DYNA"
  vendor: string;               // company name e.g. "Ansys"
  vendorUrl: string;            // vendor official URL

  domain: CAEDomain[];          // can belong to multiple domains
  solverType: SolverType;
  licenseType: LicenseType;

  os: OSSupport[];              // supported OS list
  hpcSupported: boolean;        // HPC cluster support (HPCクラスター対応)
  gpuSupported: boolean;        // GPU acceleration support

  version?: string;             // latest known version
  releaseDate?: string;         // ISO date "2025-11-01"

  description: string;          // short description (1–2 sentences)
  notes?: string;               // internal notes

  // ── Cron-fetched fields (updated every Monday) ─────────────────────────
  latestNews?: NewsItem[];      // recent news/updates from vendor site
  lastFetched?: string;         // ISO datetime of last cron fetch
  fetchStatus?: UpdateStatus;
}

// ── News item fetched by cron ─────────────────────────────────────────────────
export interface NewsItem {
  title: string;
  url: string;
  date?: string;                // ISO date
  summary?: string;
}

// ── Cron target definition (used by fetch_cae_news.php) ──────────────────────
export interface CAEFetchTarget {
  id: string;                   // matches CAESystem.id
  name: string;
  newsUrl: string;              // URL to fetch news from
  selector?: string;            // CSS selector hint for PHP scraper
}

// ── Filter state (used by React UI) ──────────────────────────────────────────
export interface CAEFilterState {
  domains: CAEDomain[];
  licenseTypes: LicenseType[];
  solverTypes: SolverType[];
  hpcOnly: boolean;
  searchQuery: string;
}

// ── Sort config ───────────────────────────────────────────────────────────────
export type SortKey = keyof Pick<
  CAESystem,
  "name" | "vendor" | "solverType" | "licenseType" | "releaseDate"
>;

export interface SortState {
  key: SortKey;
  direction: "asc" | "desc";
}

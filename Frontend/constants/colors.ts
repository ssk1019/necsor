/**
 * 全站統一的圖表顏色定義。
 * 所有圖表元件都應該從這裡引用顏色，確保跨圖表一致性。
 */
export const CHART_COLORS = {
  // 三大法人
  foreign: "#22c55e",       // 外資 — 綠色
  trust: "#3b82f6",         // 投信 — 藍色
  dealer: "#f59e0b",        // 自營商 — 橙色
  total: "#ef4444",         // 合計 — 紅色

  // 融資融券
  margin: "#ef4444",        // 融資 — 紅色
  short: "#3b82f6",         // 融券 — 藍色
  marginAmount: "#f59e0b",  // 融資金額 — 橙色

  // 台指期
  oi: "#ef4444",            // 未平倉 — 紅色
  price: "#3b82f6",         // 收盤價 — 藍色
  volume: "#94a3b8",        // 成交量 — 灰色

  // 加權指數 vs 匯率
  taiex: "#ef4444",         // 加權指數 — 紅色
  usdTwd: "#3b82f6",        // 匯率 — 藍色

  // 三大法人買賣超（上市/上櫃長條圖細分）
  dealerSelf: "#f59e0b",    // 自營商(自行買賣) — 橙色
  dealerHedge: "#8b5cf6",   // 自營商(避險) — 紫色
  foreignDealer: "#6b7280", // 外資自營商 — 灰色
};

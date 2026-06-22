/**
 * 圖表主題配色 composable。
 * 提供深色模式配色。顏色定義在 constants/colors.ts。
 */

export { CHART_COLORS } from "~/constants/colors";

/**
 * 全站統一的籌碼/維度顏色定義（auto-import friendly）。
 */
export const useChartColors = () => CHART_COLORS;

export function useChartTheme() {
  const colorMode = useColorMode();
  const isDark = computed(() => colorMode.value === "dark");

  const gridColor = computed(() =>
    isDark.value ? "rgba(148, 163, 184, 0.08)" : "rgba(148, 163, 184, 0.1)"
  );

  const tickColor = computed(() =>
    isDark.value ? "#94a3b8" : "#64748b"
  );

  const tooltipBg = computed(() =>
    isDark.value ? "rgba(2, 6, 23, 0.95)" : "rgba(15, 23, 42, 0.92)"
  );

  const legendColor = computed(() =>
    isDark.value ? "#cbd5e1" : "#475569"
  );

  return { isDark, gridColor, tickColor, tooltipBg, legendColor };
}

/**
 * 圖表深色模式配色 composable。
 * 提供根據目前主題動態調整的圖表通用設定。
 */
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

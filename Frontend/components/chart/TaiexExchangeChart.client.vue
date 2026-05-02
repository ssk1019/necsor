<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="chart-title">{{ title }}</h3>
      <div class="chart-controls">
        <button
          v-for="opt in dayOptions"
          :key="opt"
          class="day-btn"
          :class="{ active: selectedDays === opt }"
          @click="$emit('changeDays', opt)"
        >
          {{ opt }}日
        </button>
      </div>
    </div>
    <div class="chart-body">
      <Line v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else class="chart-loading">載入中...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import type { TaiexExchangeRecord } from "~/composables/useMarketApi";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const props = defineProps<{
  title: string;
  records: TaiexExchangeRecord[];
  selectedDays: number;
}>();

defineEmits<{ changeDays: [days: number] }>();

const dayOptions = [7, 14, 30, 60, 90];
const { gridColor, tickColor, tooltipBg, legendColor } = useChartTheme();

const chartData = computed(() => {
  if (!props.records.length) return null;

  const labels = props.records.map((r) => {
    const parts = r.date.split("-");
    return `${parts[1]}/${parts[2]}`;
  });

  const datasets: any[] = [
    {
      label: "加權指數收盤",
      data: props.records.map((r) => r.taiex_close ?? null),
      borderColor: "#ef4444",
      backgroundColor: "rgba(239, 68, 68, 0.06)",
      borderWidth: 2.5,
      pointRadius: props.records.length > 30 ? 0 : 3,
      pointHoverRadius: 5,
      tension: 0.3,
      fill: true,
      yAxisID: "yTaiex",
    },
  ];

  // 匯率資料（可能部分日期沒有）
  const hasRate = props.records.some((r) => r.usd_twd_sell != null);
  if (hasRate) {
    datasets.push({
      label: "USD/TWD 即期賣出",
      data: props.records.map((r) => r.usd_twd_sell ?? null),
      borderColor: "#3b82f6",
      backgroundColor: "transparent",
      borderWidth: 2,
      borderDash: [5, 3],
      pointRadius: props.records.length > 30 ? 0 : 3,
      pointHoverRadius: 5,
      tension: 0.3,
      spanGaps: true,
      yAxisID: "yRate",
    });
  }

  return { labels, datasets };
});

const chartOptions = computed(() => {
  const hasRate = props.records.some((r) => r.usd_twd_sell != null);

  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: {
        position: "bottom" as const,
        labels: { usePointStyle: true, padding: 16, font: { size: 12 }, color: legendColor.value },
      },
      tooltip: {
        backgroundColor: tooltipBg.value,
        titleFont: { size: 13 }, bodyFont: { size: 12 }, padding: 12,
        callbacks: {
          label: (ctx: any) => {
            const val = ctx.parsed.y;
            if (val == null) return "";
            const ds = ctx.dataset.label || "";
            if (ds.includes("USD")) return ` ${ds}: ${val.toFixed(3)}`;
            return ` ${ds}: ${val.toLocaleString()} 點`;
          },
        },
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { font: { size: 11 }, maxRotation: 45, color: tickColor.value } },
      yTaiex: {
        type: "linear" as const,
        position: "left" as const,
        title: { display: true, text: "加權指數", font: { size: 11 }, color: tickColor.value },
        grid: { color: gridColor.value },
        ticks: { font: { size: 11 }, color: tickColor.value, callback: (v: number) => `${(v / 1000).toFixed(0)}K` },
      },
      ...(hasRate ? {
        yRate: {
          type: "linear" as const,
          position: "right" as const,
          title: { display: true, text: "USD/TWD", font: { size: 11 }, color: tickColor.value },
          grid: { drawOnChartArea: false },
          ticks: { font: { size: 11 }, color: tickColor.value },
        },
      } : {}),
    },
  };
});
</script>

<style lang="scss" scoped>
@use "~/assets/scss/chart-card";
</style>

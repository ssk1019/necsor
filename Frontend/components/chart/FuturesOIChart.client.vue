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
      <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else class="chart-loading">載入中...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Bar } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  LineController,
  BarController,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import type { FuturesOIRecord } from "~/composables/useMarketApi";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  LineController,
  BarController,
  Title,
  Tooltip,
  Legend
);

const props = defineProps<{
  title: string;
  records: FuturesOIRecord[];
  selectedDays: number;
}>();

defineEmits<{
  changeDays: [days: number];
}>();

const dayOptions = [7, 14, 30, 60, 90];

const chartData = computed(() => {
  if (!props.records.length) return null;

  const labels = props.records.map((r) => {
    const parts = r.date.split("-");
    return `${parts[1]}/${parts[2]}`;
  });

  return {
    labels,
    datasets: [
      {
        type: "bar" as const,
        label: "成交量（口）",
        data: props.records.map((r) => r.total_volume),
        backgroundColor: "rgba(148, 163, 184, 0.35)",
        borderColor: "rgba(148, 163, 184, 0.6)",
        borderWidth: 1,
        borderRadius: 2,
        yAxisID: "yVolume",
        order: 2,
      },
      {
        type: "line" as const,
        label: "未平倉口數",
        data: props.records.map((r) => r.total_oi),
        borderColor: "#ef4444",
        backgroundColor: "rgba(239, 68, 68, 0.06)",
        borderWidth: 2.5,
        pointRadius: props.records.length > 30 ? 0 : 3,
        pointHoverRadius: 5,
        tension: 0.3,
        fill: true,
        yAxisID: "yOI",
        order: 1,
      },
      {
        type: "line" as const,
        label: "近月收盤價",
        data: props.records.map((r) => r.front_month_close),
        borderColor: "#3b82f6",
        backgroundColor: "transparent",
        borderWidth: 2,
        borderDash: [5, 3],
        pointRadius: 0,
        pointHoverRadius: 5,
        tension: 0.3,
        yAxisID: "yPrice",
        order: 0,
      },
    ],
  };
});

const { gridColor, tickColor, tooltipBg, legendColor } = useChartTheme();

const chartOptions = computed(() => ({
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
          const ds = ctx.dataset.label || "";
          if (ds.includes("收盤")) return ` ${ds}: ${val.toLocaleString()} 點`;
          return ` ${ds}: ${val.toLocaleString()}`;
        },
      },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 11 }, maxRotation: 45, color: tickColor.value } },
    yOI: {
      type: "linear" as const, position: "left" as const,
      title: { display: true, text: "未平倉口數", font: { size: 11 }, color: tickColor.value },
      grid: { color: gridColor.value },
      ticks: { font: { size: 11 }, color: tickColor.value },
    },
    yPrice: {
      type: "linear" as const, position: "right" as const,
      title: { display: true, text: "近月收盤價", font: { size: 11 }, color: tickColor.value },
      grid: { drawOnChartArea: false },
      ticks: { font: { size: 11 }, color: tickColor.value },
    },
    yVolume: { type: "linear" as const, display: false, beginAtZero: true },
  },
}));
</script>

<style lang="scss" scoped>
@use "~/assets/scss/chart-card";
</style>

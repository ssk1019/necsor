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
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import type { FuturesInstitutionalRecord } from "~/composables/useMarketApi";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const props = defineProps<{
  title: string;
  records: FuturesInstitutionalRecord[];
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
        label: "外資 淨未平倉",
        data: props.records.map((r) => r.foreign_investor?.net_oi_volume ?? 0),
        backgroundColor: props.records.map((r) => {
          const v = r.foreign_investor?.net_oi_volume ?? 0;
          return v >= 0 ? "rgba(239, 68, 68, 0.75)" : "rgba(34, 197, 94, 0.75)";
        }),
        borderColor: props.records.map((r) => {
          const v = r.foreign_investor?.net_oi_volume ?? 0;
          return v >= 0 ? "#ef4444" : "#22c55e";
        }),
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: "投信 淨未平倉",
        data: props.records.map((r) => r.investment_trust?.net_oi_volume ?? 0),
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderColor: "#3b82f6",
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: "自營商 淨未平倉",
        data: props.records.map((r) => r.dealer?.net_oi_volume ?? 0),
        backgroundColor: "rgba(245, 158, 11, 0.7)",
        borderColor: "#f59e0b",
        borderWidth: 1,
        borderRadius: 3,
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
      labels: { usePointStyle: true, pointStyle: "rectRounded", padding: 16, font: { size: 12 }, color: legendColor.value },
    },
    tooltip: {
      backgroundColor: tooltipBg.value,
      titleFont: { size: 13 }, bodyFont: { size: 12 }, padding: 12,
      callbacks: {
        label: (ctx: any) => {
          const val = ctx.parsed.y;
          const sign = val >= 0 ? "+" : "";
          return ` ${ctx.dataset.label}: ${sign}${val.toLocaleString()} 口`;
        },
      },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 11 }, maxRotation: 45, color: tickColor.value } },
    y: {
      grid: { color: gridColor.value },
      ticks: { font: { size: 11 }, color: tickColor.value, callback: (val: number) => `${(val / 1000).toFixed(0)}K` },
    },
  },
}));
</script>

<style lang="scss" scoped>
@use "~/assets/scss/chart-card";
</style>

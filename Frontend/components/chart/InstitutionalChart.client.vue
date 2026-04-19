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
import type { InstitutionalRecord } from "~/composables/useMarketApi";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const props = defineProps<{
  title: string;
  records: InstitutionalRecord[];
  selectedDays: number;
}>();

defineEmits<{
  changeDays: [days: number];
}>();

const dayOptions = [7, 14, 30, 60, 90];

// 系列定義：名稱、取值 key、顏色
const seriesDef = [
  { label: "外資及陸資", key: "foreign_investor", color: "#ef4444" },
  { label: "投信", key: "investment_trust", color: "#3b82f6" },
  { label: "自營商(自行買賣)", key: "dealer_self", color: "#f59e0b" },
  { label: "自營商(避險)", key: "dealer_hedge", color: "#8b5cf6" },
  { label: "外資自營商", key: "foreign_dealer", color: "#6b7280" },
  { label: "合計", key: "total", color: "#10b981" },
];

const chartData = computed(() => {
  if (!props.records.length) return null;

  const labels = props.records.map((r) => {
    const parts = r.date.split("-");
    return `${parts[1]}/${parts[2]}`;
  });

  const datasets = seriesDef.map((s) => ({
    label: s.label,
    data: props.records.map((r) => {
      const item = r[s.key as keyof InstitutionalRecord] as
        | { diff: number }
        | undefined;
      return item ? +(item.diff / 1e8).toFixed(2) : 0;
    }),
    backgroundColor: s.color + "cc",
    borderColor: s.color,
    borderWidth: 1,
    borderRadius: 3,
    hidden: s.key === "foreign_dealer",
  }));

  return { labels, datasets };
});

const { gridColor, tickColor, tooltipBg, legendColor } = useChartTheme();

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: "index" as const,
    intersect: false,
  },
  plugins: {
    legend: {
      position: "bottom" as const,
      labels: {
        usePointStyle: true,
        pointStyle: "rectRounded",
        padding: 16,
        font: { size: 12 },
        color: legendColor.value,
      },
    },
    tooltip: {
      backgroundColor: tooltipBg.value,
      titleFont: { size: 13 },
      bodyFont: { size: 12 },
      padding: 12,
      callbacks: {
        label: (ctx: any) => {
          const val = ctx.parsed.y;
          const sign = val >= 0 ? "+" : "";
          return ` ${ctx.dataset.label}: ${sign}${val.toLocaleString()} 億`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { font: { size: 11 }, maxRotation: 45, color: tickColor.value },
    },
    y: {
      grid: { color: gridColor.value },
      ticks: {
        font: { size: 11 },
        color: tickColor.value,
        callback: (val: number) => `${val} 億`,
      },
    },
  },
}));
</script>

<style lang="scss" scoped>
@use "~/assets/scss/chart-card";
</style>

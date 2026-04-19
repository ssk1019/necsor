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
import type { MarginRecord } from "~/composables/useMarketApi";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const props = defineProps<{
  title: string;
  records: MarginRecord[];
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
        label: "融資餘額（萬張）",
        data: props.records.map((r) =>
          r.margin_buy ? +(r.margin_buy.today_balance / 1e4).toFixed(1) : 0
        ),
        borderColor: "#ef4444",
        backgroundColor: "rgba(239, 68, 68, 0.08)",
        borderWidth: 2,
        pointRadius: props.records.length > 30 ? 0 : 3,
        pointHoverRadius: 5,
        tension: 0.3,
        fill: true,
        yAxisID: "y",
      },
      {
        label: "融券餘額（萬張）",
        data: props.records.map((r) =>
          r.short_sell ? +(r.short_sell.today_balance / 1e4).toFixed(1) : 0
        ),
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.08)",
        borderWidth: 2,
        pointRadius: props.records.length > 30 ? 0 : 3,
        pointHoverRadius: 5,
        tension: 0.3,
        fill: true,
        yAxisID: "y1",
      },
      {
        label: "融資金額（億元）",
        data: props.records.map((r) =>
          r.margin_buy_amount
            ? +(r.margin_buy_amount.today_balance / 1e5).toFixed(1)
            : 0
        ),
        borderColor: "#f59e0b",
        backgroundColor: "transparent",
        borderWidth: 2,
        borderDash: [6, 3],
        pointRadius: 0,
        pointHoverRadius: 5,
        tension: 0.3,
        yAxisID: "y2",
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
          if (ds.includes("金額")) return ` ${ds}: ${val.toLocaleString()} 億`;
          return ` ${ds}: ${val.toLocaleString()} 萬張`;
        },
      },
    },
  },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 11 }, maxRotation: 45, color: tickColor.value } },
    y: {
      type: "linear" as const, position: "left" as const,
      title: { display: true, text: "融資（萬張）", font: { size: 11 }, color: tickColor.value },
      grid: { color: gridColor.value },
      ticks: { font: { size: 11 }, color: tickColor.value },
    },
    y1: {
      type: "linear" as const, position: "right" as const,
      title: { display: true, text: "融券（萬張）", font: { size: 11 }, color: tickColor.value },
      grid: { drawOnChartArea: false },
      ticks: { font: { size: 11 }, color: tickColor.value },
    },
    y2: { type: "linear" as const, display: false },
  },
}));
</script>

<style lang="scss" scoped>
@use "~/assets/scss/chart-card";
</style>

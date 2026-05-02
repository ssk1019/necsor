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
    <!-- 期貨商品 Tab -->
    <div class="product-tabs">
      <button
        v-for="(label, key) in productTabs"
        :key="key"
        class="product-tab"
        :class="{ active: activeProduct === key }"
        @click="activeProduct = key"
      >
        {{ label }}
      </button>
    </div>
    <div class="chart-body">
      <Bar v-if="chartData" :key="activeProduct" :data="chartData" :options="chartOptions" />
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
import type { FuturesInstitutionalRecord, FuturesProductData, FuturesInstitutionalItem } from "~/composables/useMarketApi";

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
const productTabs = {
  TX: "臺股期貨",
  MTX: "小型臺指",
  TE: "電子期貨",
  TF: "金融期貨",
  XIF: "非金電期貨",
};
const activeProduct = ref<string>("TX");

const { gridColor, tickColor, tooltipBg, legendColor } = useChartTheme();

// 從記錄中取得指定商品的法人資料（相容新舊格式）
function getProductData(record: FuturesInstitutionalRecord, product: string): FuturesProductData | undefined {
  // 新格式：record.TX / record.TE / ...
  const data = record[product as keyof FuturesInstitutionalRecord] as FuturesProductData | undefined;
  if (data && typeof data === "object" && ("dealer" in data || "investment_trust" in data || "foreign_investor" in data)) {
    return data;
  }
  // 舊格式（只有 TX，直接在根層）
  if (product === "TX" && record.dealer) {
    return {
      dealer: record.dealer,
      investment_trust: record.investment_trust,
      foreign_investor: record.foreign_investor,
    };
  }
  return undefined;
}

const chartData = computed(() => {
  if (!props.records.length) return null;
  const product = activeProduct.value;

  const labels = props.records.map((r) => {
    const parts = r.date.split("-");
    return `${parts[1]}/${parts[2]}`;
  });

  return {
    labels,
    datasets: [
      {
        label: "外資 淨未平倉",
        data: props.records.map((r) => {
          const pd = getProductData(r, product);
          return pd?.foreign_investor?.net_oi_volume ?? 0;
        }),
        backgroundColor: "rgba(34, 197, 94, 0.7)",
        borderColor: "#22c55e",
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: "投信 淨未平倉",
        data: props.records.map((r) => {
          const pd = getProductData(r, product);
          return pd?.investment_trust?.net_oi_volume ?? 0;
        }),
        backgroundColor: "rgba(59, 130, 246, 0.7)",
        borderColor: "#3b82f6",
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: "自營商 淨未平倉",
        data: props.records.map((r) => {
          const pd = getProductData(r, product);
          return pd?.dealer?.net_oi_volume ?? 0;
        }),
        backgroundColor: "rgba(245, 158, 11, 0.7)",
        borderColor: "#f59e0b",
        borderWidth: 1,
        borderRadius: 3,
      },
    ],
  };
});

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

.product-tabs {
  display: flex;
  gap: 0;
  padding: 0 1.5rem;
  border-bottom: 1px solid var(--border-light);
}

.product-tab {
  padding: 0.5rem 1rem;
  border: none;
  border-bottom: 2px solid transparent;
  background: none;
  color: var(--text-muted);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    color: var(--text-primary);
  }

  &.active {
    color: $color-primary;
    border-bottom-color: $color-primary;
  }
}
</style>

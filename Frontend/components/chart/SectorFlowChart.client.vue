<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="chart-title">🏭 類股資金流向（三大法人買賣超）</h3>
      <div class="chart-controls">
        <select class="sort-select" v-model="sortBy" @change="resortData">
          <option value="total">依合計排序</option>
          <option value="foreign">依外資排序</option>
          <option value="trust">依投信排序</option>
          <option value="dealer">依自營商排序</option>
        </select>
        <button class="day-btn" :disabled="loading" @click="loadData">
          {{ loading ? '載入中...' : '刷新' }}
        </button>
      </div>
    </div>
    <div class="chart-body-tall">
      <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
      <div v-else-if="loading" class="chart-loading">載入中（約需 10 秒）...</div>
      <div v-else class="chart-loading">無資料</div>
    </div>
    <!-- 類股選擇按鈕列 -->
    <div v-if="sectorData.length" class="sector-buttons">
      <span class="sector-hint">點擊類股查看個股：</span>
      <button
        v-for="s in sectorData"
        :key="s.sector"
        class="sector-btn"
        :class="{ active: selectedSector?.sector === s.sector }"
        @click="toggleSector(s)"
      >
        {{ s.sector }}
        <span class="btn-count" v-if="s.stocks?.length">({{ s.stocks.length }})</span>
      </button>
    </div>
    <!-- 類股個股明細展開區 -->
    <Transition name="expand">
      <div v-if="selectedSector" class="sector-detail-section">
        <div class="detail-header">
          <span class="detail-title">📋 {{ selectedSector.sector }}</span>
          <span class="detail-count">（{{ selectedSector.stocks?.length || 0 }} 檔個股）</span>
          <button class="detail-close" @click="selectedSector = null">✕</button>
        </div>
        <div class="detail-body">
          <span
            v-for="stock in selectedSector.stocks"
            :key="stock"
            class="stock-tag"
          >{{ stock }}</span>
          <span v-if="!selectedSector.stocks?.length" class="no-data">無個股資料（舊資料需重新抓取）</span>
        </div>
      </div>
    </Transition>
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
import { CHART_COLORS } from "~/constants/colors";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const config = useRuntimeConfig();
const baseUrl = config.public.apiBase;
const { gridColor, tickColor, tooltipBg, legendColor } = useChartTheme();

const loading = ref(false);
const sortBy = ref("total");
const sectorData = ref<any[]>([]);
const selectedSector = ref<any>(null);

const loadData = async () => {
  loading.value = true;
  try {
    const res = await $fetch<{ success: boolean; data: any[] }>(`${baseUrl}/market/sector-flow`);
    if (res.data) {
      sectorData.value = [...res.data].sort((a, b) => b[sortBy.value] - a[sortBy.value]);
    }
  } catch (e) {
    console.error("載入類股資金流向失敗", e);
  }
  loading.value = false;
};

const resortData = () => {
  if (sectorData.value.length) {
    sectorData.value = [...sectorData.value].sort((a, b) => b[sortBy.value] - a[sortBy.value]);
  }
};

const toggleSector = (sector: any) => {
  if (selectedSector.value?.sector === sector.sector) {
    selectedSector.value = null;
  } else {
    selectedSector.value = sector;
  }
};

const chartData = computed(() => {
  if (!sectorData.value.length) return null;

  const labels = sectorData.value.map((d) => d.sector);

  return {
    labels,
    datasets: [
      {
        label: "外資",
        data: sectorData.value.map((d) => +(d.foreign / 1e6).toFixed(1)),
        backgroundColor: CHART_COLORS.foreign + "b3",
        borderColor: CHART_COLORS.foreign,
        borderWidth: 1,
        borderRadius: 2,
      },
      {
        label: "投信",
        data: sectorData.value.map((d) => +(d.trust / 1e6).toFixed(1)),
        backgroundColor: CHART_COLORS.trust + "b3",
        borderColor: CHART_COLORS.trust,
        borderWidth: 1,
        borderRadius: 2,
      },
      {
        label: "自營商",
        data: sectorData.value.map((d) => +(d.dealer / 1e6).toFixed(1)),
        backgroundColor: CHART_COLORS.dealer + "b3",
        borderColor: CHART_COLORS.dealer,
        borderWidth: 1,
        borderRadius: 2,
      },
    ],
  };
});

const chartOptions = computed(() => ({
  indexAxis: "y" as const,
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index" as const, intersect: false },
  plugins: {
    legend: {
      position: "top" as const,
      labels: { usePointStyle: true, pointStyle: "rectRounded", padding: 16, font: { size: 12 }, color: legendColor.value },
    },
    tooltip: {
      backgroundColor: tooltipBg.value,
      titleFont: { size: 13 }, bodyFont: { size: 12 }, padding: 12,
      callbacks: {
        label: (ctx: any) => {
          const val = ctx.parsed.x;
          const sign = val >= 0 ? "+" : "";
          return ` ${ctx.dataset.label}: ${sign}${val.toLocaleString()} 百萬股`;
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: gridColor.value },
      ticks: { font: { size: 11 }, color: tickColor.value, callback: (v: number) => `${v}M` },
    },
    y: {
      grid: { display: false },
      ticks: { font: { size: 12 }, color: tickColor.value },
    },
  },
}));

onMounted(() => { loadData(); });
</script>

<style lang="scss" scoped>
@use "~/assets/scss/chart-card";

.chart-body-tall {
  padding: 1rem 1.5rem 1.5rem;
  height: 700px;
}

.sort-select {
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: $radius-sm;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 0.8rem;
  outline: none;
}

/* 類股按鈕列 */
.sector-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0.75rem 1.5rem;
  border-top: 1px solid var(--border-light);
  align-items: center;
}

.sector-hint {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-right: 0.3rem;
}

.sector-btn {
  padding: 0.3rem 0.7rem;
  border: 1px solid var(--border-color);
  border-radius: 16px;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;

  .btn-count {
    font-size: 0.68rem;
    color: var(--text-muted);
    margin-left: 0.15rem;
  }

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }

  &.active {
    background: $color-primary;
    border-color: $color-primary;
    color: #fff;

    .btn-count {
      color: rgba(255, 255, 255, 0.8);
    }
  }
}

/* 類股個股明細展開區 */
.sector-detail-section {
  border-top: 1px solid var(--border-light);
  padding: 1rem 1.5rem 1.5rem;
  max-height: 400px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}

.detail-title {
  font-weight: 600;
  font-size: 1rem;
  color: var(--text-primary);
}

.detail-count {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-left: 0.4rem;
}

.detail-close {
  margin-left: auto;
  border: none;
  background: none;
  color: var(--text-muted);
  font-size: 1.1rem;
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  transition: all 0.15s;

  &:hover {
    background: var(--bg-hover, rgba(148, 163, 184, 0.15));
    color: var(--text-primary);
  }
}

.detail-body {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.stock-tag {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  background: var(--bg-hover, rgba(148, 163, 184, 0.1));
  border: 1px solid var(--border-light, rgba(148, 163, 184, 0.15));
  border-radius: 4px;
  font-size: 0.78rem;
  color: var(--text-secondary);
  white-space: nowrap;
}

.no-data {
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* 展開動畫 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>

<template>
  <div class="market-page">
    <div class="page-header">
      <h1 class="page-title">市場總覽</h1>
      <p class="page-subtitle">三大法人買賣金額 ・ 融資融券餘額 ・ 台指期未平倉 ・ 期貨三大法人 ・ 台股vs匯率</p>
    </div>

    <!-- 台股 vs 匯率 -->
    <section class="chart-section">
      <ChartTaiexExchangeChart
        title="💱 台股加權指數 vs USD/TWD 匯率"
        :records="taiexData"
        :selected-days="taiexDays"
        @change-days="changeTaiexDays"
      />
    </section>

    <!-- 上市三大法人 -->
    <section class="chart-section">
      <ChartInstitutionalChart
        title="📈 上市 — 三大法人買賣超（億元）"
        :records="twseData"
        :selected-days="twseDays"
        @change-days="changeTwseDays"
      />
    </section>

    <!-- 上櫃三大法人 -->
    <section class="chart-section">
      <ChartInstitutionalChart
        title="📊 上櫃 — 三大法人買賣超（億元）"
        :records="tpexData"
        :selected-days="tpexDays"
        @change-days="changeTpexDays"
      />
    </section>

    <!-- 融資融券餘額 -->
    <section class="chart-section">
      <ChartMarginChart
        title="💰 融資融券餘額趨勢"
        :records="marginData"
        :selected-days="marginDays"
        @change-days="changeMarginDays"
      />
    </section>

    <!-- 台指期未平倉 -->
    <section class="chart-section">
      <ChartFuturesOIChart
        title="📉 台指期未平倉口數 ・ 成交量 ・ 近月收盤"
        :records="futuresData"
        :selected-days="futuresDays"
        @change-days="changeFuturesDays"
      />
    </section>

    <!-- 期貨三大法人未平倉 -->
    <section class="chart-section">
      <ChartFuturesInstitutionalChart
        title="🏛️ 期貨三大法人淨未平倉口數"
        :records="futuresInstData"
        :selected-days="futuresInstDays"
        @change-days="changeFuturesInstDays"
      />
    </section>

    <!-- 未來擴充區塊預留 -->
    <section class="coming-soon">
      <div class="coming-soon-card">
        <span class="coming-soon-icon">🔜</span>
        <p>各類股資訊...即將推出</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { InstitutionalRecord, MarginRecord, FuturesOIRecord, FuturesInstitutionalRecord, TaiexExchangeRecord } from "~/composables/useMarketApi";

useHead({ title: "市場總覽 — Necsor" });

const { fetchInstitutional, fetchMargin, fetchFuturesOI, fetchFuturesInstitutional, fetchTaiexExchange } = useMarketApi();

const twseDays = ref(30);
const tpexDays = ref(30);
const marginDays = ref(30);
const futuresDays = ref(30);
const futuresInstDays = ref(30);
const taiexDays = ref(60);
const twseData = ref<InstitutionalRecord[]>([]);
const tpexData = ref<InstitutionalRecord[]>([]);
const marginData = ref<MarginRecord[]>([]);
const futuresData = ref<FuturesOIRecord[]>([]);
const futuresInstData = ref<FuturesInstitutionalRecord[]>([]);
const taiexData = ref<TaiexExchangeRecord[]>([]);

const loadTwse = async () => {
  try {
    twseData.value = await fetchInstitutional("twse", twseDays.value);
  } catch (e) {
    console.error("載入上市三大法人資料失敗", e);
  }
};

const loadTpex = async () => {
  try {
    tpexData.value = await fetchInstitutional("tpex", tpexDays.value);
  } catch (e) {
    console.error("載入上櫃三大法人資料失敗", e);
  }
};

const loadMargin = async () => {
  try {
    marginData.value = await fetchMargin(marginDays.value);
  } catch (e) {
    console.error("載入融資融券資料失敗", e);
  }
};

const changeTwseDays = (days: number) => {
  twseDays.value = days;
  loadTwse();
};

const changeTpexDays = (days: number) => {
  tpexDays.value = days;
  loadTpex();
};

const changeMarginDays = (days: number) => {
  marginDays.value = days;
  loadMargin();
};

const loadFutures = async () => {
  try {
    futuresData.value = await fetchFuturesOI(futuresDays.value);
  } catch (e) {
    console.error("載入台指期資料失敗", e);
  }
};

const changeFuturesDays = (days: number) => {
  futuresDays.value = days;
  loadFutures();
};

const loadFuturesInst = async () => {
  try {
    futuresInstData.value = await fetchFuturesInstitutional(futuresInstDays.value);
  } catch (e) {
    console.error("載入期貨三大法人資料失敗", e);
  }
};

const changeFuturesInstDays = (days: number) => {
  futuresInstDays.value = days;
  loadFuturesInst();
};

const loadTaiex = async () => {
  try {
    taiexData.value = await fetchTaiexExchange(taiexDays.value);
  } catch (e) {
    console.error("載入台股指數匯率失敗", e);
  }
};

const changeTaiexDays = (days: number) => {
  taiexDays.value = days;
  loadTaiex();
};

onMounted(() => {
  loadTwse();
  loadTpex();
  loadMargin();
  loadFutures();
  loadFuturesInst();
  loadTaiex();
});
</script>

<style lang="scss" scoped>
.market-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin: 0;
}

.chart-section {
  margin-bottom: 2rem;
}

.coming-soon {
  margin-top: 1rem;
}

.coming-soon-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  background: var(--bg-card);
  border: 1px dashed var(--border-color);
  border-radius: $radius-lg;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.coming-soon-icon {
  font-size: 1.25rem;
}
</style>

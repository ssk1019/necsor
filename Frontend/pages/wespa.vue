<template>
  <div class="wespa-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Wespa 股票資料</h1>
        <p class="page-subtitle" v-if="fetchedAt">
          資料更新時間：{{ formatDate(fetchedAt) }}
        </p>
        <p class="page-subtitle" v-else>尚無資料，請點擊按鈕抓取</p>
      </div>
      <button class="refresh-btn" :disabled="loading" @click="refreshData">
        <span v-if="loading" class="spinner"></span>
        <span v-else>🔄</span>
        {{ loading ? progressText : "重新刷新資料" }}
      </button>
    </div>

    <!-- 進度條 -->
    <div v-if="loading" class="progress-bar-container">
      <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
      <span class="progress-text">{{ progressText }}</span>
    </div>

    <!-- 全域搜尋 + 篩選預設 -->
    <div v-if="records.length" class="toolbar">
      <input class="global-search" v-model="globalSearch" placeholder="🔍 全域搜尋（股票代號、公司名稱...）" />

      <!-- 欄位顯示 -->
      <button class="col-toggle-btn" @click="showColPanel = !showColPanel">
        📊 欄位 ({{ visibleColumns.length }}/{{ columns.length }})
      </button>

      <!-- 篩選預設 -->
      <div class="preset-group">
        <select class="preset-select" v-model="selectedPreset" @change="applyPreset">
          <option value="">📋 載入篩選預設...</option>
          <option v-for="p in presets" :key="p.name" :value="p.name">{{ p.name }}</option>
        </select>
        <button class="preset-save-btn" @click="savePreset" title="儲存目前篩選條件">💾</button>
        <button v-if="selectedPreset" class="preset-delete-btn" @click="deletePreset" title="刪除此預設">🗑️</button>
      </div>

      <div class="filter-tags" v-if="activeFilterCount > 0">
        <span class="filter-tag" v-for="(info, col) in activeFilters" :key="col">
          {{ col }}: {{ info }}
          <button @click="removeFilter(col as string)">×</button>
        </span>
        <button class="clear-all-btn" @click="clearAllFilters">清除全部</button>
      </div>
      <div class="table-count">顯示 {{ filteredRecords.length }} / {{ records.length }} 筆</div>
    </div>

    <!-- 進階條件 -->
    <div v-if="records.length" class="advanced-filter">
      <div class="af-header" @click="showAdvanced = !showAdvanced">
        <span>🔧 進階條件（欄位比較）</span>
        <span class="af-toggle">{{ showAdvanced ? '▲' : '▼' }}</span>
        <span v-if="crossFilters.length" class="af-badge">{{ crossFilters.length }}</span>
      </div>
      <div v-if="showAdvanced" class="af-body">
        <div v-for="(cf, idx) in crossFilters" :key="idx" class="af-row">
          <select v-model="cf.colA">
            <option value="">選擇欄位</option>
            <option v-for="c in numericColumns" :key="c" :value="c">{{ c }}</option>
          </select>
          <select v-model="cf.op">
            <option value="<">&lt;</option>
            <option value="<=">&le;</option>
            <option value=">">&gt;</option>
            <option value=">=">&ge;</option>
            <option value="=">=</option>
            <option value="!=">≠</option>
          </select>
          <select v-model="cf.colB">
            <option value="">選擇欄位</option>
            <option v-for="c in numericColumns" :key="c" :value="c">{{ c }}</option>
          </select>
          <button class="af-remove" @click="crossFilters.splice(idx, 1)">✕</button>
        </div>
        <button class="af-add" @click="crossFilters.push({ colA: '', op: '<', colB: '' })">+ 新增條件</button>
      </div>
    </div>

    <!-- 表格 -->
    <div v-if="records.length" class="table-container">
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th v-for="(col, colIdx) in visibleColumns" :key="col"
                class="table-th" :class="{ 'frozen-col': isFrozenCol(col), ['frozen-' + frozenIndex(col)]: isFrozenCol(col) }"
                @click="toggleSort(col)">
                <div class="th-inner">
                  <span class="th-label">{{ col }}</span>
                  <span v-if="sortCol === col" class="sort-icon">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
                  <button
                    class="filter-icon"
                    :class="{ active: filters[col] }"
                    @click.stop="openFilterPanel(col)"
                    title="篩選"
                  >⏷</button>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in paginatedRecords" :key="idx" class="table-row">
              <td v-for="(col, colIdx) in visibleColumns" :key="col"
                class="table-td" :class="{ 'frozen-col': isFrozenCol(col), ['frozen-' + frozenIndex(col)]: isFrozenCol(col) }">
                <template v-if="col === '股票代號'">
                  <a :href="`https://www.wantgoo.com/stock/${row[col]}/technical-chart`"
                     target="_blank" class="stock-link">{{ row[col] }}</a>
                </template>
                <template v-else>{{ formatCell(row[col]) }}</template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 分頁 -->
      <div class="pagination">
        <button :disabled="page <= 1" @click="page--">◀</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="page++">▶</button>
        <select v-model="pageSize">
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
          <option :value="9999">全部</option>
        </select>
      </div>
    </div>

    <div v-else-if="!loading" class="empty-state">
      <p>目前沒有資料，請點擊「重新刷新資料」按鈕開始抓取。</p>
    </div>

    <!-- 欄位選擇面板 -->
    <Teleport to="body">
      <div v-if="showColPanel" class="filter-overlay" @click="showColPanel = false"></div>
      <div v-if="showColPanel" class="filter-panel">
        <div class="fp-header">
          <strong>選擇顯示欄位</strong>
          <button @click="showColPanel = false">✕</button>
        </div>
        <input class="fp-search" v-model="colSearch" placeholder="搜尋欄位..." />
        <div class="fp-select-all">
          <label><input type="checkbox" :checked="hiddenColumns.length === 0" @change="toggleAllColumns" /> 全選</label>
        </div>
        <div class="fp-list">
          <label v-for="col in filteredColumns" :key="col" class="fp-item">
            <input type="checkbox" :checked="!hiddenColumns.includes(col)" @change="toggleColumn(col)" />
            <span :class="{ 'col-has-filter': !!filters[col] }">{{ col }}</span>
          </label>
        </div>
      </div>
    </Teleport>

    <!-- 篩選面板 -->
    <Teleport to="body">
      <div v-if="filterPanel.open" class="filter-overlay" @click="closeFilterPanel"></div>
      <div v-if="filterPanel.open" class="filter-panel" :style="filterPanelStyle">
        <div class="fp-header">
          <strong>{{ filterPanel.col }}</strong>
          <button @click="closeFilterPanel">✕</button>
        </div>

        <!-- 數字範圍篩選 -->
        <template v-if="isNumericCol(filterPanel.col)">
          <div class="fp-range">
            <input type="number" v-model.number="filterPanel.min" placeholder="最小值" />
            <span>~</span>
            <input type="number" v-model.number="filterPanel.max" placeholder="最大值" />
          </div>
          <div class="fp-actions">
            <button class="fp-apply" @click="applyRangeFilter">套用</button>
            <button class="fp-clear" @click="removeFilter(filterPanel.col); closeFilterPanel()">清除</button>
          </div>
        </template>

        <!-- 文字勾選篩選 -->
        <template v-else>
          <input class="fp-search" v-model="filterPanel.search" placeholder="搜尋..." />
          <div class="fp-select-all">
            <label><input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" /> 全選</label>
          </div>
          <div class="fp-list">
            <label v-for="val in filteredUniqueValues" :key="val" class="fp-item">
              <input type="checkbox" :checked="filterPanel.selected.has(val)" @change="toggleValue(val)" />
              <span>{{ val || '(空)' }}</span>
            </label>
          </div>
          <div class="fp-actions">
            <button class="fp-apply" @click="applyTextFilter">套用</button>
            <button class="fp-clear" @click="removeFilter(filterPanel.col); closeFilterPanel()">清除</button>
          </div>
        </template>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
useHead({ title: "Wespa — Necsor" });
const config = useRuntimeConfig();
const baseUrl = config.public.apiBase;

const records = ref<Record<string, any>[]>([]);
const columns = ref<string[]>([]);
const fetchedAt = ref<string | null>(null);
const loading = ref(false);
const progress = ref(0);
const progressText = ref("");
const globalSearch = ref("");
const sortCol = ref<string | null>(null);
const sortDir = ref<"asc" | "desc">("asc");
const page = ref(1);
const pageSize = ref(100);

// 進階條件（欄位間比較）
const showAdvanced = ref(false);
const crossFilters = ref<{ colA: string; op: string; colB: string }[]>([]);
const numericColumns = computed(() => columns.value.filter((col) => isNumericCol(col)));

// 欄位顯示控制
const showColPanel = ref(false);
const hiddenColumns = ref<string[]>([]);
const colSearch = ref("");
const visibleColumns = computed(() => columns.value.filter((col) => !hiddenColumns.value.includes(col)));
const filteredColumns = computed(() => {
  if (!colSearch.value.trim()) return columns.value;
  const s = colSearch.value.toLowerCase();
  return columns.value.filter((col) => col.toLowerCase().includes(s));
});

// 凍結欄位
const FROZEN_COLS = ["股票代號", "公司"];
const isFrozenCol = (col: string) => FROZEN_COLS.includes(col);
const frozenIndex = (col: string) => FROZEN_COLS.indexOf(col);

const toggleColumn = (col: string) => {
  const idx = hiddenColumns.value.indexOf(col);
  if (idx >= 0) hiddenColumns.value.splice(idx, 1);
  else hiddenColumns.value.push(col);
};

const toggleAllColumns = () => {
  if (hiddenColumns.value.length === 0) {
    // 全隱藏（保留股票代號）
    hiddenColumns.value = columns.value.filter((c) => c !== "股票代號");
  } else {
    hiddenColumns.value = [];
  }
};

// 篩選預設（localStorage）
interface FilterPreset {
  name: string;
  globalSearch: string;
  filters: Record<string, any>;
  crossFilters: { colA: string; op: string; colB: string }[];
}

const PRESETS_KEY = "wespa_filter_presets";
const presets = ref<FilterPreset[]>([]);
const selectedPreset = ref("");

const loadPresets = () => {
  try {
    const raw = localStorage.getItem(PRESETS_KEY);
    if (raw) presets.value = JSON.parse(raw);
  } catch { presets.value = []; }
};

const savePresetsToStorage = () => {
  localStorage.setItem(PRESETS_KEY, JSON.stringify(presets.value));
};

const savePreset = () => {
  const name = prompt("請輸入篩選預設名稱：");
  if (!name?.trim()) return;

  // 序列化 filters（Set 不能直接 JSON）
  const serializedFilters: Record<string, any> = {};
  for (const [col, f] of Object.entries(filters.value)) {
    if (f.type === "text") {
      serializedFilters[col] = { type: "text", values: [...f.values] };
    } else {
      serializedFilters[col] = { ...f };
    }
  }

  const preset: FilterPreset = {
    name: name.trim(),
    globalSearch: globalSearch.value,
    filters: serializedFilters,
    crossFilters: [...crossFilters.value],
  };

  // 如果同名則覆蓋
  const idx = presets.value.findIndex((p) => p.name === preset.name);
  if (idx >= 0) presets.value[idx] = preset;
  else presets.value.push(preset);

  savePresetsToStorage();
  selectedPreset.value = preset.name;
  alert(`已儲存篩選預設「${preset.name}」`);
};

const applyPreset = () => {
  const name = selectedPreset.value;
  if (!name) return;
  const preset = presets.value.find((p) => p.name === name);
  if (!preset) return;

  // 還原 filters
  const restoredFilters: Record<string, any> = {};
  for (const [col, f] of Object.entries(preset.filters)) {
    if (f.type === "text") {
      restoredFilters[col] = { type: "text", values: new Set(f.values) };
    } else {
      restoredFilters[col] = { ...f };
    }
  }

  globalSearch.value = preset.globalSearch || "";
  filters.value = restoredFilters;
  crossFilters.value = [...(preset.crossFilters || [])];
  showAdvanced.value = crossFilters.value.length > 0;
  page.value = 1;
};

const deletePreset = () => {
  const name = selectedPreset.value;
  if (!name) return;
  if (!confirm(`確定要刪除篩選預設「${name}」嗎？`)) return;
  presets.value = presets.value.filter((p) => p.name !== name);
  savePresetsToStorage();
  selectedPreset.value = "";
};

// 篩選狀態：col -> { type: 'text', values: Set } | { type: 'range', min, max }
const filters = ref<Record<string, any>>({});

// 篩選面板
const filterPanel = ref({
  open: false,
  col: "",
  search: "",
  selected: new Set<string>(),
  min: null as number | null,
  max: null as number | null,
});
const filterPanelStyle = ref({});

const activeFilterCount = computed(() => Object.keys(filters.value).length);
const activeFilters = computed(() => {
  const result: Record<string, string> = {};
  for (const [col, f] of Object.entries(filters.value)) {
    if (f.type === "range") {
      const parts = [];
      if (f.min != null) parts.push(`≥${f.min}`);
      if (f.max != null) parts.push(`≤${f.max}`);
      result[col] = parts.join(" ");
    } else {
      result[col] = `${f.values.size} 項`;
    }
  }
  return result;
});

const isNumericCol = (col: string) => {
  const sample = records.value.find((r) => r[col] != null);
  return sample && typeof sample[col] === "number";
};

const getUniqueValues = (col: string): string[] => {
  const vals = new Set<string>();
  for (const r of records.value) {
    vals.add(String(r[col] ?? ""));
  }
  return [...vals].sort();
};

const filteredUniqueValues = computed(() => {
  const all = getUniqueValues(filterPanel.value.col);
  if (!filterPanel.value.search) return all.slice(0, 200);
  const s = filterPanel.value.search.toLowerCase();
  return all.filter((v) => v.toLowerCase().includes(s)).slice(0, 200);
});

const isAllSelected = computed(() => {
  return filteredUniqueValues.value.every((v) => filterPanel.value.selected.has(v));
});

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    for (const v of filteredUniqueValues.value) filterPanel.value.selected.delete(v);
  } else {
    for (const v of filteredUniqueValues.value) filterPanel.value.selected.add(v);
  }
};

const toggleValue = (val: string) => {
  if (filterPanel.value.selected.has(val)) filterPanel.value.selected.delete(val);
  else filterPanel.value.selected.add(val);
};

const openFilterPanel = (col: string) => {
  const existing = filters.value[col];
  filterPanel.value = {
    open: true,
    col,
    search: "",
    selected: existing?.type === "text" ? new Set(existing.values) : new Set(getUniqueValues(col)),
    min: existing?.type === "range" ? existing.min : null,
    max: existing?.type === "range" ? existing.max : null,
  };
};

const closeFilterPanel = () => { filterPanel.value.open = false; };

const applyTextFilter = () => {
  const allValues = new Set(getUniqueValues(filterPanel.value.col));
  if (filterPanel.value.selected.size === allValues.size) {
    delete filters.value[filterPanel.value.col];
  } else {
    filters.value[filterPanel.value.col] = { type: "text", values: new Set(filterPanel.value.selected) };
  }
  page.value = 1;
  closeFilterPanel();
};

const applyRangeFilter = () => {
  const { min, max } = filterPanel.value;
  if (min == null && max == null) {
    delete filters.value[filterPanel.value.col];
  } else {
    filters.value[filterPanel.value.col] = { type: "range", min, max };
  }
  page.value = 1;
  closeFilterPanel();
};

const removeFilter = (col: string) => { delete filters.value[col]; page.value = 1; };
const clearAllFilters = () => { filters.value = {}; globalSearch.value = ""; page.value = 1; };
const toggleSort = (col: string) => {
  if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  else { sortCol.value = col; sortDir.value = "asc"; }
};

const filteredRecords = computed(() => {
  let data = [...records.value];

  // 全域搜尋
  if (globalSearch.value.trim()) {
    const s = globalSearch.value.toLowerCase();
    data = data.filter((r) => Object.values(r).some((v) => v != null && String(v).toLowerCase().includes(s)));
  }

  // 欄位篩選
  for (const [col, f] of Object.entries(filters.value)) {
    if (f.type === "text") {
      data = data.filter((r) => f.values.has(String(r[col] ?? "")));
    } else if (f.type === "range") {
      data = data.filter((r) => {
        const v = parseFloat(r[col]);
        if (isNaN(v)) return false;
        if (f.min != null && v < f.min) return false;
        if (f.max != null && v > f.max) return false;
        return true;
      });
    }
  }

  // 進階條件（欄位間比較）
  for (const cf of crossFilters.value) {
    if (!cf.colA || !cf.colB) continue;
    data = data.filter((r) => {
      const a = parseFloat(r[cf.colA]);
      const b = parseFloat(r[cf.colB]);
      if (isNaN(a) || isNaN(b)) return false;
      switch (cf.op) {
        case "<": return a < b;
        case "<=": return a <= b;
        case ">": return a > b;
        case ">=": return a >= b;
        case "=": return a === b;
        case "!=": return a !== b;
        default: return true;
      }
    });
  }

  // 排序
  if (sortCol.value) {
    const col = sortCol.value;
    const dir = sortDir.value === "asc" ? 1 : -1;
    data.sort((a, b) => {
      const va = a[col], vb = b[col];
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      if (typeof va === "number" && typeof vb === "number") return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
  }
  return data;
});

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value)));
const paginatedRecords = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return filteredRecords.value.slice(start, start + pageSize.value);
});

const formatDate = (dateStr: string) => new Date(dateStr).toLocaleString("zh-TW", { timeZone: "Asia/Taipei" });
const formatCell = (val: any) => {
  if (val == null) return "-";
  if (typeof val === "number") return Number.isInteger(val) ? val.toLocaleString() : val.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return val;
};

const loadData = async () => {
  try {
    const res = await $fetch<{ success: boolean; data: any[]; fetched_at: string | null }>(`${baseUrl}/wespa`);
    if (res.data?.length) { records.value = res.data; columns.value = Object.keys(res.data[0]); fetchedAt.value = res.fetched_at; }
  } catch (e) { console.error("載入失敗", e); }
};

const refreshData = async () => {
  loading.value = true; progress.value = 0; progressText.value = "正在連接...";
  try {
    const iv = setInterval(() => { if (progress.value < 85) { progress.value += Math.random() * 10; progressText.value = `抓取中 ${Math.min(Math.floor(progress.value / 14) + 1, 6)}/6...`; } }, 1500);
    const res = await $fetch<{ success: boolean; count: number; fetched_at: string }>(`${baseUrl}/wespa/refresh`, { method: "POST" });
    clearInterval(iv); progress.value = 100; progressText.value = `完成！${res.count} 筆`;
    await loadData();
    setTimeout(() => { loading.value = false; progress.value = 0; }, 1500);
  } catch (e) { loading.value = false; progress.value = 0; alert("抓取失敗"); }
};

onMounted(() => { loadPresets(); loadData(); });
</script>

<style lang="scss" scoped>
.wespa-page { max-width: 100%; margin: 0 auto; padding: 1.5rem; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; gap: 1rem; }
.header-left { flex: 1; }
.page-title { font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin: 0 0 0.2rem; }
.page-subtitle { color: var(--text-secondary); font-size: 0.85rem; margin: 0; }

.refresh-btn { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border: none; border-radius: $radius-md; background: $color-primary; color: #fff; font-size: 0.85rem; font-weight: 500; cursor: pointer; white-space: nowrap; &:hover:not(:disabled) { opacity: 0.9; } &:disabled { opacity: 0.7; cursor: not-allowed; } }
.spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.progress-bar-container { position: relative; height: 24px; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: $radius-md; margin-bottom: 1rem; overflow: hidden; }
.progress-bar { height: 100%; background: $color-primary; transition: width 0.3s; }
.progress-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 0.75rem; color: var(--text-primary); }

.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.global-search { flex: 1; min-width: 200px; padding: 0.5rem 0.75rem; border: 1px solid var(--border-color); border-radius: $radius-md; background: var(--bg-card); color: var(--text-primary); font-size: 0.85rem; outline: none; &:focus { border-color: $color-primary; } &::placeholder { color: var(--text-muted); } }
.filter-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }

.col-toggle-btn {
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--border-color);
  border-radius: $radius-sm;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }
}

.col-has-filter {
  color: $color-primary;
  font-weight: 600;
}

// 篩選預設
.preset-group {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.preset-select {
  padding: 0.4rem 0.6rem;
  border: 1px solid var(--border-color);
  border-radius: $radius-sm;
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 0.8rem;
  outline: none;
  min-width: 160px;

  &:focus {
    border-color: $color-primary;
  }
}

.preset-save-btn,
.preset-delete-btn {
  border: 1px solid var(--border-color);
  border-radius: $radius-sm;
  background: var(--bg-card);
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0.3rem 0.5rem;
  line-height: 1;

  &:hover {
    border-color: $color-primary;
    background: var(--bg-secondary);
  }
}

.preset-delete-btn:hover {
  border-color: $color-danger;
}
.filter-tag { display: flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.5rem; background: rgba($color-primary, 0.1); border-radius: $radius-sm; font-size: 0.75rem; color: $color-primary; button { border: none; background: none; color: $color-primary; cursor: pointer; font-size: 0.85rem; padding: 0; } }
.clear-all-btn { padding: 0.2rem 0.5rem; border: 1px solid var(--border-color); border-radius: $radius-sm; background: var(--bg-card); color: var(--text-secondary); font-size: 0.7rem; cursor: pointer; }
.table-count { font-size: 0.8rem; color: var(--text-muted); margin-left: auto; }

.table-container { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: $radius-lg; overflow: hidden; }
.table-scroll { overflow-x: auto; max-height: 65vh; overflow-y: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }

.table-th { position: sticky; top: 0; background: var(--bg-secondary); z-index: 2; padding: 0.5rem; border-bottom: 2px solid var(--border-color); white-space: nowrap; cursor: pointer; user-select: none; &:hover { background: var(--bg-card); } }

// 凍結欄位
.frozen-col {
  position: sticky;
  z-index: 3;
  background: var(--bg-secondary);
  border-right: 2px solid var(--border-color);
}

th.frozen-col {
  z-index: 4;
}

.frozen-0 { left: 0; }
.frozen-1 { left: 80px; }

tr .frozen-col {
  background: var(--bg-card);
}

tr:hover .frozen-col {
  background: rgba($color-primary, 0.03);
}
.th-inner { display: flex; align-items: center; gap: 0.3rem; }
.th-label { font-weight: 600; color: var(--text-primary); font-size: 0.75rem; }
.sort-icon { font-size: 0.6rem; color: $color-primary; }
.filter-icon { border: none; background: none; color: var(--text-muted); font-size: 0.7rem; cursor: pointer; padding: 0 2px; opacity: 0.5; &:hover, &.active { opacity: 1; color: $color-primary; } }

.table-row { &:hover { background: rgba($color-primary, 0.03); } }
.table-td { padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border-light); white-space: nowrap; color: var(--text-primary); }
.stock-link { color: $color-primary; font-weight: 500; text-decoration: none; &:hover { text-decoration: underline; } }

.pagination { display: flex; align-items: center; gap: 0.5rem; padding: 0.6rem 1rem; border-top: 1px solid var(--border-light); font-size: 0.8rem; color: var(--text-secondary);
  button { padding: 0.25rem 0.6rem; border: 1px solid var(--border-color); border-radius: $radius-sm; background: var(--bg-card); color: var(--text-primary); cursor: pointer; &:disabled { opacity: 0.4; cursor: not-allowed; } }
  select { padding: 0.25rem; border: 1px solid var(--border-color); border-radius: $radius-sm; background: var(--bg-card); color: var(--text-primary); font-size: 0.75rem; }
}

.empty-state { text-align: center; padding: 4rem 2rem; color: var(--text-muted); }

// 進階條件
.advanced-filter {
  margin-bottom: 1rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: $radius-md;
  overflow: hidden;
}

.af-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--text-secondary);
  user-select: none;

  &:hover {
    background: var(--bg-secondary);
  }
}

.af-toggle {
  font-size: 0.65rem;
}

.af-badge {
  background: $color-primary;
  color: #fff;
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  font-weight: 600;
}

.af-body {
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.af-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;

  select {
    flex: 1;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: $radius-sm;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.8rem;
    outline: none;

    &:focus {
      border-color: $color-primary;
    }
  }

  select:nth-child(2) {
    flex: 0 0 60px;
    text-align: center;
  }
}

.af-remove {
  border: none;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 0 0.3rem;

  &:hover {
    color: $color-danger;
  }
}

.af-add {
  align-self: flex-start;
  padding: 0.35rem 0.75rem;
  border: 1px dashed var(--border-color);
  border-radius: $radius-sm;
  background: none;
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;

  &:hover {
    border-color: $color-primary;
    color: $color-primary;
  }
}

// 篩選面板
.filter-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.15);
}

.filter-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1000;
  width: 320px;
  max-height: 420px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: $radius-lg;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.fp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
  font-size: 0.9rem;

  button {
    border: none;
    background: none;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 1.2rem;
    line-height: 1;
    padding: 0;
  }
}

.fp-search {
  display: block;
  width: calc(100% - 1.5rem);
  margin: 0.6rem auto;
  padding: 0.45rem 0.7rem;
  border: 1px solid var(--border-color);
  border-radius: $radius-sm;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.82rem;
  outline: none;
  box-sizing: border-box;

  &:focus {
    border-color: $color-primary;
  }

  &::placeholder {
    color: var(--text-muted);
  }
}

.fp-select-all {
  padding: 0.4rem 0.75rem;
  border-bottom: 1px solid var(--border-light);
  font-size: 0.82rem;
  color: var(--text-secondary);

  label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  input[type="checkbox"] {
    width: 15px;
    height: 15px;
    margin: 0;
    cursor: pointer;
  }
}

.fp-list {
  flex: 1;
  overflow-y: auto;
  max-height: 200px;
  padding: 0.3rem 0;
}

.fp-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.75rem;
  font-size: 0.8rem;
  color: var(--text-primary);
  cursor: pointer;

  &:hover {
    background: rgba($color-primary, 0.05);
  }

  input[type="checkbox"] {
    width: 14px;
    height: 14px;
    margin: 0;
    flex-shrink: 0;
    cursor: pointer;
  }

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.fp-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 0.75rem;

  input[type="number"] {
    flex: 1;
    width: 0;
    padding: 0.45rem 0.6rem;
    border: 1px solid var(--border-color);
    border-radius: $radius-sm;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 0.82rem;
    outline: none;
    box-sizing: border-box;

    &:focus {
      border-color: $color-primary;
    }

    &::placeholder {
      color: var(--text-muted);
    }
  }

  span {
    color: var(--text-muted);
    font-size: 0.85rem;
  }
}

.fp-actions {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  border-top: 1px solid var(--border-light);
}

.fp-apply {
  flex: 1;
  padding: 0.5rem;
  border: none;
  border-radius: $radius-sm;
  background: $color-primary;
  color: #fff;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;

  &:hover {
    opacity: 0.9;
  }
}

.fp-clear {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: $radius-sm;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 0.82rem;
  cursor: pointer;

  &:hover {
    background: var(--bg-secondary);
  }
}
</style>

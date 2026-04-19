<template>
  <div class="layout-default">
    <header class="layout-header">
      <div class="header-inner">
        <NuxtLink to="/" class="logo">Necsor</NuxtLink>
        <nav class="nav-links">
          <NuxtLink to="/market" class="nav-link">市場總覽</NuxtLink>
        </nav>
        <div class="header-actions">
          <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切換淺色模式' : '切換深色模式'">
            <span v-if="isDark">☀️</span>
            <span v-else>🌙</span>
          </button>
        </div>
      </div>
    </header>

    <main class="layout-main">
      <slot />
    </main>

    <footer class="layout-footer">
      <p>&copy; {{ new Date().getFullYear() }} Necsor</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
const colorMode = useColorMode();
const isDark = computed(() => colorMode.value === "dark");

const toggleTheme = () => {
  colorMode.preference = isDark.value ? "light" : "dark";
};
</script>

<style lang="scss" scoped>
.layout-default {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.layout-header {
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: background-color 0.2s, border-color 0.2s;
}

.header-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 2rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: $color-primary;
  text-decoration: none;
  letter-spacing: -0.02em;
}

.nav-links {
  display: flex;
  gap: 0.25rem;
  flex: 1;
}

.nav-link {
  padding: 0.375rem 0.875rem;
  border-radius: $radius-md;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.15s;

  &:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  &.router-link-active {
    background: rgba($color-primary, 0.12);
    color: $color-primary;
  }
}

.header-actions {
  display: flex;
  align-items: center;
}

.theme-toggle {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  border-radius: $radius-md;
  background: var(--bg-card);
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.15s;

  &:hover {
    border-color: $color-primary;
    background: var(--bg-secondary);
  }
}

.layout-main {
  flex: 1;
}

.layout-footer {
  padding: 1rem 2rem;
  text-align: center;
  border-top: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.8rem;
  background: var(--bg-header);
  transition: background-color 0.2s, border-color 0.2s, color 0.2s;
}
</style>

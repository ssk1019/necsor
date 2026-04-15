<template>
  <div class="layout-default">
    <header class="layout-header">
      <nav>
        <NuxtLink to="/">Home</NuxtLink>
      </nav>
    </header>

    <main class="layout-main">
      <slot />
    </main>

    <footer class="layout-footer">
      <p>&copy; {{ new Date().getFullYear() }} MyApp</p>
    </footer>
  </div>
</template>

<style lang="scss" scoped>
.layout-default {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.layout-header {
  padding: 1rem 2rem;
  border-bottom: 1px solid #e2e8f0;
}

.layout-main {
  flex: 1;
  padding: 2rem;
}

.layout-footer {
  padding: 1rem 2rem;
  text-align: center;
  border-top: 1px solid #e2e8f0;
  color: $color-text-light;
}
</style>

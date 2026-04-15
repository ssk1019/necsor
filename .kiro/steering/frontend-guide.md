---
inclusion: fileMatch
fileMatchPattern: "Frontend/**"
---

# Frontend Development Guide

## Directory Structure

```
Frontend/
├── assets/scss/
│   ├── _variables.scss       # Design tokens (colors, fonts, breakpoints, shadows)
│   └── main.scss             # Global reset + base styles
├── components/
│   └── ui/                   # Reusable UI components (AppButton, etc.)
├── composables/
│   └── useApi.ts             # API call wrapper (uses runtimeConfig.public.apiBase)
├── layouts/
│   └── default.vue           # Default page layout (header/main/footer)
├── middleware/                # Route middleware (auth guards, etc.)
├── pages/                    # File-based routing
│   └── index.vue             # Home page
├── plugins/                  # Nuxt plugins (runs on app init)
├── public/                   # Static assets (favicon, robots.txt)
├── server/                   # Nitro server routes (API proxy, SSR helpers)
├── stores/
│   └── app.ts                # Pinia global store (isLoading, sidebarOpen)
├── types/
│   └── index.ts              # Shared TS types (ApiResponse, PaginatedResponse)
├── .env                      # Environment variables (NUXT_PUBLIC_API_BASE)
├── .env.example              # Template
├── .nuxtrc                   # Nuxt local config (telemetry disabled)
├── nuxt.config.ts            # Nuxt configuration
├── package.json              # Dependencies + scripts
└── tsconfig.json             # TypeScript config
```

## Conventions

- **Components:** Place reusable UI components in `components/ui/`. Feature-specific components go in `components/<feature>/`. Nuxt auto-imports all components.

- **Composables:** Place shared logic in `composables/`. Nuxt auto-imports them. Use `useApi()` for backend calls.

- **Pages:** File-based routing. `pages/about.vue` → `/about`. Dynamic routes: `pages/users/[id].vue`.

- **Stores:** One Pinia store per domain in `stores/`. Use `defineStore()` with Nuxt auto-import.

- **Styling:** Global SCSS variables from `_variables.scss` are injected into all components via `nuxt.config.ts` `vite.css.preprocessorOptions`. Use `<style lang="scss" scoped>` in components.

- **Types:** Backend response types are mirrored in `types/index.ts` (ApiResponse, PaginatedResponse).

- **API calls:** Use the `useApi()` composable which prepends `runtimeConfig.public.apiBase`. For server-side calls, use `$fetch` directly.

## Running

```bash
# Development (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Note:** Nuxt telemetry has been disabled (via `.nuxtrc`) to prevent interactive prompts from blocking the dev server. If telemetry prompt reappears after updates, run `npx nuxt telemetry disable` in `Frontend/`.

## Nuxt Modules Installed

| Module | Purpose |
|--------|---------|
| @pinia/nuxt | State management |
| @vueuse/nuxt | Vue composition utilities |
| @nuxt/eslint | Linting |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| NUXT_PUBLIC_API_BASE | http://localhost:8000/api/v1 | Backend API base URL |

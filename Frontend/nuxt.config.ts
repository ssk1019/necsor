// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-05-15",
  devtools: { enabled: true },

  // Modules
  modules: [
    "@pinia/nuxt",
    "@vueuse/nuxt",
    "@nuxt/eslint",
  ],

  // Runtime config (env variables)
  runtimeConfig: {
    // Server-side only
    apiSecret: "",
    // Public (exposed to client)
    public: {
      apiBase: "http://localhost:8000/api/v1",
    },
  },

  // App metadata
  app: {
    head: {
      charset: "utf-8",
      viewport: "width=device-width, initial-scale=1",
      title: "MyApp",
      meta: [
        { name: "description", content: "MyApp — High Performance Web App" },
      ],
    },
  },

  // CSS
  css: ["~/assets/scss/main.scss"],

  // Vite config
  vite: {
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@use "~/assets/scss/_variables" as *;`,
        },
      },
    },
  },

  // TypeScript
  typescript: {
    strict: true,
  },
});

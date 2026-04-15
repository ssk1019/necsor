/**
 * Global application store.
 */
export const useAppStore = defineStore("app", {
  state: () => ({
    isLoading: false,
    sidebarOpen: true,
  }),

  actions: {
    setLoading(value: boolean) {
      this.isLoading = value;
    },
    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen;
    },
  },
});

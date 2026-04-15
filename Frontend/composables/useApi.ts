/**
 * Composable for making API calls to the backend.
 * Wraps useFetch with base URL and common options.
 */
export function useApi<T>(path: string, options: Record<string, unknown> = {}) {
  const config = useRuntimeConfig();

  return useFetch<T>(`${config.public.apiBase}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    },
  });
}

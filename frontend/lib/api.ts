import { API_URL } from "./constants";

export const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

import { apiFetch } from "./http";

export const buscarStats = () => apiFetch("/dashboard/stats");

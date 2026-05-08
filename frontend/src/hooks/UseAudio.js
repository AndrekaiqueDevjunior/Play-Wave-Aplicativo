/**
 * hooks/useAudio.js
 * Hooks para Rádio Indoor — faixas e playlists sonoras.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";

// ── Faixas ────────────────────────────────────────────────────────────────────

export function useFaixasAudio(filtros = {}) {
  return useQuery({
    queryKey: ["faixas-audio", filtros],
    queryFn: () =>
      Object.keys(filtros).length
        ? base44.entities.AudioTrack.filter(filtros)
        : base44.entities.AudioTrack.list("-created_date"),
    initialData: [],
  });
}

export function useSalvarFaixa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) =>
      id
        ? base44.entities.AudioTrack.update(id, dados)
        : base44.entities.AudioTrack.create(dados),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["faixas-audio"] }),
  });
}

// ── Playlists ─────────────────────────────────────────────────────────────────

export function usePlaylistsSonoras(filtros = {}) {
  return useQuery({
    queryKey: ["playlists-sonoras", filtros],
    queryFn: () =>
      Object.keys(filtros).length
        ? base44.entities.AudioPlaylist.filter(filtros)
        : base44.entities.AudioPlaylist.list("-created_date"),
    initialData: [],
  });
}

export function useSalvarPlaylist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) =>
      id
        ? base44.entities.AudioPlaylist.update(id, dados)
        : base44.entities.AudioPlaylist.create(dados),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playlists-sonoras"] }),
  });
}

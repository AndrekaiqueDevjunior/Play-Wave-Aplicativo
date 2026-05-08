import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listarFaixas,
  uploadFaixa,
  atualizarFaixa,
  listarPlaylistsAudio,
  criarPlaylistAudio,
  atualizarPlaylistAudio,
} from "@/api/audio";

// ── Faixas ────────────────────────────────────────────────────────────────────

export function useFaixasAudio(filtros = {}) {
  return useQuery({
    queryKey: ["faixas-audio", filtros],
    queryFn: () => listarFaixas(filtros),
    initialData: [],
  });
}

export function useSalvarFaixa() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) => {
      if (id) return atualizarFaixa(id, dados);
      const { file, ...metadata } = dados;
      return uploadFaixa(file, metadata);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["faixas-audio"] }),
  });
}

// ── Playlists ─────────────────────────────────────────────────────────────────

export function usePlaylistsSonoras(filtros = {}) {
  return useQuery({
    queryKey: ["playlists-sonoras", filtros],
    queryFn: () => listarPlaylistsAudio(filtros),
    initialData: [],
  });
}

export function useSalvarPlaylist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) =>
      id ? atualizarPlaylistAudio(id, dados) : criarPlaylistAudio(dados),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["playlists-sonoras"] }),
  });
}

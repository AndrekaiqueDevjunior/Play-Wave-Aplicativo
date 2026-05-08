/**
 * hooks/useCampanha.js
 * Hook para buscar e gerenciar campanhas.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";

export function useCampanhas(filtros = {}) {
  return useQuery({
    queryKey: ["campanhas", filtros],
    queryFn: () =>
      Object.keys(filtros).length
        ? base44.entities.Campaign.filter(filtros)
        : base44.entities.Campaign.list("-updated_date"),
    initialData: [],
  });
}

export function useCampanha(id) {
  return useQuery({
    queryKey: ["campanha", id],
    queryFn: () => base44.entities.Campaign.filter({ id }),
    select: (data) => data[0],
    enabled: !!id,
  });
}

export function useSalvarCampanha() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) =>
      id
        ? base44.entities.Campaign.update(id, dados)
        : base44.entities.Campaign.create(dados),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campanhas"] }),
  });
}

export function useDeletarCampanha() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => base44.entities.Campaign.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campanhas"] }),
  });
}

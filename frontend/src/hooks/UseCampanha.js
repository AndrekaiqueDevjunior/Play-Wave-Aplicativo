import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listarCampanhas,
  buscarCampanha,
  criarCampanha,
  atualizarCampanha,
  deletarCampanha,
} from "@/api/campanhas";

export function useCampanhas(filtros = {}) {
  return useQuery({
    queryKey: ["campanhas", filtros],
    queryFn: () => listarCampanhas(filtros),
    initialData: [],
  });
}

export function useCampanha(id) {
  return useQuery({
    queryKey: ["campanha", id],
    queryFn: () => buscarCampanha(id),
    enabled: !!id,
  });
}

export function useSalvarCampanha() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) =>
      id ? atualizarCampanha(id, dados) : criarCampanha(dados),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campanhas"] }),
  });
}

export function useDeletarCampanha() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id) => deletarCampanha(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campanhas"] }),
  });
}

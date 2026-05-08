import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  buscarDispositivo,
  listarDispositivos,
  atualizarDispositivo,
} from "@/api/dispositivos";

export function useDispositivo(id) {
  return useQuery({
    queryKey: ["dispositivo", id],
    queryFn: () => buscarDispositivo(id),
    enabled: !!id,
  });
}

export function useDispositivosLista(filtros = {}) {
  return useQuery({
    queryKey: ["dispositivos", filtros],
    queryFn: () => listarDispositivos(filtros),
  });
}

export function useAtualizarDispositivo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) => atualizarDispositivo(id, dados),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dispositivos"] });
      qc.invalidateQueries({ queryKey: ["dispositivo"] });
    },
  });
}

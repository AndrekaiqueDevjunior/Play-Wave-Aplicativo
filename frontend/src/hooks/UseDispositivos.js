/**
 * hooks/useDispositivo.js
 * Hook para buscar e gerenciar um dispositivo pelo ID.
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";

export function useDispositivo(id) {
  return useQuery({
    queryKey: ["dispositivo", id],
    queryFn: () => base44.entities.Device.filter({ id }),
    select: (data) => data[0],
    enabled: !!id,
  });
}

export function useDispositivosLista(filtros = {}) {
  return useQuery({
    queryKey: ["dispositivos", filtros],
    queryFn: () =>
      Object.keys(filtros).length
        ? base44.entities.Device.filter(filtros)
        : base44.entities.Device.list("-updated_date"),
  });
}

export function useAtualizarDispositivo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dados }) => base44.entities.Device.update(id, dados),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dispositivos"] });
      qc.invalidateQueries({ queryKey: ["dispositivo"] });
    },
  });
}

import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Ban,
  Clock,
  Link as LinkIcon,
  RefreshCw,
  ShieldCheck,
  ShieldOff,
  AlertTriangle,
} from "lucide-react";
import moment from "moment";
import { listarEventosPareamento } from "@/api/dispositivos";

const EVENT_META = {
  paired:            { label: "Pareado",             icon: LinkIcon,   className: "text-emerald-600 bg-emerald-50 border-emerald-200" },
  re_paired:         { label: "Re-pareado",          icon: LinkIcon,   className: "text-blue-600 bg-blue-50 border-blue-200" },
  code_regenerated:  { label: "Código regenerado",   icon: RefreshCw,  className: "text-amber-700 bg-amber-50 border-amber-200" },
  force_repair:     { label: "Reparamento forçado", icon: AlertTriangle, className: "text-orange-700 bg-orange-50 border-orange-200" },
  token_revoked:     { label: "Token revogado",      icon: ShieldOff,  className: "text-slate-700 bg-slate-100 border-slate-200" },
  code_expired:      { label: "Código expirou",      icon: Clock,      className: "text-slate-500 bg-slate-50 border-slate-200" },
  device_blocked:    { label: "Bloqueado",           icon: Ban,        className: "text-red-700 bg-red-50 border-red-200" },
  device_unblocked:  { label: "Desbloqueado",        icon: ShieldCheck, className: "text-emerald-700 bg-emerald-50 border-emerald-200" },
};

/**
 * PairingEventTimeline — histórico de eventos de pareamento (SPEC 004).
 */
export default function PairingEventTimeline({ deviceId, limit = 20 }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["device-pairing-events", deviceId, limit],
    queryFn: () => listarEventosPareamento(deviceId, { limit }),
    enabled: !!deviceId,
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return (
      <div className="text-center py-6 text-sm text-muted-foreground">
        Carregando histórico…
      </div>
    );
  }
  if (error) {
    return (
      <div className="text-center py-6 text-sm text-red-600">
        Erro ao carregar histórico de pareamento.
      </div>
    );
  }
  const items = data?.items || [];
  if (items.length === 0) {
    return (
      <div className="text-center py-6 text-sm text-muted-foreground">
        Nenhum evento registrado ainda.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((ev) => {
        const meta = EVENT_META[ev.event_type] || {
          label: ev.event_type,
          icon: LinkIcon,
          className: "text-slate-700 bg-slate-50 border-slate-200",
        };
        const Icon = meta.icon;
        return (
          <div
            key={ev.id}
            className={`flex gap-3 p-3 border rounded-lg ${meta.className}`}
          >
            <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium">{meta.label}</span>
                <span className="text-xs opacity-60">
                  {moment(ev.created_at).format("DD/MM HH:mm:ss")}
                </span>
              </div>

              {ev.requested_by?.name && (
                <p className="text-xs opacity-70 mt-0.5">
                  por {ev.requested_by.name}
                </p>
              )}

              {ev.previous_pairing_code && ev.new_pairing_code && (
                <p className="text-xs font-mono mt-1.5 opacity-80">
                  {ev.previous_pairing_code} → {ev.new_pairing_code}
                </p>
              )}

              {(ev.previous_token_version != null || ev.new_token_version != null) && (
                <p className="text-xs mt-1 opacity-70">
                  token v{ev.previous_token_version ?? "?"} → v{ev.new_token_version ?? "?"}
                </p>
              )}

              {ev.reason && (
                <p className="text-xs italic mt-1.5 opacity-90">"{ev.reason}"</p>
              )}

              {ev.metadata?.revoked_sessions_count > 0 && (
                <p className="text-xs mt-1 font-medium">
                  {ev.metadata.revoked_sessions_count} sessão(ões) revogada(s)
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

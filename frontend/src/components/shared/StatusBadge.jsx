import React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const statusConfig = {
  online: {
    label: "Online",
    className: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  offline: {
    label: "Offline",
    className: "bg-red-100 text-red-700 border-red-200",
  },
  syncing: {
    label: "Sincronizando",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
  error: { label: "Erro", className: "bg-red-100 text-red-700 border-red-200" },
  draft: {
    label: "Rascunho",
    className: "bg-slate-100 text-slate-700 border-slate-200",
  },
  scheduled: {
    label: "Agendada",
    className: "bg-blue-100 text-blue-700 border-blue-200",
  },
  active: {
    label: "Ativa",
    className: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  paused: {
    label: "Pausada",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
  ended: {
    label: "Encerrada",
    className: "bg-slate-100 text-slate-700 border-slate-200",
  },
  available: {
    label: "Disponível",
    className: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  processing: {
    label: "Processando",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
  success: {
    label: "Sucesso",
    className: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  partial: {
    label: "Parcial",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
};

export default function StatusBadge({ status }) {
  const config = statusConfig[status] || {
    label: status,
    className: "bg-slate-100 text-slate-700",
  };
  return (
    <Badge
      variant="outline"
      className={cn("font-medium text-xs border", config.className)}
    >
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full mr-1.5 inline-block",
          status === "online" ||
            status === "active" ||
            status === "available" ||
            status === "success"
            ? "bg-emerald-500"
            : status === "offline" || status === "error"
              ? "bg-red-500"
              : status === "syncing" ||
                  status === "paused" ||
                  status === "processing" ||
                  status === "partial"
                ? "bg-amber-500"
                : status === "scheduled"
                  ? "bg-blue-500"
                  : "bg-slate-400",
        )}
      />
      {config.label}
    </Badge>
  );
}

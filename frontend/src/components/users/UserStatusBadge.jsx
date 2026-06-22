import React from "react";
import { Badge } from "@/components/ui/badge";

const config = {
  active: {
    label: "Ativo",
    className: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
  inactive: {
    label: "Inativo",
    className: "bg-slate-100 text-slate-600 border-slate-200",
  },
  blocked: {
    label: "Bloqueado (inadimpl.)",
    className: "bg-red-100 text-red-700 border-red-200",
  },
  pending_invite: {
    label: "Convite pendente",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
};

const dot = {
  active: "bg-emerald-500",
  inactive: "bg-slate-400",
  blocked: "bg-red-500",
  pending_invite: "bg-amber-500",
};

export default function UserStatusBadge({ status }) {
  const s = config[status] || config.inactive;
  return (
    <Badge
      variant="outline"
      className={`text-xs font-medium border ${s.className}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full mr-1.5 inline-block ${dot[status] || "bg-slate-400"}`}
      />
      {s.label}
    </Badge>
  );
}

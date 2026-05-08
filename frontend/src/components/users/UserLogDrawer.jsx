import React from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useQuery } from "@tanstack/react-query";
import { listarLogsPorUsuario } from "@/api/userLogs";
import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  ClipboardList,
  UserCheck,
  UserX,
  ShieldOff,
  Shield,
  KeyRound,
  Send,
  Pencil,
} from "lucide-react";

const ACTION_CONFIG = {
  invite: {
    label: "Convite enviado",
    icon: Send,
    color: "text-blue-500 bg-blue-50",
  },
  edit: {
    label: "Dados editados",
    icon: Pencil,
    color: "text-amber-500 bg-amber-50",
  },
  activate: {
    label: "Ativado",
    icon: UserCheck,
    color: "text-emerald-500 bg-emerald-50",
  },
  deactivate: {
    label: "Desativado",
    icon: UserX,
    color: "text-slate-500 bg-slate-100",
  },
  block: {
    label: "Bloqueado",
    icon: ShieldOff,
    color: "text-red-500 bg-red-50",
  },
  unblock: {
    label: "Desbloqueado",
    icon: Shield,
    color: "text-emerald-500 bg-emerald-50",
  },
  reset_password: {
    label: "Senha redefinida",
    icon: KeyRound,
    color: "text-violet-500 bg-violet-50",
  },
};

export default function UserLogDrawer({ userId, userName, open, onClose }) {
  const { data: logs = [] } = useQuery({
    queryKey: ["user-logs", userId],
    queryFn: () => listarLogsPorUsuario(userId),
    enabled: open && !!userId,
  });

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-full sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <ClipboardList className="w-5 h-5" />
            Histórico — {userName}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6 space-y-3">
          {logs.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">
              Nenhuma ação registrada.
            </p>
          )}
          {logs.map((log) => {
            const cfg = ACTION_CONFIG[log.action] || {
              label: log.action,
              icon: ClipboardList,
              color: "text-slate-500 bg-slate-100",
            };
            const Icon = cfg.icon;
            return (
              <div key={log.id} className="flex gap-3">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${cfg.color}`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{cfg.label}</p>
                  {log.details && (
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {log.details}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">
                    por <span className="font-medium">{log.performed_by}</span>
                    {log.created_date &&
                      ` · ${format(new Date(log.created_date), "dd/MM/yy 'às' HH:mm", { locale: ptBR })}`}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </SheetContent>
    </Sheet>
  );
}

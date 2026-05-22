import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  Clock,
  Loader2,
  Send,
  ShieldOff,
  XCircle,
} from "lucide-react";
import moment from "moment";
import {
  commandLabel,
  statusBadgeFor,
} from "@/utils/deviceCommands";

/**
 * CommandHistoryTimeline — exibe histórico de comandos do dispositivo com
 * status colorido, timeline de transições e ação "Cancelar" quando aplicável.
 *
 * SPEC 003 — substitui a lista simples anterior por timeline detalhada.
 *
 * Props:
 *  - commands: Array<DeviceCommand>
 *  - onCancel?: (commandId) => Promise<void>
 *  - cancellingId?: string | null
 */
export default function CommandHistoryTimeline({ commands = [], onCancel, cancellingId = null }) {
  if (!commands || commands.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-muted-foreground">
        Nenhum comando enviado ainda.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {commands.map((cmd) => (
        <CommandRow
          key={cmd.id}
          cmd={cmd}
          onCancel={onCancel}
          cancelling={cancellingId === cmd.id}
        />
      ))}
    </div>
  );
}

function CommandRow({ cmd, onCancel, cancelling }) {
  const badge = statusBadgeFor(cmd);
  const canCancel = onCancel && (cmd.status === "pending" || cmd.status === "sent");
  const errorCode = cmd?.result?.error_code;
  const platform = cmd?.result?.platform;

  return (
    <div className="border rounded-lg p-3 bg-card">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm">{commandLabel(cmd.command_type)}</span>
            {cmd.is_destructive && (
              <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                <AlertTriangle className="w-3 h-3 mr-1" />
                Destrutivo
              </Badge>
            )}
            <Badge variant="outline" className={`text-xs ${badge.className}`}>
              {badge.label}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Por: {cmd.requested_by || "—"} · {moment(cmd.requested_at).format("DD/MM HH:mm:ss")}
          </p>
        </div>

        {canCancel && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onCancel(cmd.id)}
            disabled={cancelling}
            className="text-xs"
          >
            {cancelling ? <Loader2 className="w-3 h-3 animate-spin" /> : <Ban className="w-3 h-3 mr-1" />}
            {cancelling ? "Cancelando..." : "Cancelar"}
          </Button>
        )}
      </div>

      <TimelineSteps cmd={cmd} />

      {cmd.error_message && (
        <div className="mt-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded px-2 py-1.5 flex items-start gap-1.5">
          <XCircle className="w-3 h-3 mt-0.5 shrink-0" />
          <div className="flex-1 break-words">
            {errorCode && <span className="font-mono font-semibold mr-1">[{errorCode}]</span>}
            {cmd.error_message}
          </div>
        </div>
      )}

      {(platform || cmd?.result?.ack_phase) && (
        <details className="mt-2 text-xs text-muted-foreground">
          <summary className="cursor-pointer hover:text-foreground">Detalhes técnicos</summary>
          <pre className="mt-1 p-2 bg-muted rounded overflow-x-auto text-[10px]">
            {JSON.stringify(cmd.result, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

function TimelineSteps({ cmd }) {
  const steps = [
    { key: "sent_at",     label: "Enviado",   icon: Send },
    { key: "received_at", label: "Recebido",  icon: CheckCircle2 },
    { key: "started_at",  label: "Iniciado",  icon: Loader2 },
    { key: "executed_at", label: cmd.status === "failed" ? "Falhou" : "Concluído", icon: CheckCircle2 },
  ];

  const requestedAt = moment(cmd.requested_at);
  const visibleSteps = steps.filter((s) => cmd[s.key]);

  if (visibleSteps.length === 0 && cmd.status === "pending") {
    return (
      <div className="mt-2 text-xs text-muted-foreground flex items-center gap-1">
        <Clock className="w-3 h-3" />
        Aguardando envio ao player…
        {cmd.expires_at && (
          <span className="ml-1">· expira {moment(cmd.expires_at).fromNow()}</span>
        )}
      </div>
    );
  }

  return (
    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
      {visibleSteps.map((step) => {
        const t = moment(cmd[step.key]);
        const delta = t.diff(requestedAt, "seconds");
        return (
          <span key={step.key} className="inline-flex items-center gap-1">
            <step.icon className="w-3 h-3" />
            <span>{step.label}: {t.format("HH:mm:ss")}</span>
            <span className="text-[10px] opacity-60">(+{delta}s)</span>
          </span>
        );
      })}
      {cmd.expires_at && cmd.status !== "completed" && cmd.status !== "executed" && cmd.status !== "failed" && (
        <span className="inline-flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Expira {moment(cmd.expires_at).fromNow()}
        </span>
      )}
    </div>
  );
}

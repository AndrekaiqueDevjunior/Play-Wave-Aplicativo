import React, { useEffect, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, RefreshCw } from "lucide-react";
import { buscarSessoesAtivas } from "@/api/dispositivos";

/**
 * RegenerateCodeDialog — confirmação para gerar novo pairing_code (SPEC 004).
 *
 * Mostra quantas sessões ativas serão revogadas e permite anexar `reason`
 * para a trilha de auditoria em device_pairing_events.
 */
export default function RegenerateCodeDialog({
  open,
  onOpenChange,
  deviceId,
  deviceName,
  currentCode,
  onConfirm,
  loading = false,
}) {
  const [reason, setReason] = useState("");
  const [activeSessions, setActiveSessions] = useState(null);
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (!open || !deviceId) return;
    setFetching(true);
    buscarSessoesAtivas(deviceId)
      .then((s) => setActiveSessions(s || []))
      .catch(() => setActiveSessions(null))
      .finally(() => setFetching(false));
  }, [open, deviceId]);

  // Reset reason quando dialog fecha
  useEffect(() => {
    if (!open) setReason("");
  }, [open]);

  const sessionCount = Array.isArray(activeSessions) ? activeSessions.length : null;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-amber-500" />
            Regenerar código de pareamento
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3 text-sm">
              <p>
                Esta ação vai:
              </p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Gerar um <strong>novo código</strong> de pareamento (o atual <code className="font-mono">{currentCode || "—"}</code> deixa de funcionar).</li>
                <li>Revogar <strong>todos os players</strong> atualmente conectados a este dispositivo.</li>
                <li>Forçar reparamento manual em cada TV.</li>
              </ul>

              <div className="bg-amber-50 border border-amber-200 rounded px-3 py-2 text-amber-900">
                {fetching ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Verificando sessões ativas…
                  </span>
                ) : sessionCount == null ? (
                  <span className="text-amber-700">
                    Não foi possível verificar sessões ativas — prossiga com cautela.
                  </span>
                ) : sessionCount === 0 ? (
                  <span>Nenhum player conectado no momento.</span>
                ) : (
                  <span>
                    <strong>{sessionCount}</strong> sessão(ões) ativa(s) serão desconectadas.
                  </span>
                )}
              </div>

              <div>
                <label className="text-xs font-medium block mb-1">Motivo (opcional, para auditoria)</label>
                <Textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={2}
                  maxLength={500}
                  placeholder="Ex: TV trocada de loja, suspeita de cracha clonado…"
                  disabled={loading}
                />
              </div>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={loading}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => onConfirm(reason.trim() || null)}
            disabled={loading}
            className="bg-amber-600 hover:bg-amber-700 focus:ring-amber-600"
          >
            {loading ? "Regenerando…" : "Sim, regenerar e revogar"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

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
import { ShieldOff } from "lucide-react";

/**
 * ForceRepairDialog — confirmação para revogar tokens sem trocar o
 * pairing_code (SPEC 004).
 *
 * Use quando suspeitar de player clonado/roubado mas quiser manter o
 * código atual nas TVs autorizadas (que pareiam novamente com o mesmo).
 */
export default function ForceRepairDialog({
  open,
  onOpenChange,
  deviceName,
  currentCode,
  onConfirm,
  loading = false,
}) {
  const [reason, setReason] = useState("");

  useEffect(() => {
    if (!open) setReason("");
  }, [open]);

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <ShieldOff className="w-5 h-5 text-orange-500" />
            Forçar reparamento (manter código)
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3 text-sm">
              <p>Esta ação vai:</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>Revogar <strong>todos os players</strong> atualmente conectados a {deviceName}.</li>
                <li>
                  Manter o código de pareamento atual: <code className="font-mono">{currentCode || "—"}</code>
                </li>
                <li>Operadores podem reparear com o <strong>mesmo código</strong>.</li>
              </ul>

              <div className="bg-orange-50 border border-orange-200 rounded px-3 py-2 text-orange-900 text-xs">
                Use quando suspeitar de player clonado ou roubado, sem
                querer reconfigurar todas as TVs autorizadas. A ação fica
                registrada na trilha de auditoria do dispositivo.
              </div>

              <div>
                <label className="text-xs font-medium block mb-1">Motivo (recomendado)</label>
                <Textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={2}
                  maxLength={500}
                  placeholder="Ex: player suspeito, sem identificação, IP de origem inesperado…"
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
            className="bg-orange-600 hover:bg-orange-700 focus:ring-orange-600"
          >
            {loading ? "Revogando…" : "Sim, forçar reparamento"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

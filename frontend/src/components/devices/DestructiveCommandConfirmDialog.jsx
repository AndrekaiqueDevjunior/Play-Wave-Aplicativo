import React from "react";
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
import { AlertTriangle } from "lucide-react";
import { commandLabel } from "@/utils/deviceCommands";

/**
 * DestructiveCommandConfirmDialog — confirmação forte para comandos que
 * reiniciam ou desligam o dispositivo físico.
 *
 * SPEC 003 — força o operador a confirmar a operação e exibe a plataforma
 * detectada do dispositivo + nível de suporte conhecido.
 *
 * Props:
 *  - open: boolean
 *  - onOpenChange: (open) => void
 *  - commandType: string ("restart_device" | "shutdown_device" | "restart_app" | ...)
 *  - deviceName: string
 *  - devicePlatform?: string (ex: "android", "electron-linux", "web")
 *  - onConfirm: () => Promise<void> | void
 *  - loading?: boolean
 */
export default function DestructiveCommandConfirmDialog({
  open,
  onOpenChange,
  commandType,
  deviceName,
  devicePlatform = null,
  onConfirm,
  loading = false,
}) {
  const label = commandLabel(commandType);
  const isShutdown = commandType === "shutdown_device";
  const isReboot = commandType === "restart_device";

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Atenção — operação física no dispositivo
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3 text-sm">
              <p>
                Você está prestes a <strong>{label.toLowerCase()}</strong> o dispositivo
                {" "}<strong>{deviceName}</strong>.
              </p>

              {isShutdown && (
                <p className="text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                  Esta operação desliga fisicamente o dispositivo. Alguém precisará
                  estar perto dele para ligá-lo novamente.
                </p>
              )}

              {isReboot && (
                <p className="text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
                  O dispositivo ficará offline durante a reinicialização
                  (~1-2 minutos).
                </p>
              )}

              <PlatformSupport command={commandType} platform={devicePlatform} />
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={loading}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={loading}
            className="bg-red-600 hover:bg-red-700 focus:ring-red-600"
          >
            {loading ? "Enviando..." : `Confirmar ${label}`}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

function PlatformSupport({ command, platform }) {
  if (!platform) {
    return (
      <p className="text-xs text-muted-foreground">
        Plataforma do dispositivo desconhecida — o player retornará "não suportado"
        se não conseguir executar.
      </p>
    );
  }

  const support = resolveSupport(command, platform);

  return (
    <p className="text-xs text-muted-foreground">
      <strong>Plataforma:</strong> {platform} · <strong>Suporte:</strong> {support}
    </p>
  );
}

function resolveSupport(command, platform) {
  const p = (platform || "").toLowerCase();
  if (p.includes("web") && !p.includes("electron") && !p.includes("capacitor")) {
    return "Não suportado em navegador puro";
  }
  if (p.includes("electron")) {
    if (command === "restart_device" || command === "shutdown_device") {
      return "Suportado (requer sudo/Admin no SO)";
    }
    return "Suportado";
  }
  if (p.includes("capacitor") || p.includes("android")) {
    if (command === "restart_device" || command === "shutdown_device") {
      return "Suportado se provisionado como Device Owner";
    }
    return "Suportado";
  }
  return "Verificar logs do player";
}

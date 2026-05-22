import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  RefreshCw,
  Download,
  Trash2,
  Power,
  Monitor,
  HardDrive,
  Cpu,
  Globe,
  Clock,
  Wifi,
  WifiOff,
  AlertTriangle,
  KeyRound,
  RotateCcw,
} from "lucide-react";
import StatusBadge from "@/components/shared/StatusBadge";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  buscarDispositivo,
  atualizarDispositivo,
  listarComandosDispositivo,
  regenerarCodigoPareamento,
  cancelarComando,
} from "@/api/dispositivos";
import {
  sendDeviceCommand,
  getDeviceMetrics,
  isApiConfigured,
} from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";
import moment from "moment";
import {
  COMMANDS_BY_GROUP,
  commandLabel,
  isDestructive,
} from "@/utils/deviceCommands";
import CommandHistoryTimeline from "@/components/devices/CommandHistoryTimeline";
import DestructiveCommandConfirmDialog from "@/components/devices/DestructiveCommandConfirmDialog";

export default function DispositivoDetalhe() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [commandLoading, setCommandLoading] = useState(null);
  const [pairingLoading, setPairingLoading] = useState(false);
  const [syncLog, setSyncLog] = useState([]);
  const [pendingDestructive, setPendingDestructive] = useState(null); // { command, label }
  const [cancellingId, setCancellingId] = useState(null);

  const { data: device, isLoading } = useQuery({
    queryKey: ["device", id],
    queryFn: () => buscarDispositivo(id),
    enabled: !!id,
  });

  const { data: metrics } = useQuery({
    queryKey: ["device-metrics", id],
    queryFn: () => getDeviceMetrics(id),
    enabled: isApiConfigured() && !!id,
    refetchInterval: 30_000,
  });

  const { data: commandHistory, refetch: refetchCommands } = useQuery({
    queryKey: ["device-commands", id],
    queryFn: () => listarComandosDispositivo(id, { limit: 30 }),
    enabled: isApiConfigured() && !!id,
    // SPEC 003 — 5s para feedback rápido durante operações destrutivas.
    refetchInterval: 5_000,
  });

  const updateMutation = useMutation({
    mutationFn: (data) => atualizarDispositivo(id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["device", id] }),
  });

  const handleCommand = async (command, label) => {
    // SPEC 003 — comandos destrutivos passam por modal de confirmação.
    if (isDestructive(command)) {
      setPendingDestructive({ command, label });
      return;
    }
    await sendCommand(command, label);
  };

  const sendCommand = async (command, label) => {
    setCommandLoading(command);
    let result = null;
    if (isApiConfigured()) {
      try {
        result = await sendDeviceCommand(id, command);
      } catch (err) {
        toast({
          title: `Falha ao enviar "${label}"`,
          description: err?.message || "Erro desconhecido.",
          variant: "destructive",
        });
        setCommandLoading(null);
        return;
      }
    }
    const entry = {
      date: moment().format("DD/MM HH:mm"),
      status: "success",
      message: `Comando "${label}" enviado${result?.queued_at ? " — aguardando TV" : ""}`,
    };
    setSyncLog((prev) => [entry, ...prev]);
    if (command === "sync" || command === "refresh_playlist") {
      await updateMutation.mutateAsync({ status: "syncing" });
    }
    if (isApiConfigured()) {
      queryClient.invalidateQueries({ queryKey: ["device-commands", id] });
    }
    toast({
      title: label,
      description: isApiConfigured()
        ? "Comando enviado ao dispositivo."
        : "Registrado (backend não configurado).",
    });
    setCommandLoading(null);
  };

  const confirmDestructive = async () => {
    if (!pendingDestructive) return;
    const { command, label } = pendingDestructive;
    await sendCommand(command, label);
    setPendingDestructive(null);
  };

  const handleCancelCommand = async (commandId) => {
    setCancellingId(commandId);
    try {
      await cancelarComando(id, commandId);
      toast({ title: "Comando cancelado", description: "O comando foi cancelado antes da execução." });
      queryClient.invalidateQueries({ queryKey: ["device-commands", id] });
    } catch (err) {
      toast({
        title: "Falha ao cancelar",
        description: err?.message || "Comando pode já ter sido executado.",
        variant: "destructive",
      });
    } finally {
      setCancellingId(null);
    }
  };

  const handleToggleActive = async () => {
    if (!device) return;
    await updateMutation.mutateAsync({ is_active: !device.is_active });
    toast({
      title: device.is_active
        ? "Dispositivo desativado"
        : "Dispositivo ativado",
    });
  };

  const handleRegeneratePairing = async () => {
    if (!device) return;
    const confirmed = window.confirm(
      "Regenerar o código de pareamento vai derrubar o player atual e exigir novo pareamento nesta TV. Continuar?",
    );
    if (!confirmed) return;
    setPairingLoading(true);
    try {
      const updated = await regenerarCodigoPareamento(id);
      queryClient.invalidateQueries({ queryKey: ["device", id] });
      toast({
        title: "Código regenerado",
        description: `Novo código: ${updated?.pairing_code || "gerado"}. O player antigo precisará parear novamente.`,
      });
    } catch (error) {
      toast({
        title: "Erro ao regenerar código",
        description: error?.message || "Não foi possível regenerar o pareamento.",
        variant: "destructive",
      });
    } finally {
      setPairingLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!device) {
    return (
      <div className="text-center py-20">
        <p className="text-muted-foreground">Dispositivo não encontrado.</p>
        <Button className="mt-4" onClick={() => navigate("/dispositivos")}>
          Voltar
        </Button>
      </div>
    );
  }

  const infoItems = [
    { label: "Status", value: <StatusBadge status={device.status} /> },
    {
      label: "Última Conexão",
      value: device.last_connection
        ? moment(device.last_connection).format("DD/MM/YYYY HH:mm")
        : "—",
      icon: Clock,
    },
    { label: "IP", value: device.ip_address || "—", icon: Globe },
    { label: "Versão do Player", value: device.player_version || "—" },
    { label: "Sistema Operacional", value: device.os || "—", icon: Cpu },
    {
      label: "Armazenamento Usado",
      value: device.storage_used
        ? `${(device.storage_used / 1024).toFixed(1)} GB`
        : "—",
      icon: HardDrive,
    },
    { label: "Campanha Atual", value: device.current_campaign || "Nenhuma" },
    {
      label: "Código de Pareamento",
      value: (
        <span className="font-mono font-bold tracking-wider">
          {device.pairing_code}
        </span>
      ),
    },
    { label: "Localização", value: device.location || "—" },
    { label: "Grupo", value: device.group || "—" },
  ];

  // SPEC 003 — Ícones por command_type.
  const COMMAND_ICONS = {
    sync: RefreshCw,
    refresh_playlist: Download,
    clear_cache: Trash2,
    reload_player: RotateCcw,
    restart_app: Monitor,
    restart_device: Power,
    shutdown_device: Power,
  };

  const devicePlatform = device?.player_version
    ? `${device.os || "?"} (player ${device.player_version})`
    : device?.os || null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/dispositivos")}
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="text-xl font-bold">{device.name}</h2>
            <StatusBadge status={device.status} />
            {!device.is_active && (
              <Badge
                variant="outline"
                className="text-destructive border-destructive/30"
              >
                Inativo
              </Badge>
            )}
            {isApiConfigured() ? (
              <Badge
                variant="outline"
                className="bg-emerald-50 text-emerald-700 border-emerald-200 text-xs"
              >
                <Wifi className="w-3 h-3 mr-1" />
                Backend conectado
              </Badge>
            ) : (
              <Badge
                variant="outline"
                className="bg-amber-50 text-amber-700 border-amber-200 text-xs"
              >
                <WifiOff className="w-3 h-3 mr-1" />
                Sem FastAPI
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {device.location} · {device.group}
          </p>
        </div>
      </div>

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Views hoje", value: metrics.views_today ?? "—" },
            {
              label: "Uptime",
              value: metrics.uptime_seconds
                ? `${Math.floor(metrics.uptime_seconds / 3600)}h`
                : "—",
            },
            {
              label: "Última atividade",
              value: metrics.last_seen
                ? moment(metrics.last_seen).fromNow()
                : "—",
            },
            { label: "Mídia atual", value: metrics.current_media || "—" },
          ].map((m, i) => (
            <div key={i} className="rounded-xl border bg-card p-3">
              <p className="text-xs text-muted-foreground">{m.label}</p>
              <p className="text-sm font-semibold mt-0.5 truncate">{m.value}</p>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-3">
        <CommandGroup
          title="Operacional"
          subtitle="Recarrega dados sem interromper o player."
          commands={COMMANDS_BY_GROUP.operational}
          icons={COMMAND_ICONS}
          commandLoading={commandLoading}
          onCommand={handleCommand}
        />
        <CommandGroup
          title="Reset do app"
          subtitle="Reinicia o app do player."
          commands={COMMANDS_BY_GROUP.reset}
          icons={COMMAND_ICONS}
          commandLoading={commandLoading}
          onCommand={handleCommand}
          variant="warn"
        />
        <CommandGroup
          title="Energia (físico)"
          subtitle="Operações no SO. Requer permissão adequada por plataforma."
          commands={COMMANDS_BY_GROUP.power}
          icons={COMMAND_ICONS}
          commandLoading={commandLoading}
          onCommand={handleCommand}
          variant="destructive"
        />

        <div className="flex flex-wrap gap-2 pt-1 border-t border-border">
          <Button
            variant="outline"
            size="sm"
            disabled={pairingLoading}
            onClick={handleRegeneratePairing}
          >
            <KeyRound className={cn("w-4 h-4 mr-2", pairingLoading && "animate-spin")} />
            {pairingLoading ? "Regenerando..." : "Regenerar Pareamento"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className={
              device.is_active
                ? "text-destructive border-destructive/30"
                : "text-emerald-600 border-emerald-300"
            }
            onClick={handleToggleActive}
          >
            <Power className="w-4 h-4 mr-2" />
            {device.is_active ? "Desativar" : "Ativar"}
          </Button>
        </div>
      </div>

      <DestructiveCommandConfirmDialog
        open={!!pendingDestructive}
        onOpenChange={(open) => !open && setPendingDestructive(null)}
        commandType={pendingDestructive?.command}
        deviceName={device.name}
        devicePlatform={devicePlatform}
        onConfirm={confirmDestructive}
        loading={commandLoading === pendingDestructive?.command}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Informações do Dispositivo
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-0">
            {infoItems.map((item, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2.5 border-b border-border last:border-0"
              >
                <span className="text-sm text-muted-foreground">
                  {item.label}
                </span>
                <span className="text-sm font-medium">{item.value}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Histórico de Comandos</CardTitle>
              {isApiConfigured() ? (
                <Badge
                  variant="outline"
                  className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200"
                >
                  Tempo real (5s)
                </Badge>
              ) : (
                <Badge variant="outline" className="text-xs">
                  Sem backend
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <CommandHistoryTimeline
              commands={commandHistory || []}
              onCancel={isApiConfigured() ? handleCancelCommand : undefined}
              cancellingId={cancellingId}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/**
 * Bloco de botões agrupados por categoria — Operacional / Reset / Energia.
 */
function CommandGroup({ title, subtitle, commands, icons, commandLoading, onCommand, variant }) {
  const groupClass = {
    destructive: "border-red-200 bg-red-50/30",
    warn: "border-amber-200 bg-amber-50/30",
  }[variant] || "border-border";

  const buttonClass = {
    destructive: "text-red-700 border-red-300 hover:bg-red-50",
    warn: "text-amber-800 border-amber-300 hover:bg-amber-50",
  }[variant] || "";

  return (
    <div className={`border rounded-lg p-3 ${groupClass}`}>
      <div className="mb-2">
        <h4 className="text-sm font-semibold">{title}</h4>
        {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap gap-2">
        {commands.map(({ command, label, tooltip }) => {
          const Icon = icons[command] || RefreshCw;
          return (
            <Button
              key={command}
              variant="outline"
              size="sm"
              disabled={commandLoading === command}
              onClick={() => onCommand(command, label)}
              title={tooltip}
              className={buttonClass}
            >
              <Icon
                className={cn(
                  "w-4 h-4 mr-2",
                  commandLoading === command && "animate-spin",
                )}
              />
              {commandLoading === command ? "Enviando..." : label}
            </Button>
          );
        })}
      </div>
    </div>
  );
}

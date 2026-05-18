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
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import StatusBadge from "@/components/shared/StatusBadge";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { buscarDispositivo, atualizarDispositivo, listarComandosDispositivo } from "@/api/dispositivos";
import {
  sendDeviceCommand,
  getDeviceMetrics,
  isApiConfigured,
} from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";
import moment from "moment";

export default function DispositivoDetalhe() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [commandLoading, setCommandLoading] = useState(null);
  const [syncLog, setSyncLog] = useState([]);

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
    refetchInterval: 15_000,
  });

  const updateMutation = useMutation({
    mutationFn: (data) => atualizarDispositivo(id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["device", id] }),
  });

  const handleCommand = async (command, label) => {
    setCommandLoading(command);
    let result = null;
    if (isApiConfigured()) {
      result = await sendDeviceCommand(id, command);
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

  const handleToggleActive = async () => {
    if (!device) return;
    await updateMutation.mutateAsync({ is_active: !device.is_active });
    toast({
      title: device.is_active
        ? "Dispositivo desativado"
        : "Dispositivo ativado",
    });
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

  const commands = [
    { command: "sync", label: "Sincronizar", icon: RefreshCw },
    { command: "refresh_playlist", label: "Atualizar Playlist", icon: Download },
    { command: "clear_cache", label: "Limpar Cache", icon: Trash2 },
    { command: "restart", label: "Reiniciar Player", icon: Monitor },
  ];

  const statusLabel = { pending: "Pendente", sent: "Enviado", executed: "Executado", failed: "Falhou", cancelled: "Cancelado" };
  const statusIcon = { executed: "success", failed: "error", pending: "info", sent: "info", cancelled: "info" };

  const apiLogs = (commandHistory || []).map((c) => ({
    date: moment(c.requested_at).format("DD/MM HH:mm"),
    status: statusIcon[c.status] || "info",
    message: `${c.command_type} — ${statusLabel[c.status] || c.status}${c.error_message ? `: ${c.error_message}` : ""}`,
    origin: c.requested_by || "admin",
  }));

  const allLogs =
    apiLogs.length > 0
      ? apiLogs
      : [
          ...syncLog,
          {
            date: "—",
            status: "info",
            message: isApiConfigured()
              ? "Nenhum comando enviado ainda."
              : "Histórico de sessões anteriores indisponível sem backend.",
          },
        ];

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

      <div className="flex flex-wrap gap-2">
        {commands.map(({ command, label, icon: Icon }) => (
          <Button
            key={command}
            variant="outline"
            size="sm"
            disabled={commandLoading === command}
            onClick={() => handleCommand(command, label)}
          >
            <Icon
              className={cn(
                "w-4 h-4 mr-2",
                commandLoading === command && "animate-spin",
              )}
            />
            {commandLoading === command ? "Enviando..." : label}
          </Button>
        ))}
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
              <CardTitle className="text-base">Log de Comandos</CardTitle>
              {isApiConfigured() ? (
                <Badge
                  variant="outline"
                  className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200"
                >
                  FastAPI ativo
                </Badge>
              ) : (
                <Badge variant="outline" className="text-xs">
                  Sem backend
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-0">
              {allLogs.map((entry, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 py-2.5 border-b border-border last:border-0"
                >
                  {entry.status === "success" && (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
                  )}
                  {entry.status === "error" && (
                    <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                  )}
                  {entry.status === "info" && (
                    <div className="w-4 h-4 shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="text-sm">{entry.message}</p>
                    {entry.date !== "—" && (
                      <p className="text-xs text-muted-foreground">
                        {entry.date}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

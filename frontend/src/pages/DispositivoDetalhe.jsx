import React, { useEffect, useState, useCallback } from "react";
import { AudioPolicySelector } from "@/components/shared/AudioPolicySelector";
import { OSDConfigForm } from "@/components/shared/OSDConfigForm";
import {
  OSDConfigPreview,
  normalizeOSDConfig,
} from "@/components/shared/OSDConfigPreview";
import SpotSchedulePanel from "@/components/audio/SpotSchedulePanel";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
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
  KeyRound,
  RotateCcw,
  Save,
  Minimize2,
  Maximize2,
} from "lucide-react";
import StatusBadge from "@/components/shared/StatusBadge";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listarCampanhas } from "@/api/campanhas";
import {
  listarSpots,
  criarSpot,
  atualizarSpot,
  deletarSpot,
  listarSpotSchedules,
  criarSpotSchedule,
  atualizarSpotSchedule,
  deletarSpotSchedule,
} from "@/api/audio";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tv2, PlayCircle, Music2, CheckCircle2, ExternalLink } from "lucide-react";
import {
  buscarDispositivo,
  atualizarDispositivo,
  atualizarOSDConfigDispositivo,
  atualizarDesktopExposureConfigDispositivo,
  listarComandosDispositivo,
  regenerarCodigoPareamento,
  cancelarComando,
  forcarReparamento,
} from "@/api/dispositivos";
import {
  sendDeviceCommand,
  getDeviceMetrics,
  isApiConfigured,
} from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { cn } from "@/lib/utils";
import moment from "moment";
import { COMMANDS_BY_GROUP, isDestructive } from "@/utils/deviceCommands";
import CommandHistoryTimeline from "@/components/devices/CommandHistoryTimeline";
import DestructiveCommandConfirmDialog from "@/components/devices/DestructiveCommandConfirmDialog";
import RegenerateCodeDialog from "@/components/devices/RegenerateCodeDialog";
import ForceRepairDialog from "@/components/devices/ForceRepairDialog";
import PairingEventTimeline from "@/components/devices/PairingEventTimeline";

export default function DispositivoDetalhe() {
  console.log("[DispositivoDetalhe] Componente montado");

  const { id } = useParams();
  console.log("[DispositivoDetalhe] Device ID:", id);

  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [commandLoading, setCommandLoading] = useState(null);
  const [pairingLoading, setPairingLoading] = useState(false);
  const [syncLog, setSyncLog] = useState([]);
  const [pendingDestructive, setPendingDestructive] = useState(null); // { command, label }
  const [cancellingId, setCancellingId] = useState(null);
  const [desktopExposureConfig, setDesktopExposureConfig] = useState({
    enabled: false,
    interval_seconds: 10,
    duration_seconds: 10,
    restore_fullscreen: true,
    // SPEC 015 — aviso visual antes de minimizar (política WAIT_CONTENT_END).
    show_warning: false,
    warning_seconds_before: 15,
    warning_text: "",
  });
  const [desktopExposureTestLoading, setDesktopExposureTestLoading] =
    useState(false);
  // SPEC 004 — dialogs separados para regenerate vs force-repair.
  const [regenerateDialogOpen, setRegenerateDialogOpen] = useState(false);
  const [forceRepairDialogOpen, setForceRepairDialogOpen] = useState(false);
  const [forceRepairLoading, setForceRepairLoading] = useState(false);
  const [osdLocalConfig, setOsdLocalConfig] = useState({});
  const [campaignLinking, setCampaignLinking] = useState(false);
  const [campaignLinked, setCampaignLinked] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);

  const { data: campaignList = [] } = useQuery({
    queryKey: ["campaigns-list"],
    queryFn: () => listarCampanhas({ status: "active" }),
    enabled: isApiConfigured(),
  });

  const handleLinkCampaign = useCallback(async (campaignId) => {
    setCampaignLinking(true);
    setCampaignLinked(false);
    try {
      await atualizarDispositivo(id, { current_campaign_id: campaignId || null });
      queryClient.invalidateQueries({ queryKey: ["device", id] });
      if (campaignId) await sendDeviceCommand(id, "sync", {});
      setCampaignLinked(true);
      setTimeout(() => setCampaignLinked(false), 3000);
      toast({
        title: campaignId ? "✅ Campanha vinculada!" : "Campanha removida",
        description: campaignId
          ? "O player irá sincronizar a nova campanha em instantes."
          : "Dispositivo sem campanha ativa.",
      });
    } catch (err) {
      toast({ title: "Erro", description: err.message, variant: "destructive" });
    } finally {
      setCampaignLinking(false);
    }
  }, [id, queryClient, toast]);

  const {
    data: device,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["device", id],
    queryFn: () => buscarDispositivo(id),
    enabled: !!id,
    refetchInterval: 10_000,
  });

  const activeCampaignInfo = campaignList.find(
    (c) => c.id === (selectedCampaignId ?? device?.current_campaign_id)
  ) ?? null;

  useEffect(() => {
    if (!device?.osd_config_local) return;
    setOsdLocalConfig(device.osd_config_local);
  }, [device?.id, device?.osd_config_local]);

  useEffect(() => {
    if (!device?.desktop_exposure_config) return;
    setDesktopExposureConfig({
      enabled: device.desktop_exposure_config.enabled ?? false,
      interval_seconds: device.desktop_exposure_config.interval_seconds ?? 10,
      duration_seconds: device.desktop_exposure_config.duration_seconds ?? 10,
      restore_fullscreen:
        device.desktop_exposure_config.restore_fullscreen ?? true,
      show_warning: device.desktop_exposure_config.show_warning ?? false,
      warning_seconds_before:
        device.desktop_exposure_config.warning_seconds_before ?? 15,
      warning_text: device.desktop_exposure_config.warning_text ?? "",
    });
  }, [device?.id, device?.desktop_exposure_config]);

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

  // ── Dados de spots do device ───────────────────────────────────────────────
  const activeCampaign = campaignList.find(
    (c) => c.id === (device?.current_campaign_id)
  );
  const devicePlaylistId = activeCampaign?.audio_playlist_id || device?.audio_playlist_id || null;

  const { data: allSpots = [] } = useQuery({
    queryKey: ["audio-spots"],
    queryFn: () => listarSpots({ status: "active" }),
    enabled: isApiConfigured() && !!id,
  });

  const { data: deviceSpotSchedules = [], refetch: refetchSpotSchedules } = useQuery({
    queryKey: ["spot-schedules-device", id, devicePlaylistId],
    queryFn: () => devicePlaylistId
      ? listarSpotSchedules(devicePlaylistId).then((all) =>
          all.filter(
            (s) => s.device_id === id || (!s.device_id && !s.campaign_id)
          )
        )
      : Promise.resolve([]),
    enabled: isApiConfigured() && !!id,
  });

  const handleCreateDeviceSpot = async (payload) => {
    await criarSpot(payload);
    queryClient.invalidateQueries({ queryKey: ["audio-spots"] });
  };

  const handleUpdateDeviceSpot = async (spotId, payload) => {
    await atualizarSpot(spotId, payload);
    queryClient.invalidateQueries({ queryKey: ["audio-spots"] });
  };

  const handleDeleteDeviceSpot = async (spotId) => {
    await deletarSpot(spotId);
    queryClient.invalidateQueries({ queryKey: ["audio-spots"] });
  };

  const handleCreateDeviceSchedule = async (payload) => {
    if (!devicePlaylistId) {
      throw new Error("Vincule uma playlist ou campanha ao device para agendar spots");
    }
    await criarSpotSchedule(devicePlaylistId, { ...payload, device_id: id });
    refetchSpotSchedules();
  };

  const handleUpdateDeviceSchedule = async (scheduleId, payload) => {
    if (!devicePlaylistId) return;
    await atualizarSpotSchedule(devicePlaylistId, scheduleId, payload);
    refetchSpotSchedules();
  };

  const handleDeleteDeviceSchedule = async (scheduleId) => {
    if (!devicePlaylistId) return;
    await deletarSpotSchedule(devicePlaylistId, scheduleId);
    refetchSpotSchedules();
  };

  const updateMutation = useMutation({
    mutationFn: (data) => atualizarDispositivo(id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["device", id] }),
  });

  const osdMutation = useMutation({
    mutationFn: (payload) => atualizarOSDConfigDispositivo(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", id] });
      toast({ title: "Overlay OSD atualizado" });
    },
    onError: (err) => {
      toast({
        title: "Erro ao atualizar overlay",
        description: err.message || "Tente novamente.",
        variant: "destructive",
      });
    },
  });

  const desktopExposureMutation = useMutation({
    mutationFn: (payload) =>
      atualizarDesktopExposureConfigDispositivo(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["device", id] });
      toast({ title: "Configuração do player atualizada" });
    },
    onError: (err) => {
      toast({
        title: "Erro ao atualizar configuração do player",
        description: err.message || "Tente novamente.",
        variant: "destructive",
      });
    },
  });

  const handleTestDesktopExposure = async () => {
    if (!id) return;
    setDesktopExposureTestLoading(true);
    try {
      await sendDeviceCommand(id, "show_desktop", {
        payload: {
          duration_seconds: desktopExposureConfig.duration_seconds,
          restore_fullscreen: desktopExposureConfig.restore_fullscreen,
        },
      });
      toast({ title: "Comando de teste enviado" });
    } catch (err) {
      toast({
        title: "Erro ao testar a exposição do desktop",
        description: err?.message || "Tente novamente.",
        variant: "destructive",
      });
    } finally {
      setDesktopExposureTestLoading(false);
    }
  };

  const handleCommand = async (command, label, opts = {}) => {
    // SPEC 003 — comandos destrutivos passam por modal de confirmação.
    if (isDestructive(command)) {
      setPendingDestructive({ command, label });
      return;
    }
    await sendCommand(command, label, opts);
  };

  const sendCommand = async (command, label, opts = {}) => {
    setCommandLoading(command);
    let result = null;
    if (isApiConfigured()) {
      try {
        result = await sendDeviceCommand(id, command, opts);
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
      toast({
        title: "Comando cancelado",
        description: "O comando foi cancelado antes da execução.",
      });
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

  // SPEC 004 — agora passa por modal RegenerateCodeDialog.
  const handleConfirmRegenerate = async (reason) => {
    if (!device) return;
    setPairingLoading(true);
    try {
      const updated = await regenerarCodigoPareamento(id, reason);
      queryClient.invalidateQueries({ queryKey: ["device", id] });
      queryClient.invalidateQueries({
        queryKey: ["device-pairing-events", id],
      });
      const revoked = updated?.revoked_sessions_count ?? 0;
      toast({
        title: "Código regenerado",
        description:
          `Novo código: ${updated?.pairing_code || "gerado"}. ` +
          `${revoked} sessão(ões) revogada(s).`,
      });
      setRegenerateDialogOpen(false);
    } catch (error) {
      toast({
        title: "Erro ao regenerar código",
        description:
          error?.message || "Não foi possível regenerar o pareamento.",
        variant: "destructive",
      });
    } finally {
      setPairingLoading(false);
    }
  };

  // SPEC 004 — força repareamento sem trocar o código.
  const handleConfirmForceRepair = async (reason) => {
    if (!device) return;
    setForceRepairLoading(true);
    try {
      const result = await forcarReparamento(id, reason);
      queryClient.invalidateQueries({ queryKey: ["device", id] });
      queryClient.invalidateQueries({
        queryKey: ["device-pairing-events", id],
      });
      const revoked = result?.revoked_sessions_count ?? 0;
      toast({
        title: "Reparamento forçado",
        description:
          `${revoked} sessão(ões) revogada(s). ` +
          `O código permanece: ${result?.pairing_code_unchanged || device.pairing_code}.`,
      });
      setForceRepairDialogOpen(false);
    } catch (error) {
      toast({
        title: "Erro ao forçar reparamento",
        description: error?.message || "Não foi possível forçar o reparamento.",
        variant: "destructive",
      });
    } finally {
      setForceRepairLoading(false);
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
      label: "Tocando agora",
      value: device.current_audio_track_name
        ? `${device.current_audio_track_name}${
            device.current_audio_track_started_at
              ? ` (${moment(device.current_audio_track_started_at).fromNow()})`
              : ""
          }`
        : "—",
    },
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
    minimize_player: Minimize2,
    restore_player: Maximize2,
    show_desktop: Monitor,
    restart_app: Monitor,
    restart_device: Power,
    shutdown_device: Power,
  };

  const devicePlatform = device?.player_version
    ? `${device.os || "?"} (player ${device.player_version})`
    : device?.os || null;
  const osdEffectiveConfig = normalizeOSDConfig(
    device?.osd_config_effective || {},
  );
  const osdPreviewConfig = normalizeOSDConfig({
    ...osdEffectiveConfig,
    ...Object.fromEntries(
      Object.entries(osdLocalConfig || {}).filter(
        ([, value]) => value !== null && value !== undefined,
      ),
    ),
  });

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
          title="Janela do player"
          subtitle="Minimiza/restaura o Player Electron. Browser e Smart TV retornam nao suportado."
          commands={COMMANDS_BY_GROUP.window}
          icons={COMMAND_ICONS}
          commandLoading={commandLoading}
          onCommand={handleCommand}
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
            onClick={() => setRegenerateDialogOpen(true)}
            title="Gera novo código de pareamento e expulsa todos os players atuais."
          >
            <KeyRound
              className={cn("w-4 h-4 mr-2", pairingLoading && "animate-spin")}
            />
            {pairingLoading ? "Regenerando..." : "Regenerar Pareamento"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={forceRepairLoading}
            onClick={() => setForceRepairDialogOpen(true)}
            title="Expulsa players atuais MANTENDO o código de pareamento."
            className="text-orange-700 border-orange-300 hover:bg-orange-50"
          >
            <KeyRound
              className={cn(
                "w-4 h-4 mr-2",
                forceRepairLoading && "animate-spin",
              )}
            />
            {forceRepairLoading ? "Forçando..." : "Forçar Reparamento"}
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

      <RegenerateCodeDialog
        open={regenerateDialogOpen}
        onOpenChange={setRegenerateDialogOpen}
        deviceId={id}
        deviceName={device.name}
        currentCode={device.pairing_code}
        onConfirm={handleConfirmRegenerate}
        loading={pairingLoading}
      />

      <ForceRepairDialog
        open={forceRepairDialogOpen}
        onOpenChange={setForceRepairDialogOpen}
        deviceName={device.name}
        currentCode={device.pairing_code}
        onConfirm={handleConfirmForceRepair}
        loading={forceRepairLoading}
      />

      {/* ── Campanha Ativa ─────────────────────────────────────────────── */}
      <Card className={cn(campaignLinked && "ring-2 ring-emerald-400 transition-all")}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Tv2 className="w-4 h-4 text-primary" />
              <CardTitle className="text-base">Campanha Ativa</CardTitle>
            </div>
            {campaignLinked && (
              <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium animate-in fade-in">
                <CheckCircle2 className="w-3.5 h-3.5" /> Sincronizando...
              </span>
            )}
            {device.current_campaign && !campaignLinked && (
              <Badge className="bg-emerald-100 text-emerald-700 border-emerald-200 text-xs">
                <PlayCircle className="w-3 h-3 mr-1" /> Reproduzindo
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Info da campanha atual */}
          {device.current_campaign && (
            <div className="rounded-lg border bg-muted/30 p-3 flex items-start justify-between gap-3">
              <div className="space-y-1">
                <p className="text-sm font-semibold">{device.current_campaign}</p>
                {activeCampaignInfo?.audio_playlist_id && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <Music2 className="w-3 h-3" />
                    Rádio indoor configurado
                  </p>
                )}
                {activeCampaignInfo && (
                  <p className="text-xs text-muted-foreground">
                    {activeCampaignInfo.total_items ?? activeCampaignInfo.media_ids?.length ?? "—"} mídia(s)
                    {activeCampaignInfo.priority > 1 && ` · Prioridade ${activeCampaignInfo.priority}`}
                  </p>
                )}
              </div>
              <Button variant="ghost" size="sm" className="shrink-0 h-7 text-xs" asChild>
                <a href={`/campanhas`}><ExternalLink className="w-3 h-3 mr-1" />Ver</a>
              </Button>
            </div>
          )}

          {/* Trocar campanha */}
          <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center">
            <Select
              value={selectedCampaignId ?? device.current_campaign_id ?? "none"}
              onValueChange={(v) => setSelectedCampaignId(v === "none" ? "" : v)}
            >
              <SelectTrigger className="flex-1 sm:max-w-xs">
                <SelectValue placeholder="Selecionar campanha..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">— Sem campanha —</SelectItem>
                {campaignList.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    <span className="flex items-center gap-2">
                      {c.name}
                      {c.id === device.current_campaign_id && (
                        <Badge className="text-[10px] h-4 bg-emerald-100 text-emerald-700 border-0">ativa</Badge>
                      )}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              disabled={campaignLinking || selectedCampaignId === null}
              onClick={() => handleLinkCampaign(selectedCampaignId)}
              className={cn("shrink-0", campaignLinked && "bg-emerald-600 hover:bg-emerald-700")}
            >
              {campaignLinking ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />Aplicando...</>
              ) : campaignLinked ? (
                <><CheckCircle2 className="w-4 h-4 mr-2" />Aplicado!</>
              ) : (
                "Aplicar Campanha"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

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

      {/* SPEC 004 — histórico de pareamento */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Histórico de Pareamento</CardTitle>
        </CardHeader>
        <CardContent>
          <PairingEventTimeline deviceId={id} limit={20} />
        </CardContent>
      </Card>

      {/* SPEC 006 — overlay OSD do dispositivo */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Overlay OSD</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
            <OSDConfigForm
              value={osdLocalConfig}
              onChange={setOsdLocalConfig}
              allowNull
              inheritedFrom={osdEffectiveConfig}
            />
            <OSDConfigPreview config={osdPreviewConfig} />
          </div>
          <div className="flex flex-wrap justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={osdMutation.isPending}
              onClick={() =>
                setOsdLocalConfig({
                  show_current_audio: null,
                  position: null,
                  duration_seconds: null,
                  opacity: null,
                  font_size: null,
                })
              }
            >
              Herdar da empresa
            </Button>
            <Button
              type="button"
              disabled={osdMutation.isPending}
              onClick={() => osdMutation.mutate(osdLocalConfig)}
            >
              <Save className="mr-2 h-4 w-4" />
              {osdMutation.isPending ? "Salvando..." : "Salvar overlay"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Comportamento do Player</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <p className="text-sm font-semibold">Exposição do Desktop</p>
              <p className="text-sm text-muted-foreground max-w-xl">
                Quando ativado, o player minimizará a janela periodicamente para
                exibir a área de trabalho.
              </p>
            </div>
            <Switch
              checked={desktopExposureConfig.enabled}
              onCheckedChange={(value) =>
                setDesktopExposureConfig((prev) => ({
                  ...prev,
                  enabled: value,
                }))
              }
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="desktop-exposure-interval">
                Intervalo entre exposições (segundos)
              </Label>
              <Input
                id="desktop-exposure-interval"
                type="number"
                min={10}
                max={86400}
                value={desktopExposureConfig.interval_seconds ?? ""}
                disabled={!desktopExposureConfig.enabled}
                onChange={(event) =>
                  setDesktopExposureConfig((prev) => ({
                    ...prev,
                    interval_seconds:
                      event.target.value === ""
                        ? null
                        : Number(event.target.value),
                  }))
                }
              />
              <p className="text-xs text-muted-foreground">
                Deve ser entre 10 e 86400 segundos.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="desktop-exposure-duration">
                Duração da exposição (segundos)
              </Label>
              <Input
                id="desktop-exposure-duration"
                type="number"
                min={1}
                max={300}
                value={desktopExposureConfig.duration_seconds ?? ""}
                disabled={!desktopExposureConfig.enabled}
                onChange={(event) =>
                  setDesktopExposureConfig((prev) => ({
                    ...prev,
                    duration_seconds:
                      event.target.value === ""
                        ? null
                        : Number(event.target.value),
                  }))
                }
              />
              <p className="text-xs text-muted-foreground">
                Deve ser menor que o intervalo e no máximo 300 segundos.
              </p>
            </div>
          </div>

          <div className="rounded border border-border bg-slate-50 p-4 text-sm text-slate-700">
            {desktopExposureConfig.enabled ? (
              <p>
                A cada {desktopExposureConfig.interval_seconds} segundos, o
                player exibirá o desktop por{" "}
                {desktopExposureConfig.duration_seconds} segundos
                {desktopExposureConfig.restore_fullscreen
                  ? ", restaurando o fullscreen depois."
                  : "."}
              </p>
            ) : (
              <p>Rotina de exposição do desktop desativada.</p>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Checkbox
              id="desktop-exposure-restore"
              checked={desktopExposureConfig.restore_fullscreen}
              disabled={!desktopExposureConfig.enabled}
              onCheckedChange={(value) =>
                setDesktopExposureConfig((prev) => ({
                  ...prev,
                  restore_fullscreen: value,
                }))
              }
            />
            <Label htmlFor="desktop-exposure-restore" className="text-sm">
              Restaurar fullscreen após exposição
            </Label>
          </div>

          {/* SPEC 015 — aviso visual configurável antes de minimizar. */}
          <div className="flex items-center gap-3">
            <Checkbox
              id="desktop-exposure-warning"
              checked={desktopExposureConfig.show_warning}
              disabled={!desktopExposureConfig.enabled}
              onCheckedChange={(value) =>
                setDesktopExposureConfig((prev) => ({
                  ...prev,
                  show_warning: value,
                }))
              }
            />
            <Label htmlFor="desktop-exposure-warning" className="text-sm">
              Exibir aviso antes de minimizar
            </Label>
          </div>

          {desktopExposureConfig.show_warning && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 pl-7">
              <div className="space-y-1">
                <Label htmlFor="desktop-exposure-warning-seconds">
                  Segundos antes de minimizar
                </Label>
                <Input
                  id="desktop-exposure-warning-seconds"
                  type="number"
                  min={0}
                  max={120}
                  value={desktopExposureConfig.warning_seconds_before ?? ""}
                  disabled={!desktopExposureConfig.enabled}
                  onChange={(event) =>
                    setDesktopExposureConfig((prev) => ({
                      ...prev,
                      warning_seconds_before:
                        event.target.value === ""
                          ? null
                          : Number(event.target.value),
                    }))
                  }
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="desktop-exposure-warning-text">
                  Texto do aviso
                </Label>
                <Input
                  id="desktop-exposure-warning-text"
                  type="text"
                  maxLength={255}
                  placeholder="A tela será minimizada em breve"
                  value={desktopExposureConfig.warning_text ?? ""}
                  disabled={!desktopExposureConfig.enabled}
                  onChange={(event) =>
                    setDesktopExposureConfig((prev) => ({
                      ...prev,
                      warning_text: event.target.value,
                    }))
                  }
                />
              </div>
            </div>
          )}

          <div className="flex flex-wrap justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              disabled={desktopExposureMutation.isPending}
              onClick={() =>
                setDesktopExposureConfig({
                  enabled: false,
                  interval_seconds: 10,
                  duration_seconds: 10,
                  restore_fullscreen: true,
                  show_warning: false,
                  warning_seconds_before: 15,
                  warning_text: "",
                })
              }
            >
              Redefinir
            </Button>
            <Button
              type="button"
              disabled={
                desktopExposureTestLoading || !desktopExposureConfig.enabled
              }
              onClick={handleTestDesktopExposure}
            >
              {desktopExposureTestLoading ? "Testando..." : "Testar agora"}
            </Button>
            <Button
              type="button"
              disabled={desktopExposureMutation.isPending}
              onClick={() =>
                desktopExposureMutation.mutate(desktopExposureConfig)
              }
            >
              <Save className="mr-2 h-4 w-4" />
              {desktopExposureMutation.isPending
                ? "Salvando..."
                : "Salvar configuração"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* SPEC 005 — política de áudio do dispositivo */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Áudio</CardTitle>
        </CardHeader>
        <CardContent>
          <AudioPolicySelector
            value={device?.audio_policy_default ?? null}
            onChange={async (v) => {
              try {
                await updateMutation.mutateAsync({ audio_policy_default: v });
                toast({ title: "Política de áudio atualizada" });
              } catch {
                toast({ title: "Erro ao atualizar", variant: "destructive" });
              }
            }}
            allowNull
            inheritedLabel="Herdar da empresa (padrão automático)"
            disabled={updateMutation.isPending}
          />
        </CardContent>
      </Card>

      {/* Spots específicos deste dispositivo */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Music2 className="w-4 h-4" />
            Spots de Áudio
          </CardTitle>
          {!devicePlaylistId && (
            <p className="text-xs text-muted-foreground mt-1">
              Vincule uma playlist ou campanha para habilitar agendamentos de spots neste dispositivo.
            </p>
          )}
        </CardHeader>
        <CardContent>
          <SpotSchedulePanel
            scope="device"
            scopeId={id}
            playlistId={devicePlaylistId}
            spots={allSpots}
            schedules={deviceSpotSchedules}
            tracks={[]}
            onCreateSpot={handleCreateDeviceSpot}
            onUpdateSpot={handleUpdateDeviceSpot}
            onDeleteSpot={handleDeleteDeviceSpot}
            onCreateSchedule={handleCreateDeviceSchedule}
            onUpdateSchedule={handleUpdateDeviceSchedule}
            onDeleteSchedule={handleDeleteDeviceSchedule}
          />
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Bloco de botões agrupados por categoria — Operacional / Reset / Energia.
 */
function CommandGroup({
  title,
  subtitle,
  commands,
  icons,
  commandLoading,
  onCommand,
  variant,
}) {
  const groupClass =
    {
      destructive: "border-red-200 bg-red-50/30",
      warn: "border-amber-200 bg-amber-50/30",
    }[variant] || "border-border";

  const buttonClass =
    {
      destructive: "text-red-700 border-red-300 hover:bg-red-50",
      warn: "text-amber-800 border-amber-300 hover:bg-amber-50",
    }[variant] || "";

  return (
    <div className={`border rounded-lg p-3 ${groupClass}`}>
      <div className="mb-2">
        <h4 className="text-sm font-semibold">{title}</h4>
        {subtitle && (
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {commands.map(
          ({ command, label, tooltip, payload, expiresInSeconds }) => {
            const Icon = icons[command] || RefreshCw;
            return (
              <Button
                key={command}
                variant="outline"
                size="sm"
                disabled={commandLoading === command}
                onClick={() =>
                  onCommand(command, label, { payload, expiresInSeconds })
                }
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
          },
        )}
      </div>
    </div>
  );
}

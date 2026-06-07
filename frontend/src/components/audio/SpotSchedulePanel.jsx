/**
 * SpotSchedulePanel — painel reutilizável de agendamento de spots.
 *
 * Funciona para três escopos:
 *   - playlist: vincula via playlist_id (fluxo original)
 *   - campaign: vincula via campaign_id + playlist_id da campanha
 *   - device:   vincula via device_id + playlist_id do device
 *
 * Props:
 *   scope        "playlist" | "campaign" | "device"
 *   scopeId      ID do escopo (playlist_id, campaign_id, device_id)
 *   playlistId   ID da playlist que receberá o schedule (obrigatório para campaign/device)
 *   spots        AudioSpot[]
 *   schedules    AudioSpotSchedule[] já filtrados para este escopo
 *   tracks       AudioTrack[]
 *   loading      boolean
 *   onCreateSchedule (payload) => Promise
 *   onUpdateSchedule (id, payload) => Promise
 *   onDeleteSchedule (id) => Promise
 *   onCreateSpot     (payload) => Promise  (opcional — se não passado, aba de spots fica oculta)
 *   onUpdateSpot     (id, payload) => Promise
 *   onDeleteSpot     (id) => Promise
 */
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Plus, Trash2, Edit, Loader2, Volume2, Info } from "lucide-react";

const INSERTION_POLICIES = {
  interrupt: "Interrompe música",
  wait_silence: "Aguarda música terminar",
};

const SPOT_STATUS = { active: "Ativo", inactive: "Inativo", archived: "Arquivado" };

const DAYS_OF_WEEK = [
  { value: 0, label: "Seg" },
  { value: 1, label: "Ter" },
  { value: 2, label: "Qua" },
  { value: 3, label: "Qui" },
  { value: 4, label: "Sex" },
  { value: 5, label: "Sáb" },
  { value: 6, label: "Dom" },
];

const SCOPE_LABELS = {
  playlist: "playlist",
  campaign: "campanha",
  device: "dispositivo",
};

const formatInterval = (s) => {
  if (!s) return "—";
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)} min`;
  return `${Math.floor(s / 3600)}h`;
};

const getCurrentHHMM = () =>
  new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", hour12: false });

const isWithinTimeWindow = (hhmm, start, end) => {
  if (!start && !end) return true;
  if (start && !end) return hhmm >= start;
  if (!start && end) return hhmm <= end;
  if (start <= end) return hhmm >= start && hhmm <= end;
  return hhmm >= start || hhmm <= end;
};

// Presets de intervalo: [label, segundos]
const INTERVAL_PRESETS = [
  ["5 min", 300],
  ["15 min", 900],
  ["30 min", 1800],
  ["1 hora", 3600],
  ["2 horas", 7200],
];

const intervalToUnit = (s) => {
  if (!s || s < 60) return { value: s || 30, unit: "sec" };
  if (s % 3600 === 0) return { value: s / 3600, unit: "hr" };
  return { value: Math.round(s / 60), unit: "min" };
};

const unitToSeconds = (value, unit) => {
  const v = parseInt(value) || 1;
  if (unit === "hr") return v * 3600;
  if (unit === "min") return v * 60;
  return v;
};

const emptyScheduleForm = () => ({
  spot_id: "",
  interval_seconds: 1800,
  intervalValue: 30,
  intervalUnit: "min",
  start_time: "",
  end_time: "",
  starts_at: "",
  ends_at: "",
  days_of_week: [],
  priority: 0,
  is_active: true,
  insertion_policy: "",
});

const emptySpotForm = () => ({
  name: "",
  description: "",
  track_id: "",
  status: "active",
  insertion_policy: "wait_silence",
});

export default function SpotSchedulePanel({
  scope = "playlist",
  scopeId,
  playlistId,
  spots = [],
  schedules = [],
  tracks = [],
  loading = false,
  onCreateSchedule,
  onUpdateSchedule,
  onDeleteSchedule,
  onCreateSpot,
  onUpdateSpot,
  onDeleteSpot,
}) {
  const [tab, setTab] = useState("schedules");
  const [scheduleDialog, setScheduleDialog] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [scheduleForm, setScheduleForm] = useState(emptyScheduleForm());
  const [scheduleError, setScheduleError] = useState("");
  const [scheduleSaving, setScheduleSaving] = useState(false);

  const [spotDialog, setSpotDialog] = useState(false);
  const [editingSpot, setEditingSpot] = useState(null);
  const [spotForm, setSpotForm] = useState(emptySpotForm());
  const [spotError, setSpotError] = useState("");
  const [spotSaving, setSpotSaving] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState(null); // { type, id, label }

  const hasSpotCRUD = !!onCreateSpot;
  const currentHHMM = getCurrentHHMM();
  const crossesMidnight = scheduleForm.start_time && scheduleForm.end_time
    && scheduleForm.start_time > scheduleForm.end_time;
  const outsideCurrentTime = scheduleForm.start_time || scheduleForm.end_time
    ? !isWithinTimeWindow(currentHHMM, scheduleForm.start_time, scheduleForm.end_time)
    : false;

  // ── Helpers ────────────────────────────────────────────────────────────────
  const getSpotName = (id) => spots.find((s) => s.id === id)?.name || "—";
  const getTrackName = (id) => tracks.find((t) => t.id === id)?.name || "—";
  const toggleDay = (day) =>
    setScheduleForm((p) => ({
      ...p,
      days_of_week: p.days_of_week.includes(day)
        ? p.days_of_week.filter((d) => d !== day)
        : [...p.days_of_week, day].sort(),
    }));

  // ── Schedule handlers ──────────────────────────────────────────────────────
  const openNewSchedule = () => {
    setEditingSchedule(null);
    setScheduleForm(emptyScheduleForm());
    setScheduleError("");
    setScheduleDialog(true);
  };

  const openEditSchedule = (s) => {
    setEditingSchedule(s);
    const { value: intervalValue, unit: intervalUnit } = intervalToUnit(s.interval_seconds);
    setScheduleForm({
      spot_id: s.spot_id,
      interval_seconds: s.interval_seconds,
      intervalValue,
      intervalUnit,
      start_time: s.start_time || "",
      end_time: s.end_time || "",
      starts_at: s.starts_at ? s.starts_at.slice(0, 10) : "",
      ends_at: s.ends_at ? s.ends_at.slice(0, 10) : "",
      days_of_week: s.days_of_week || [],
      priority: s.priority ?? 0,
      is_active: s.is_active ?? true,
      insertion_policy: s.insertion_policy || "",
    });
    setScheduleError("");
    setScheduleDialog(true);
  };

  const saveSchedule = async () => {
    setScheduleError("");
    if (!scheduleForm.spot_id) return setScheduleError("Selecione um spot");
    if (!scheduleForm.interval_seconds || scheduleForm.interval_seconds < 1)
      return setScheduleError("Intervalo mínimo: 1 segundo");

    // Se início e fim são iguais (ex: ambos "00:00"), trata como sem restrição de horário
    const startTime = scheduleForm.start_time || null;
    const endTime = scheduleForm.end_time || null;
    const effectiveStart = (startTime && endTime && startTime === endTime) ? null : startTime;
    const effectiveEnd = (startTime && endTime && startTime === endTime) ? null : endTime;

    const payload = {
      spot_id: scheduleForm.spot_id,
      interval_seconds: parseInt(scheduleForm.interval_seconds),
      start_time: effectiveStart,
      end_time: effectiveEnd,
      starts_at: scheduleForm.starts_at || null,
      ends_at: scheduleForm.ends_at || null,
      days_of_week: scheduleForm.days_of_week.length ? scheduleForm.days_of_week : null,
      priority: parseInt(scheduleForm.priority) || 0,
      is_active: scheduleForm.is_active,
      insertion_policy: scheduleForm.insertion_policy || null,
      // Escopos — só adiciona se houver valor
      playlist_id: playlistId || null,
      ...(scope === "campaign" && scopeId && { campaign_id: scopeId }),
      ...(scope === "device" && scopeId && { device_id: scopeId }),
    };

    setScheduleSaving(true);
    try {
      if (editingSchedule) {
        await onUpdateSchedule?.(editingSchedule.id, payload);
      } else {
        await onCreateSchedule?.(payload);
      }
      setScheduleDialog(false);
    } catch (err) {
      setScheduleError(err?.message || "Erro ao salvar agendamento");
    } finally {
      setScheduleSaving(false);
    }
  };

  // ── Spot handlers ──────────────────────────────────────────────────────────
  const openNewSpot = () => {
    setEditingSpot(null);
    setSpotForm(emptySpotForm());
    setSpotError("");
    setSpotDialog(true);
  };

  const openEditSpot = (s) => {
    setEditingSpot(s);
    setSpotForm({
      name: s.name,
      description: s.description || "",
      track_id: s.track_id,
      status: s.status,
      insertion_policy: s.insertion_policy,
    });
    setSpotError("");
    setSpotDialog(true);
  };

  const saveSpot = async () => {
    setSpotError("");
    if (!spotForm.name.trim()) return setSpotError("Nome obrigatório");
    if (!spotForm.track_id) return setSpotError("Selecione uma faixa");

    setSpotSaving(true);
    try {
      if (editingSpot) {
        await onUpdateSpot?.(editingSpot.id, spotForm);
      } else {
        await onCreateSpot?.(spotForm);
      }
      setSpotDialog(false);
    } catch (err) {
      setSpotError(err?.message || "Erro ao salvar spot");
    } finally {
      setSpotSaving(false);
    }
  };

  // ── Delete ─────────────────────────────────────────────────────────────────
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (deleteTarget.type === "schedule") await onDeleteSchedule?.(deleteTarget.id);
      if (deleteTarget.type === "spot") await onDeleteSpot?.(deleteTarget.id);
    } finally {
      setDeleteTarget(null);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  const scopeLabel = SCOPE_LABELS[scope] || scope;

  return (
    <div className="space-y-4">
      {/* Tabs internas */}
      <div className="flex gap-2 border-b pb-2">
        <button
          type="button"
          className={`px-3 py-1 text-sm rounded-t font-medium transition-colors ${
            tab === "schedules"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:text-foreground"
          }`}
          onClick={() => setTab("schedules")}
        >
          Agendamentos ({schedules.length})
        </button>
        {hasSpotCRUD && (
          <button
            type="button"
            className={`px-3 py-1 text-sm rounded-t font-medium transition-colors ${
              tab === "spots"
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setTab("spots")}
          >
            Biblioteca de Spots ({spots.length})
          </button>
        )}
      </div>

      {/* ── Aba: Agendamentos ──────────────────────────────────────────────── */}
      {tab === "schedules" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">
                Spots agendados neste {scopeLabel}
              </p>
            </div>
            <Button
              type="button"
              size="sm"
              onClick={openNewSchedule}
              disabled={loading || spots.length === 0}
            >
              <Plus className="mr-1.5 h-4 w-4" />
              Agendar spot
            </Button>
          </div>

          {spots.length === 0 && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
              <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>Crie spots na aba "Biblioteca de Spots" antes de agendar.</span>
            </div>
          )}

          {!playlistId && scope === "device" && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
              <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>
                Este {scopeLabel} não tem playlist de rádio vinculada.
                Vincule uma playlist para poder agendar spots.
              </span>
            </div>
          )}

          {schedules.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 border rounded-lg bg-muted/30">
              <Volume2 className="h-8 w-8 text-muted-foreground/40 mb-2" />
              <p className="text-sm text-muted-foreground">Nenhum spot agendado</p>
              <p className="text-xs text-muted-foreground/60 mt-1">
                Spots agendam jingles e anúncios a cada X minutos
              </p>
            </div>
          ) : (
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Spot</TableHead>
                    <TableHead>Intervalo</TableHead>
                    <TableHead>Horário</TableHead>
                    <TableHead>Dias</TableHead>
                    <TableHead className="text-center">Prior.</TableHead>
                    <TableHead className="text-center">Ativo</TableHead>
                    <TableHead className="w-16" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schedules.map((s) => {
                    const dayLabels =
                      Array.isArray(s.days_of_week) && s.days_of_week.length > 0
                        ? s.days_of_week
                            .map((d) => DAYS_OF_WEEK.find((x) => x.value === d)?.label)
                            .filter(Boolean)
                            .join(", ")
                        : "Todo dia";
                    // status visual: ativo agora vs fora da janela
                    const hhmm = getCurrentHHMM();
                    const inWindow = isWithinTimeWindow(hhmm, s.start_time, s.end_time);
                    const activeNow = s.is_active && inWindow;
                    return (
                      <TableRow key={s.id} className={!s.is_active ? "opacity-50" : ""}>
                        <TableCell className="font-medium text-sm">
                          <div className="flex items-center gap-1.5">
                            {getSpotName(s.spot_id)}
                            {activeNow && (
                              <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 flex-shrink-0" title="Ativo agora" />
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          a cada {formatInterval(s.interval_seconds)}
                        </TableCell>
                        <TableCell className="text-sm">
                          {s.start_time && s.end_time ? (
                            <span className={!inWindow && s.is_active ? "text-muted-foreground" : ""}>
                              {s.start_time}–{s.end_time}
                              {!inWindow && s.is_active && (
                                <span className="ml-1 text-xs text-muted-foreground">(fora)</span>
                              )}
                            </span>
                          ) : (
                            <span className="text-muted-foreground text-xs">Qualquer hora</span>
                          )}
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {dayLabels}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline" className="text-xs">
                            {s.priority}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Checkbox checked={!!s.is_active} disabled />
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1 justify-end">
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              onClick={() => openEditSchedule(s)}
                            >
                              <Edit className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-destructive"
                              onClick={() =>
                                setDeleteTarget({
                                  type: "schedule",
                                  id: s.id,
                                  label: getSpotName(s.spot_id),
                                })
                              }
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      )}

      {/* ── Aba: Biblioteca de spots ───────────────────────────────────────── */}
      {tab === "spots" && hasSpotCRUD && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Spots são jingles ou anúncios vinculados a uma faixa de áudio
            </p>
            <Button type="button" size="sm" onClick={openNewSpot} disabled={loading || tracks.length === 0}>
              <Plus className="mr-1.5 h-4 w-4" />
              Novo spot
            </Button>
          </div>

          {tracks.length === 0 && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
              <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>Faça upload de faixas de áudio antes de criar spots.</span>
            </div>
          )}

          {spots.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 border rounded-lg bg-muted/30">
              <Volume2 className="h-8 w-8 text-muted-foreground/40 mb-2" />
              <p className="text-sm text-muted-foreground">Nenhum spot criado</p>
            </div>
          ) : (
            <div className="space-y-2">
              {spots.map((spot) => (
                <div
                  key={spot.id}
                  className="flex items-start justify-between p-3 border rounded-lg hover:bg-muted/20"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{spot.name}</p>
                    {spot.description && (
                      <p className="text-xs text-muted-foreground truncate">{spot.description}</p>
                    )}
                    <div className="flex gap-1.5 mt-1.5 flex-wrap">
                      <Badge variant="secondary" className="text-xs">
                        {getTrackName(spot.track_id)}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {INSERTION_POLICIES[spot.insertion_policy] || spot.insertion_policy}
                      </Badge>
                      <Badge
                        variant={spot.status === "active" ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {SPOT_STATUS[spot.status] || spot.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex gap-1 flex-shrink-0 ml-2">
                    <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEditSpot(spot)}>
                      <Edit className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-destructive"
                      onClick={() => setDeleteTarget({ type: "spot", id: spot.id, label: spot.name })}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Dialog: Agendamento ─────────────────────────────────────────────── */}
      <Dialog open={scheduleDialog} onOpenChange={setScheduleDialog}>
        <DialogContent
          className="max-w-lg"
          onInteractOutside={(e) => e.preventDefault()}
          onPointerDownOutside={(e) => e.preventDefault()}
        >
          <DialogHeader>
            <DialogTitle>
              {editingSchedule ? "Editar agendamento" : "Novo agendamento de spot"}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5 py-2">

            {/* ── Seção 1: O que tocar ─────────────────────────────────────────── */}
            <div className="space-y-3">
              <div className="space-y-1.5">
                <Label>Spot *</Label>
                <Select
                  value={scheduleForm.spot_id}
                  onValueChange={(v) => setScheduleForm((p) => ({ ...p, spot_id: v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o spot" />
                  </SelectTrigger>
                  <SelectContent>
                    {spots.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="border-t" />

            {/* ── Seção 2: Com que frequência ──────────────────────────────────── */}
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium">Frequência</p>
                <p className="text-xs text-muted-foreground">De quanto em quanto tempo o spot será inserido na programação</p>
              </div>
              <div className="flex gap-2 items-center">
                <Input
                  type="number"
                  min={1}
                  max={scheduleForm.intervalUnit === "hr" ? 24 : scheduleForm.intervalUnit === "min" ? 1440 : 3600}
                  value={scheduleForm.intervalValue}
                  onChange={(e) => {
                    const v = parseInt(e.target.value) || 1;
                    setScheduleForm((p) => ({
                      ...p,
                      intervalValue: v,
                      interval_seconds: unitToSeconds(v, p.intervalUnit),
                    }));
                  }}
                  className="w-20"
                />
                <Select
                  value={scheduleForm.intervalUnit}
                  onValueChange={(unit) =>
                    setScheduleForm((p) => ({
                      ...p,
                      intervalUnit: unit,
                      interval_seconds: unitToSeconds(p.intervalValue, unit),
                    }))
                  }
                >
                  <SelectTrigger className="w-28">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sec">segundos</SelectItem>
                    <SelectItem value="min">minutos</SelectItem>
                    <SelectItem value="hr">horas</SelectItem>
                  </SelectContent>
                </Select>
                <span className="text-xs text-muted-foreground whitespace-nowrap">
                  = {formatInterval(scheduleForm.interval_seconds)}
                </span>
              </div>
              <div className="flex gap-1.5 flex-wrap">
                {INTERVAL_PRESETS.map(([label, secs]) => (
                  <button
                    key={secs}
                    type="button"
                    onClick={() => {
                      const { value, unit } = intervalToUnit(secs);
                      setScheduleForm((p) => ({ ...p, interval_seconds: secs, intervalValue: value, intervalUnit: unit }));
                    }}
                    className={`px-2.5 py-1 text-xs rounded border transition-colors ${
                      scheduleForm.interval_seconds === secs
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-border text-muted-foreground hover:border-primary/50"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <div className="border-t" />

            {/* ── Seção 3: Quando pode tocar ───────────────────────────────────── */}
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium">Restrições de horário</p>
                <p className="text-xs text-muted-foreground">O spot só dispara dentro desta faixa. Deixe em branco para tocar em qualquer horário</p>
              </div>

              {/* Horário do dia */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Horário início</Label>
                  <Input
                    type="time"
                    value={scheduleForm.start_time}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, start_time: e.target.value }))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Horário fim</Label>
                  <Input
                    type="time"
                    value={scheduleForm.end_time}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, end_time: e.target.value }))}
                  />
                </div>
              </div>
              {(crossesMidnight || outsideCurrentTime) && (
                <p className={`text-xs -mt-1 ${crossesMidnight ? "text-muted-foreground" : "text-amber-600"}`}>
                  {crossesMidnight
                    ? "Janela cruza meia-noite — normal para ex. 22:00–06:00."
                    : `Fora desta janela agora (${currentHHMM}) — spot não tocará até entrar no horário.`}
                </p>
              )}

              {/* Dias da semana */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Dias da semana <span className="ml-1">(vazio = todos os dias)</span></Label>
                <div className="flex gap-1.5 flex-wrap">
                  {DAYS_OF_WEEK.map((d) => (
                    <button
                    type="button"
                    key={d.value}
                    onClick={() => toggleDay(d.value)}
                    className={`px-2.5 py-1 text-xs rounded border font-medium transition-colors ${
                      scheduleForm.days_of_week.includes(d.value)
                        ? "bg-primary text-primary-foreground border-primary"
                        : "border-border text-muted-foreground hover:border-primary/50"
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            </div>

              {/* Período de validade — ainda dentro de Restrições */}
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Período de vigência <span className="ml-1">(vazio = sem limite de data)</span></Label>
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    type="date"
                    value={scheduleForm.starts_at}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, starts_at: e.target.value }))}
                  />
                  <Input
                    type="date"
                    value={scheduleForm.ends_at}
                    onChange={(e) => setScheduleForm((p) => ({ ...p, ends_at: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            <div className="border-t" />

            {/* ── Seção 4: Configurações extras ────────────────────────────────── */}
            <div className="grid grid-cols-2 gap-3 items-end">
              <div className="space-y-1.5">
                <Label className="text-xs">Como inserir <span className="text-muted-foreground">(override)</span></Label>
                <Select
                  value={scheduleForm.insertion_policy || "inherit"}
                  onValueChange={(v) =>
                    setScheduleForm((p) => ({ ...p, insertion_policy: v === "inherit" ? "" : v }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="inherit">Herdar do spot</SelectItem>
                    <SelectItem value="interrupt">Interrompe a música</SelectItem>
                    <SelectItem value="wait_silence">Aguarda música terminar</SelectItem>
                    <SelectItem value="fade_mix">Mix (fade)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Prioridade <span className="text-muted-foreground">(0–100)</span></Label>
                <Input
                  type="number"
                  min={0}
                  max={100}
                  value={scheduleForm.priority}
                  onChange={(e) =>
                    setScheduleForm((p) => ({ ...p, priority: parseInt(e.target.value) || 0 }))
                  }
                />
              </div>
            </div>
            <div className="flex items-center gap-2 -mt-1">
              <Checkbox
                id="sched-active"
                checked={scheduleForm.is_active}
                onCheckedChange={(v) => setScheduleForm((p) => ({ ...p, is_active: !!v }))}
              />
              <Label htmlFor="sched-active" className="text-sm">Agendamento ativo</Label>
            </div>

            {scheduleError && (
              <p className="text-sm text-destructive">{scheduleError}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setScheduleDialog(false)}>
              Cancelar
            </Button>
            <Button type="button" onClick={saveSchedule} disabled={scheduleSaving}>
              {scheduleSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {editingSchedule ? "Salvar" : "Criar agendamento"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Dialog: Spot ───────────────────────────────────────────────────── */}
      {hasSpotCRUD && (
        <Dialog open={spotDialog} onOpenChange={setSpotDialog}>
          <DialogContent
            className="max-w-md"
            onInteractOutside={(e) => e.preventDefault()}
            onPointerDownOutside={(e) => e.preventDefault()}
          >
            <DialogHeader>
              <DialogTitle>{editingSpot ? "Editar spot" : "Novo spot"}</DialogTitle>
            </DialogHeader>

            <div className="space-y-4 py-2">
              <div className="space-y-1.5">
                <Label>Nome *</Label>
                <Input
                  value={spotForm.name}
                  onChange={(e) => setSpotForm((p) => ({ ...p, name: e.target.value }))}
                  placeholder="Ex: Jingle Black Friday"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Descrição</Label>
                <Textarea
                  value={spotForm.description}
                  onChange={(e) => setSpotForm((p) => ({ ...p, description: e.target.value }))}
                  rows={2}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Faixa de áudio *</Label>
                <Select
                  value={spotForm.track_id}
                  onValueChange={(v) => setSpotForm((p) => ({ ...p, track_id: v }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione a faixa" />
                  </SelectTrigger>
                  <SelectContent>
                    {tracks.map((t) => (
                      <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Status</Label>
                  <Select
                    value={spotForm.status}
                    onValueChange={(v) => setSpotForm((p) => ({ ...p, status: v }))}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="active">Ativo</SelectItem>
                      <SelectItem value="inactive">Inativo</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Inserção padrão</Label>
                  <Select
                    value={spotForm.insertion_policy}
                    onValueChange={(v) => setSpotForm((p) => ({ ...p, insertion_policy: v }))}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="interrupt">Interrompe</SelectItem>
                      <SelectItem value="wait_silence">Aguarda</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {spotError && <p className="text-sm text-destructive">{spotError}</p>}
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setSpotDialog(false)}>Cancelar</Button>
              <Button type="button" onClick={saveSpot} disabled={spotSaving}>
                {spotSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {editingSpot ? "Salvar" : "Criar spot"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* ── AlertDialog: Confirmar exclusão ─────────────────────────────────── */}
      <AlertDialog open={!!deleteTarget} onOpenChange={(o) => !o && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmar exclusão</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir "{deleteTarget?.label}"?
              {deleteTarget?.type === "spot" &&
                " Todos os agendamentos deste spot também serão removidos."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <AlertDialogCancel type="button">Cancelar</AlertDialogCancel>
            <AlertDialogAction
              type="button"
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Excluir
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { AudioPolicySelector } from "@/components/shared/AudioPolicySelector";
import CampaignPlaylistBuilder, {
  itemsFromApi,
  itemsFromCampaignLegacy,
  normalizeCampaignPlaylistItems,
} from "@/components/campaigns/CampaignPlaylistBuilder";
import { listarItensCampanha } from "@/api/campanhas";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Check, Loader2, Monitor, Radio } from "lucide-react";
import { cn } from "@/lib/utils";

const DAYS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"];

const DEFAULT_FORM = {
  name: "",
  description: "",
  status: "draft",
  priority: 1,
  start_date: "",
  end_date: "",
  loop_count: "",
  media_ids: [],
  audio_playlist_id: "",
  video_muted: true,
  audio_policy: null,  // SPEC 005
  device_ids: [],
  schedule_all_day: true,
  schedule_days: [...DAYS],
  schedule_start_time: "08:00",
  schedule_end_time: "22:00",
  target_groups: [],
};

const NO_AUDIO_PLAYLIST = "__none__";

// Input type="date" só guarda data; datetime-local preserva hora.
// Backend recebe "YYYY-MM-DDTHH:MM" e Pydantic converte para datetime.
const toDateInputValue = (value) => {
  if (!value || typeof value !== "string") return "";
  return value.slice(0, 10);
};
const toDateTimeInputValue = (value) => {
  if (!value || typeof value !== "string") return "";
  // Aceita "YYYY-MM-DDTHH:MM[:SS...]" ou "YYYY-MM-DD".
  return value.slice(0, 16);
};

function SelectCheckbox({ checked }) {
  return (
    <div
      className={cn(
        "h-4 w-4 shrink-0 rounded-sm border-2 flex items-center justify-center transition-colors",
        checked ? "border-primary bg-primary" : "border-muted-foreground/40",
      )}
    >
      {checked && <Check className="h-3 w-3 text-primary-foreground" />}
    </div>
  );
}

export default function CampaignFormModal({
  open,
  onClose,
  onSave,
  campaign,
  mediaList = [],
  devices = [],
  audioPlaylists = [],
}) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [playlistItems, setPlaylistItems] = useState([]);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState("info");

  const { data: apiPlaylistItems = [], isLoading: playlistItemsLoading } = useQuery({
    queryKey: ["campaign-items", campaign?.id],
    queryFn: () => listarItensCampanha(campaign.id),
    enabled: open && !!campaign?.id,
  });

  useEffect(() => {
    if (campaign) {
      setForm({
        name: campaign.name || "",
        description: campaign.description || "",
        status: campaign.status || "draft",
        priority: campaign.priority || 1,
        start_date: toDateInputValue(campaign.start_date),
        end_date: toDateTimeInputValue(campaign.end_date),
        loop_count: campaign.loop_count != null ? String(campaign.loop_count) : "",
        media_ids: Array.isArray(campaign.media_ids) ? campaign.media_ids : [],
        audio_playlist_id: campaign.audio_playlist_id || "",
        video_muted: campaign.video_muted !== false,
        audio_policy: campaign.audio_policy || null,  // SPEC 005
        device_ids: Array.isArray(campaign.device_ids) ? campaign.device_ids : [],
        schedule_all_day: campaign.schedule_all_day !== false,
        schedule_days: campaign.schedule_days || [...DAYS],
        schedule_start_time: campaign.schedule_start_time || "08:00",
        schedule_end_time: campaign.schedule_end_time || "22:00",
        target_groups: campaign.target_groups || [],
      });
      setPlaylistItems(itemsFromCampaignLegacy(campaign, mediaList));
    } else {
      setForm(DEFAULT_FORM);
      setPlaylistItems([]);
    }
    setTab("info");
  }, [campaign, open, mediaList]);

  useEffect(() => {
    if (!open || !campaign?.id) return;
    if (!Array.isArray(apiPlaylistItems) || apiPlaylistItems.length === 0) return;
    setPlaylistItems(itemsFromApi(apiPlaylistItems, mediaList));
  }, [apiPlaylistItems, campaign?.id, mediaList, open]);

  const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));

  const toggleArr = (k, val) =>
    setForm((prev) => {
      const arr = Array.isArray(prev[k]) ? prev[k] : [];
      return {
        ...prev,
        [k]: arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val],
      };
    });

  const toggleDay = (day) =>
    setForm((prev) => {
      const days = Array.isArray(prev.schedule_days) ? prev.schedule_days : [];
      return {
        ...prev,
        schedule_days: days.includes(day)
          ? days.filter((d) => d !== day)
          : [...days, day],
      };
    });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const knownDeviceIds = new Set(
        (Array.isArray(devices) ? devices : []).map((device) => device.id),
      );
      const normalizedDeviceIds = knownDeviceIds.size
        ? (Array.isArray(form.device_ids) ? form.device_ids : []).filter((id) =>
            knownDeviceIds.has(id),
          )
        : form.device_ids;

      const loopCountInt = parseInt(form.loop_count, 10);
      const normalizedItems = normalizeCampaignPlaylistItems(playlistItems);
      await onSave({
        ...form,
        priority: Number(form.priority),
        audio_playlist_id: form.audio_playlist_id || null,
        video_muted: form.video_muted !== false,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
        loop_count: Number.isFinite(loopCountInt) && loopCountInt > 0 ? loopCountInt : null,
        media_ids: normalizedItems.map((item) => item.media_id),
        playlist_items: normalizedItems.map((item, index) => ({
          id: item.id,
          media_id: item.media_id,
          order_index: index * 10,
          display_duration_seconds: item.display_duration_seconds || null,
          starts_at: item.starts_at || null,
          ends_at: item.ends_at || null,
          is_active: item.is_active !== false,
          repeat_count: item.repeat_count || 1,
        })),
        device_ids: normalizedDeviceIds,
      });
    } finally {
      setSaving(false);
    }
  };

  const TABS = [
    { id: "info", label: "Informações" },
    { id: "media", label: `Mídias (${playlistItems.length})` },
    { id: "devices", label: `TVs (${(form.device_ids || []).length})` },
    { id: "schedule", label: "Agendamento" },
  ];

  const playlistOptions = [
    { value: NO_AUDIO_PLAYLIST, label: "Sem rádio indoor" },
    ...(Array.isArray(audioPlaylists) ? audioPlaylists.map((p) => ({ value: p.id, label: p.name })) : []),
  ];

  const activeDevices = Array.isArray(devices)
    ? devices.filter((d) => d.is_active)
    : [];
  const selectedDeviceIds = Array.isArray(form.device_ids) ? form.device_ids : [];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            {campaign ? "Editar Campanha" : "Nova Campanha"}
          </DialogTitle>
          <DialogDescription className="sr-only">
            Formulário para {campaign ? "editar" : "criar"} campanha
          </DialogDescription>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-1 border-b">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={cn(
                "px-3 py-2 text-sm font-medium border-b-2 transition-colors",
                tab === t.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col flex-1 overflow-hidden"
        >
          <div className="flex-1 overflow-y-auto py-4 space-y-4">
            {/* ── Info tab ─────────────────────────────────── */}
            {tab === "info" && (
              <>
                <div className="space-y-2">
                  <Label>Nome *</Label>
                  <Input
                    value={form.name}
                    onChange={(e) => set("name", e.target.value)}
                    placeholder="Nome da campanha"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Descrição</Label>
                  <Textarea
                    value={form.description}
                    onChange={(e) => set("description", e.target.value)}
                    rows={2}
                    placeholder="Objetivo da campanha..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Status</Label>
                    <Select
                      value={form.status}
                      onValueChange={(v) => set("status", v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="draft">Rascunho</SelectItem>
                        <SelectItem value="scheduled">Agendada</SelectItem>
                        <SelectItem value="active">Ativa</SelectItem>
                        <SelectItem value="paused">Pausada</SelectItem>
                        <SelectItem value="ended">Encerrada</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Prioridade (1–5)</Label>
                    <Select
                      value={String(form.priority)}
                      onValueChange={(v) => set("priority", Number(v))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {[1, 2, 3, 4, 5].map((n) => (
                          <SelectItem key={n} value={String(n)}>
                            {n} –{" "}
                            {n === 1 ? "Baixa" : n === 5 ? "Alta" : "Normal"}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Data Início</Label>
                    <Input
                      type="date"
                      value={form.start_date}
                      onChange={(e) => set("start_date", e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Data e hora de término</Label>
                    <Input
                      type="datetime-local"
                      value={form.end_date}
                      onChange={(e) => set("end_date", e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Em branco = sem data de término. O player para cravado neste instante.
                    </p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="flex items-center gap-1.5">
                    <Radio className="w-3.5 h-3.5 text-primary" />
                    Rádio Indoor (Áudio)
                  </Label>
                  <Select
                    value={form.audio_playlist_id || NO_AUDIO_PLAYLIST}
                    onValueChange={(v) =>
                      set(
                        "audio_playlist_id",
                        v === NO_AUDIO_PLAYLIST ? "" : v,
                      )
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Sem rádio indoor" />
                    </SelectTrigger>
                    <SelectContent>
                      {playlistOptions.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    A playlist de áudio tocará junto com as mídias da campanha.
                  </p>
                </div>
                {/* SPEC 005 — política de áudio */}
                <AudioPolicySelector
                  value={form.audio_policy}
                  onChange={(v) => set("audio_policy", v)}
                  allowNull
                  inheritedLabel="Herdar do dispositivo/empresa (padrão automático)"
                />

                {/* legado — mantido para compat por 2 releases */}
                <details className="text-xs text-muted-foreground mt-1">
                  <summary className="cursor-pointer hover:text-foreground">
                    Configuração legada (video_muted)
                  </summary>
                  <div className="flex items-center justify-between rounded-md border px-3 py-2 mt-2">
                    <div className="pr-3">
                      <Label>Som embutido dos vídeos (legado)</Label>
                      <p className="text-xs text-muted-foreground">
                        Substituído pela Política de áudio acima.
                      </p>
                    </div>
                    <Switch
                      checked={!form.video_muted}
                      onCheckedChange={(v) => set("video_muted", !v)}
                    />
                  </div>
                </details>
              </>
            )}

            {/* ── Mídias tab ───────────────────────────────── */}
            {tab === "media" && (
              <CampaignPlaylistBuilder
                items={playlistItems}
                onChange={setPlaylistItems}
                mediaList={mediaList}
                loading={playlistItemsLoading}
              />
            )}

            {/* ── TVs tab ──────────────────────────────────── */}
            {tab === "devices" && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  {selectedDeviceIds.length} TV(s) selecionada(s)
                </p>
                {activeDevices.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    Nenhum dispositivo cadastrado
                  </p>
                ) : (
                  activeDevices.map((d) => {
                    const selected = selectedDeviceIds.includes(d.id);
                    return (
                      <div
                        key={d.id}
                        role="button"
                        tabIndex={0}
                        onClick={() => toggleArr("device_ids", d.id)}
                        onKeyDown={(e) =>
                          (e.key === "Enter" || e.key === " ") &&
                          toggleArr("device_ids", d.id)
                        }
                        className={cn(
                          "flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors select-none",
                          selected
                            ? "border-primary bg-primary/5"
                            : "border-border hover:border-primary/30",
                        )}
                      >
                        <Monitor className="w-5 h-5 text-muted-foreground shrink-0" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{d.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {d.location}
                            {d.group ? ` · ${d.group}` : ""}
                          </p>
                        </div>
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-xs shrink-0",
                            d.status === "online"
                              ? "text-emerald-600"
                              : "text-muted-foreground",
                          )}
                        >
                          {d.status}
                        </Badge>
                        <SelectCheckbox checked={selected} />
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* ── Agendamento tab ──────────────────────────── */}
            {tab === "schedule" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Rodar o dia todo</Label>
                  <Switch
                    checked={form.schedule_all_day}
                    onCheckedChange={(v) => set("schedule_all_day", v)}
                  />
                </div>
                {!form.schedule_all_day && (
                  <>
                    <div className="space-y-2">
                      <Label>Dias da semana</Label>
                      <div className="flex flex-wrap gap-2">
                        {DAYS.map((day) => (
                          <Button
                            key={day}
                            type="button"
                            variant={
                              (form.schedule_days || []).includes(day)
                                ? "default"
                                : "outline"
                            }
                            size="sm"
                            onClick={() => toggleDay(day)}
                            className="capitalize"
                          >
                            {day}
                          </Button>
                        ))}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Início diário</Label>
                        <Input
                          type="time"
                          value={form.schedule_start_time}
                          onChange={(e) =>
                            set("schedule_start_time", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Fim diário</Label>
                        <Input
                          type="time"
                          value={form.schedule_end_time}
                          onChange={(e) =>
                            set("schedule_end_time", e.target.value)
                          }
                        />
                      </div>
                    </div>
                  </>
                )}

                <div className="border-t pt-4 space-y-2">
                  <Label>Número de repetições da playlist</Label>
                  <Input
                    type="number"
                    min="1"
                    step="1"
                    value={form.loop_count}
                    placeholder="Em branco = loop infinito"
                    onChange={(e) => set("loop_count", e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Quantas vezes a fila completa deve ser repetida. O player para no
                    que acontecer primeiro: este contador, a hora diária de fim, ou a
                    data de término definida na aba Informações.
                  </p>
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saving}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {campaign ? "Salvar alterações" : "Criar Campanha"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

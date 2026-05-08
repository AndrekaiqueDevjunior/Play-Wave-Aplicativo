import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import {
  X,
  Plus,
  ChevronDown,
  ChevronUp,
  Calendar,
  Clock,
  Monitor,
  Film,
} from "lucide-react";
import { cn } from "@/lib/utils";

const DAYS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"];
const DAY_LABELS = {
  seg: "Seg",
  ter: "Ter",
  qua: "Qua",
  qui: "Qui",
  sex: "Sex",
  sab: "Sáb",
  dom: "Dom",
};

const statusColors = {
  active: "bg-emerald-500",
  draft: "bg-slate-400",
  paused: "bg-amber-500",
  ended: "bg-slate-300",
};

export default function ScheduleSidebar({
  campaigns,
  devices,
  media,
  selectedDay,
  onClose,
  onCampaignSaved,
  onCampaignMoved,
}) {
  const [tab, setTab] = useState("day"); // 'day' | 'new'
  const [form, setForm] = useState({
    name: "",
    description: "",
    start_date: selectedDay || "",
    end_date: selectedDay || "",
    status: "active",
    schedule_all_day: true,
    schedule_start_time: "08:00",
    schedule_end_time: "22:00",
    schedule_days: [...DAYS],
    media_ids: [],
    device_ids: [],
  });
  const [saving, setSaving] = useState(false);
  const [mediaOpen, setMediaOpen] = useState(false);
  const [devicesOpen, setDevicesOpen] = useState(false);

  const dayCampaigns = selectedDay
    ? campaigns.filter(
        (c) =>
          c.start_date &&
          c.end_date &&
          selectedDay >= c.start_date &&
          selectedDay <= c.end_date,
      )
    : [];

  const toggleArr = (key, id) =>
    setForm((prev) => ({
      ...prev,
      [key]: prev[key].includes(id)
        ? prev[key].filter((x) => x !== id)
        : [...prev[key], id],
    }));

  const toggleDay = (day) =>
    setForm((prev) => ({
      ...prev,
      schedule_days: prev.schedule_days.includes(day)
        ? prev.schedule_days.filter((d) => d !== day)
        : [...prev.schedule_days, day],
    }));

  const handleSave = async () => {
    if (!form.name) return;
    setSaving(true);
    await onCampaignSaved(form);
    setForm({
      name: "",
      description: "",
      start_date: selectedDay || "",
      end_date: selectedDay || "",
      status: "active",
      schedule_all_day: true,
      schedule_start_time: "08:00",
      schedule_end_time: "22:00",
      schedule_days: [...DAYS],
      media_ids: [],
      device_ids: [],
    });
    setSaving(false);
    setTab("day");
  };

  const formatDate = (d) => {
    if (!d) return "—";
    const [y, m, day] = d.split("-");
    return `${day}/${m}/${y}`;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b shrink-0">
        <div>
          <p className="text-xs text-muted-foreground uppercase tracking-wide font-semibold">
            Agenda
          </p>
          <h3 className="font-bold text-foreground">
            {selectedDay ? formatDate(selectedDay) : "Painel"}
          </h3>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex border-b shrink-0">
        <button
          className={cn(
            "flex-1 py-2.5 text-sm font-medium transition-colors",
            tab === "day"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground",
          )}
          onClick={() => setTab("day")}
        >
          <Calendar className="w-3.5 h-3.5 inline mr-1.5" />
          Dia
        </button>
        <button
          className={cn(
            "flex-1 py-2.5 text-sm font-medium transition-colors",
            tab === "new"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground",
          )}
          onClick={() => setTab("new")}
        >
          <Plus className="w-3.5 h-3.5 inline mr-1.5" />
          Nova Campanha
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {tab === "day" && (
          <>
            {dayCampaigns.length === 0 ? (
              <div className="flex flex-col items-center py-10 text-center">
                <Calendar className="w-10 h-10 text-muted-foreground/40 mb-3" />
                <p className="text-sm text-muted-foreground">
                  Nenhuma campanha neste dia
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-3"
                  onClick={() => setTab("new")}
                >
                  <Plus className="w-3.5 h-3.5 mr-1.5" />
                  Criar campanha
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
                  {dayCampaigns.length} campanha(s)
                </p>
                {dayCampaigns.map((c) => (
                  <div
                    key={c.id}
                    className="rounded-xl border bg-card p-3 space-y-2 shadow-sm"
                  >
                    <div className="flex items-start gap-2">
                      <span
                        className={cn(
                          "w-2 h-2 rounded-full mt-1.5 shrink-0",
                          statusColors[c.status],
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold truncate">
                          {c.name}
                        </p>
                        {c.description && (
                          <p className="text-xs text-muted-foreground truncate">
                            {c.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-1 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(c.start_date)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {c.schedule_all_day
                          ? "Dia todo"
                          : `${c.schedule_start_time}–${c.schedule_end_time}`}
                      </span>
                      <span className="flex items-center gap-1">
                        <Monitor className="w-3 h-3" />
                        {c.device_ids?.length || 0} TVs
                      </span>
                      <span className="flex items-center gap-1">
                        <Film className="w-3 h-3" />
                        {c.media_ids?.length || 0} mídias
                      </span>
                    </div>
                    <div className="flex gap-2 pt-1">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-[10px] border-0 text-white",
                          statusColors[c.status],
                        )}
                      >
                        {c.status === "active"
                          ? "Ativa"
                          : c.status === "draft"
                            ? "Rascunho"
                            : c.status === "paused"
                              ? "Pausada"
                              : "Encerrada"}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {tab === "new" && (
          <div className="space-y-4">
            {/* Nome */}
            <div className="space-y-1.5">
              <Label className="text-xs">Nome da Campanha *</Label>
              <Input
                placeholder="Ex: Promoção de Maio"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>

            {/* Descrição */}
            <div className="space-y-1.5">
              <Label className="text-xs">Descrição</Label>
              <Textarea
                placeholder="Objetivo da campanha..."
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
                className="h-20 resize-none"
              />
            </div>

            {/* Datas */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Início</Label>
                <Input
                  type="date"
                  value={form.start_date}
                  onChange={(e) =>
                    setForm({ ...form, start_date: e.target.value })
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Fim</Label>
                <Input
                  type="date"
                  value={form.end_date}
                  onChange={(e) =>
                    setForm({ ...form, end_date: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Status */}
            <div className="space-y-1.5">
              <Label className="text-xs">Status Inicial</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setForm({ ...form, status: v })}
              >
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Rascunho</SelectItem>
                  <SelectItem value="active">Ativa</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Horário */}
            <div className="space-y-2 rounded-lg border p-3 bg-muted/30">
              <div className="flex items-center justify-between">
                <Label className="text-xs">Rodar o dia todo</Label>
                <Switch
                  checked={form.schedule_all_day}
                  onCheckedChange={(v) =>
                    setForm({ ...form, schedule_all_day: v })
                  }
                />
              </div>
              {!form.schedule_all_day && (
                <>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {DAYS.map((day) => (
                      <button
                        key={day}
                        type="button"
                        onClick={() => toggleDay(day)}
                        className={cn(
                          "px-2 py-0.5 rounded text-xs font-medium transition-colors",
                          form.schedule_days.includes(day)
                            ? "bg-primary text-white"
                            : "bg-muted text-muted-foreground",
                        )}
                      >
                        {DAY_LABELS[day]}
                      </button>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <div className="space-y-1">
                      <Label className="text-xs">De</Label>
                      <Input
                        type="time"
                        value={form.schedule_start_time}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            schedule_start_time: e.target.value,
                          })
                        }
                        className="h-8 text-sm"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Até</Label>
                      <Input
                        type="time"
                        value={form.schedule_end_time}
                        onChange={(e) =>
                          setForm({
                            ...form,
                            schedule_end_time: e.target.value,
                          })
                        }
                        className="h-8 text-sm"
                      />
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Mídias */}
            <div className="rounded-lg border overflow-hidden">
              <button
                className="flex w-full items-center justify-between p-3 text-sm font-medium hover:bg-muted/50 transition-colors"
                onClick={() => setMediaOpen((o) => !o)}
              >
                <span className="flex items-center gap-2">
                  <Film className="w-4 h-4 text-muted-foreground" />
                  Mídias{" "}
                  <Badge className="ml-1 text-[10px] h-5">
                    {form.media_ids.length}
                  </Badge>
                </span>
                {mediaOpen ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
              {mediaOpen && (
                <div className="border-t divide-y max-h-40 overflow-y-auto">
                  {media.length === 0 && (
                    <p className="text-xs text-muted-foreground p-3">
                      Nenhuma mídia disponível
                    </p>
                  )}
                  {media.map((m) => (
                    <label
                      key={m.id}
                      className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-muted/50"
                    >
                      <input
                        type="checkbox"
                        checked={form.media_ids.includes(m.id)}
                        onChange={() => toggleArr("media_ids", m.id)}
                        className="rounded"
                      />
                      <span className="text-xs truncate">{m.name}</span>
                      <span className="text-[10px] text-muted-foreground ml-auto">
                        {m.type === "video" ? "Vídeo" : "Img"}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            {/* Dispositivos */}
            <div className="rounded-lg border overflow-hidden">
              <button
                className="flex w-full items-center justify-between p-3 text-sm font-medium hover:bg-muted/50 transition-colors"
                onClick={() => setDevicesOpen((o) => !o)}
              >
                <span className="flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-muted-foreground" />
                  TVs{" "}
                  <Badge className="ml-1 text-[10px] h-5">
                    {form.device_ids.length}
                  </Badge>
                </span>
                {devicesOpen ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>
              {devicesOpen && (
                <div className="border-t divide-y max-h-40 overflow-y-auto">
                  {devices.length === 0 && (
                    <p className="text-xs text-muted-foreground p-3">
                      Nenhum dispositivo cadastrado
                    </p>
                  )}
                  {devices.map((d) => (
                    <label
                      key={d.id}
                      className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-muted/50"
                    >
                      <input
                        type="checkbox"
                        checked={form.device_ids.includes(d.id)}
                        onChange={() => toggleArr("device_ids", d.id)}
                        className="rounded"
                      />
                      <span className="text-xs truncate">{d.name}</span>
                      <span
                        className={cn(
                          "text-[10px] ml-auto",
                          d.status === "online"
                            ? "text-emerald-600"
                            : "text-muted-foreground",
                        )}
                      >
                        {d.status}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer action */}
      {tab === "new" && (
        <div className="p-4 border-t shrink-0">
          <Button
            className="w-full"
            disabled={!form.name || saving}
            onClick={handleSave}
          >
            {saving ? (
              "Salvando..."
            ) : (
              <>
                <Plus className="w-4 h-4 mr-2" />
                Criar Campanha
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}

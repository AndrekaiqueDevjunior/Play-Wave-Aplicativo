import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
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
import { Checkbox } from "@/components/ui/checkbox";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Loader2, Image, Film, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";

const DAYS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"];

const DEFAULT_FORM = {
  name: "",
  description: "",
  status: "draft",
  priority: 1,
  start_date: "",
  end_date: "",
  media_ids: [],
  device_ids: [],
  schedule_all_day: true,
  schedule_days: [...DAYS],
  schedule_start_time: "08:00",
  schedule_end_time: "22:00",
  target_groups: [],
};

export default function CampaignFormModal({
  open,
  onClose,
  onSave,
  campaign,
  mediaList = [],
  devices = [],
}) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState("info"); // info | media | devices | schedule

  useEffect(() => {
    if (campaign) {
      setForm({
        name: campaign.name || "",
        description: campaign.description || "",
        status: campaign.status || "draft",
        priority: campaign.priority || 1,
        start_date: campaign.start_date || "",
        end_date: campaign.end_date || "",
        media_ids: campaign.media_ids || [],
        device_ids: campaign.device_ids || [],
        schedule_all_day: campaign.schedule_all_day !== false,
        schedule_days: campaign.schedule_days || [...DAYS],
        schedule_start_time: campaign.schedule_start_time || "08:00",
        schedule_end_time: campaign.schedule_end_time || "22:00",
        target_groups: campaign.target_groups || [],
      });
    } else {
      setForm(DEFAULT_FORM);
    }
    setTab("info");
  }, [campaign, open]);

  const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));
  const toggleArr = (k, val) =>
    setForm((prev) => ({
      ...prev,
      [k]: prev[k].includes(val)
        ? prev[k].filter((x) => x !== val)
        : [...prev[k], val],
    }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    await onSave({ ...form, priority: Number(form.priority) });
    setSaving(false);
  };

  const TABS = [
    { id: "info", label: "Informações" },
    { id: "media", label: `Mídias (${form.media_ids.length})` },
    { id: "devices", label: `TVs (${form.device_ids.length})` },
    { id: "schedule", label: "Agendamento" },
  ];

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>
            {campaign ? "Editar Campanha" : "Nova Campanha"}
          </DialogTitle>
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
                    <Label>Data Fim</Label>
                    <Input
                      type="date"
                      value={form.end_date}
                      onChange={(e) => set("end_date", e.target.value)}
                    />
                  </div>
                </div>
              </>
            )}

            {tab === "media" && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  {form.media_ids.length} mídia(s) selecionada(s)
                </p>
                {mediaList
                  .filter((m) => m.status === "available")
                  .map((m) => (
                    <div
                      key={m.id}
                      onClick={() => toggleArr("media_ids", m.id)}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors",
                        form.media_ids.includes(m.id)
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/30",
                      )}
                    >
                      {m.thumbnail_url ? (
                        <img
                          src={m.thumbnail_url}
                          alt={m.name}
                          className="w-14 h-9 rounded object-cover shrink-0"
                        />
                      ) : (
                        <div className="w-14 h-9 rounded bg-muted flex items-center justify-center shrink-0">
                          {m.type === "video" ? (
                            <Film className="w-4 h-4 text-muted-foreground" />
                          ) : (
                            <Image className="w-4 h-4 text-muted-foreground" />
                          )}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{m.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {m.type} · {m.duration}s
                          {m.category ? ` · ${m.category}` : ""}
                        </p>
                      </div>
                      <Checkbox
                        checked={form.media_ids.includes(m.id)}
                        readOnly
                      />
                    </div>
                  ))}
                {mediaList.length === 0 && (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    Nenhuma mídia disponível
                  </p>
                )}
              </div>
            )}

            {tab === "devices" && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  {form.device_ids.length} TV(s) selecionada(s)
                </p>
                {devices
                  .filter((d) => d.is_active)
                  .map((d) => (
                    <div
                      key={d.id}
                      onClick={() => toggleArr("device_ids", d.id)}
                      className={cn(
                        "flex items-center gap-3 p-3 rounded-lg border-2 cursor-pointer transition-colors",
                        form.device_ids.includes(d.id)
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
                      <Checkbox
                        checked={form.device_ids.includes(d.id)}
                        readOnly
                      />
                    </div>
                  ))}
                {devices.length === 0 && (
                  <p className="text-sm text-muted-foreground py-4 text-center">
                    Nenhum dispositivo cadastrado
                  </p>
                )}
              </div>
            )}

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
                              form.schedule_days.includes(day)
                                ? "default"
                                : "outline"
                            }
                            size="sm"
                            onClick={() => toggleArr("schedule_days", day)}
                            className="capitalize"
                          >
                            {day}
                          </Button>
                        ))}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Início</Label>
                        <Input
                          type="time"
                          value={form.schedule_start_time}
                          onChange={(e) =>
                            set("schedule_start_time", e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Fim</Label>
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

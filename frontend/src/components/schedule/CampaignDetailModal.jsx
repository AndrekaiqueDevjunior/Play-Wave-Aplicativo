import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar, Clock, Monitor, Film, Pencil, Check, X } from "lucide-react";
import StatusBadge from "@/components/shared/StatusBadge";
import { cn } from "@/lib/utils";

const statusColors = {
  active: "bg-emerald-500",
  draft: "bg-slate-400",
  paused: "bg-amber-500",
  ended: "bg-slate-300",
};

export default function CampaignDetailModal({ campaign, onClose, onUpdate }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    name: campaign?.name || "",
    start_date: campaign?.start_date || "",
    end_date: campaign?.end_date || "",
    status: campaign?.status || "draft",
  });
  const [saving, setSaving] = useState(false);

  if (!campaign) return null;

  const handleSave = async () => {
    setSaving(true);
    await onUpdate(campaign.id, form);
    setSaving(false);
    setEditing(false);
  };

  const formatDate = (d) => {
    if (!d) return "—";
    const [y, m, day] = d.split("-");
    return `${day}/${m}/${y}`;
  };

  return (
    <Dialog open={!!campaign} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <span
              className={cn(
                "w-3 h-3 rounded-full shrink-0",
                statusColors[campaign.status],
              )}
            />
            <DialogTitle className="text-base">{campaign.name}</DialogTitle>
          </div>
        </DialogHeader>

        {!editing ? (
          <div className="space-y-4">
            {campaign.description && (
              <p className="text-sm text-muted-foreground">
                {campaign.description}
              </p>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-muted/50 p-3 space-y-1">
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground font-semibold">
                  Status
                </p>
                <StatusBadge status={campaign.status} />
              </div>
              <div className="rounded-lg bg-muted/50 p-3 space-y-1">
                <p className="text-[10px] uppercase tracking-wide text-muted-foreground font-semibold">
                  Exibições
                </p>
                <p className="text-sm font-semibold">
                  {(campaign.total_views || 0).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Calendar className="w-4 h-4" />
                <span>
                  {formatDate(campaign.start_date)} →{" "}
                  {formatDate(campaign.end_date)}
                </span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span>
                  {campaign.schedule_all_day !== false
                    ? "Dia todo"
                    : `${campaign.schedule_start_time} – ${campaign.schedule_end_time}`}
                </span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Monitor className="w-4 h-4" />
                <span>{campaign.device_ids?.length || 0} TVs vinculadas</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <Film className="w-4 h-4" />
                <span>{campaign.media_ids?.length || 0} mídias</span>
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setEditing(true)}
              >
                <Pencil className="w-3.5 h-3.5 mr-1.5" />
                Editar datas
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-xs">Nome</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
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
            <div className="space-y-1.5">
              <Label className="text-xs">Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setForm({ ...form, status: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Rascunho</SelectItem>
                  <SelectItem value="active">Ativa</SelectItem>
                  <SelectItem value="paused">Pausada</SelectItem>
                  <SelectItem value="ended">Encerrada</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setEditing(false)}
              >
                <X className="w-3.5 h-3.5 mr-1" />
                Cancelar
              </Button>
              <Button size="sm" disabled={saving} onClick={handleSave}>
                <Check className="w-3.5 h-3.5 mr-1" />
                {saving ? "Salvando..." : "Salvar"}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

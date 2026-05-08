import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { listarPlaylistsAudio } from "@/api/audio";
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
import { Loader2, Radio } from "lucide-react";

const DEVICE_TYPES = [
  { value: "tv", label: "TV" },
  { value: "tablet", label: "Tablet" },
  { value: "totem", label: "Totem" },
  { value: "smartphone", label: "Celular" },
  { value: "panel", label: "Painel" },
  { value: "other", label: "Outro" },
];

const DEFAULT_FORM = {
  name: "",
  pairing_code: "",
  device_type: "tv",
  location: "",
  group: "",
  os: "Web Player",
  notes: "",
  audio_playlist_id: "",
  audio_volume: 0.7,
};

export default function DeviceFormModal({ open, onClose, onSave, device }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);

  const { data: playlists = [] } = useQuery({
    queryKey: ["audio-playlists"],
    queryFn: () => listarPlaylistsAudio({ status: "active" }),
  });

  useEffect(() => {
    if (device) {
      setForm({
        name: device.name || "",
        pairing_code: device.pairing_code || "",
        device_type: device.device_type || "tv",
        location: device.location || "",
        group: device.group || "",
        os: device.os || "Web Player",
        notes: device.notes || "",
        audio_playlist_id: device.audio_playlist_id || "",
        audio_volume: device.audio_volume ?? 0.7,
      });
    } else {
      setForm(DEFAULT_FORM);
    }
  }, [device, open]);

  const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.pairing_code.trim()) return;
    setSaving(true);
    await onSave(form);
    setSaving(false);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {device ? "Editar Dispositivo" : "Novo Dispositivo"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 space-y-2">
              <Label>Nome *</Label>
              <Input
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
                placeholder="Ex: TV Recepção"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Código de Pareamento *</Label>
              <Input
                value={form.pairing_code}
                onChange={(e) =>
                  set("pairing_code", e.target.value.toUpperCase())
                }
                placeholder="TV-0000"
                className="font-mono tracking-widest"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Select
                value={form.device_type}
                onValueChange={(v) => set("device_type", v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DEVICE_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Localização</Label>
              <Input
                value={form.location}
                onChange={(e) => set("location", e.target.value)}
                placeholder="Ex: Recepção"
              />
            </div>
            <div className="space-y-2">
              <Label>Grupo</Label>
              <Input
                value={form.group}
                onChange={(e) => set("group", e.target.value)}
                placeholder="Ex: Matriz"
              />
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Sistema Operacional</Label>
              <Select value={form.os} onValueChange={(v) => set("os", v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Web Player">Web Player</SelectItem>
                  <SelectItem value="Android TV">Android TV</SelectItem>
                  <SelectItem value="Windows">Windows</SelectItem>
                  <SelectItem value="iOS">iOS</SelectItem>
                  <SelectItem value="Linux">Linux</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="col-span-2 space-y-2">
              <Label>Observações</Label>
              <Textarea
                value={form.notes}
                onChange={(e) => set("notes", e.target.value)}
                placeholder="Anotações opcionais..."
                rows={2}
              />
            </div>

            {/* Rádio Indoor */}
            <div className="col-span-2 border-t pt-4 space-y-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <Radio className="w-4 h-4 text-primary" />
                Rádio Indoor
              </div>
              <div className="space-y-2">
                <Label>Playlist Sonora</Label>
                <Select
                  value={form.audio_playlist_id || "none"}
                  onValueChange={(v) =>
                    set("audio_playlist_id", v === "none" ? "" : v)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Nenhuma playlist" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sem rádio indoor</SelectItem>
                    {playlists.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {form.audio_playlist_id && (
                <div className="space-y-1">
                  <Label>Volume: {Math.round(form.audio_volume * 100)}%</Label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={form.audio_volume}
                    onChange={(e) =>
                      set("audio_volume", parseFloat(e.target.value))
                    }
                    className="w-full accent-primary"
                  />
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saving}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {device ? "Salvar alterações" : "Cadastrar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

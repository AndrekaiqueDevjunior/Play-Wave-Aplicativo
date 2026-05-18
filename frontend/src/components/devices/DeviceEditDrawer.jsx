import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Radio, Tv, Megaphone } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import ComboSearch from "@/components/shared/ComboSearch";
import QuickCreateDrawer from "@/components/shared/QuickCreateDrawer";
import { listarPlaylistsAudio } from "@/api/audio";
import { listarCampanhas } from "@/api/campanhas";
import { listarLocalizacoes } from "@/api/localizacoes";
import { listarDispositivos } from "@/api/dispositivos";

const DEVICE_TYPES = [
  { value: "tv", label: "TV" },
  { value: "tablet", label: "Tablet" },
  { value: "totem", label: "Totem" },
  { value: "smartphone", label: "Celular" },
  { value: "panel", label: "Painel" },
  { value: "other", label: "Outro" },
];

const OS_OPTIONS = [
  { value: "web_player", label: "Web Player" },
  { value: "android_tv", label: "Android TV" },
  { value: "windows", label: "Windows" },
  { value: "ios", label: "iOS" },
  { value: "linux", label: "Linux" },
  { value: "tizen", label: "Tizen (Samsung)" },
  { value: "webos", label: "WebOS (LG)" },
];

const DEFAULT_FORM = {
  name: "",
  pairing_code: "",
  device_type: "tv",
  location: "",
  group: "",
  os: "web_player",
  notes: "",
  audio_playlist_id: "",
  audio_volume: 0.7,
  current_campaign_id: "",
};

export default function DeviceEditDrawer({ open, onClose, onSave, device }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [extraLocations, setExtraLocations] = useState([]);
  const [extraGroups, setExtraGroups] = useState([]);
  const [createLocationOpen, setCreateLocationOpen] = useState(false);
  const [createGroupOpen, setCreateGroupOpen] = useState(false);
  const [createInitialValue, setCreateInitialValue] = useState("");

  const { data: playlists = [] } = useQuery({
    queryKey: ["audio-playlists"],
    queryFn: () => listarPlaylistsAudio({ status: "active" }),
    enabled: open,
  });

  const { data: campaigns = [] } = useQuery({
    queryKey: ["campaigns-select"],
    queryFn: () => listarCampanhas({ limit: 200 }),
    enabled: open,
  });

  const { data: localizacoes = [] } = useQuery({
    queryKey: ["locations-select"],
    queryFn: () => listarLocalizacoes({ limit: 200 }),
    enabled: open,
  });

  const { data: allDevices = [] } = useQuery({
    queryKey: ["devices"],
    queryFn: () => listarDispositivos(),
    staleTime: Infinity,
    enabled: open,
  });

  const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));

  useEffect(() => {
    if (device) {
      setForm({
        name: device.name || "",
        pairing_code: device.pairing_code || "",
        device_type: device.device_type || "tv",
        location: device.location || "",
        group: device.group || "",
        os: device.os || "web_player",
        notes: device.notes || "",
        audio_playlist_id: device.audio_playlist_id || "",
        audio_volume: device.audio_volume ?? 0.7,
        current_campaign_id: device.current_campaign_id || "",
      });
    } else {
      setForm(DEFAULT_FORM);
    }
    setExtraLocations([]);
    setExtraGroups([]);
  }, [device, open]);

  const locationOptions = [
    ...localizacoes.map((l) => ({ value: l.name || l.id, label: l.name })),
    ...Array.from(
      new Set([
        ...allDevices.map((d) => d.location).filter(Boolean),
        ...extraLocations,
      ])
    )
      .filter((loc) => !localizacoes.some((l) => l.name === loc))
      .map((loc) => ({ value: loc, label: loc })),
  ];

  const groupOptions = [
    ...Array.from(
      new Set([
        ...allDevices.map((d) => d.group).filter(Boolean),
        ...extraGroups,
      ])
    ).map((g) => ({ value: g, label: g })),
  ];

  const campaignOptions = (Array.isArray(campaigns) ? campaigns : campaigns?.items || []).map(
    (c) => ({ value: c.id, label: c.name })
  );

  const playlistOptions = [
    { value: "__none__", label: "Sem rádio indoor" },
    ...playlists.map((p) => ({ value: p.id, label: p.name })),
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim() || !form.pairing_code.trim()) return;
    setSaving(true);
    try {
      await onSave({
        ...form,
        audio_playlist_id: form.audio_playlist_id === "__none__" ? "" : form.audio_playlist_id,
        current_campaign_id: form.current_campaign_id || null,
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-[480px] overflow-y-auto flex flex-col gap-0 p-0"
      >
        <SheetHeader className="px-6 pt-6 pb-4 border-b">
          <SheetTitle className="flex items-center gap-2 text-base">
            <Tv className="w-4 h-4 text-primary" />
            {device ? "Editar Dispositivo" : "Novo Dispositivo"}
          </SheetTitle>
          {device && (
            <SheetDescription className="text-xs font-mono text-muted-foreground">
              {device.pairing_code}
            </SheetDescription>
          )}
        </SheetHeader>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col flex-1 overflow-y-auto"
        >
          <div className="px-6 py-5 space-y-5 flex-1">
            {/* Nome */}
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Identificação
              </Label>
              <Input
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
                placeholder="Ex: TV Recepção"
                required
              />
            </div>

            {/* Código + Tipo */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Código de Pareamento *</Label>
                <Input
                  value={form.pairing_code}
                  onChange={(e) => set("pairing_code", e.target.value.toUpperCase())}
                  placeholder="TV-0000"
                  className="font-mono tracking-widest"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Tipo</Label>
                <ComboSearch
                  options={DEVICE_TYPES}
                  value={form.device_type}
                  onChange={(v) => set("device_type", v)}
                  placeholder="Tipo"
                  searchPlaceholder="Buscar tipo..."
                />
              </div>
            </div>

            <Separator />

            {/* Localização + Grupo */}
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Localização &amp; Grupo
              </Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Localização</Label>
                  <ComboSearch
                    options={locationOptions}
                    value={form.location}
                    onChange={(v) => set("location", v)}
                    placeholder="Selecionar..."
                    searchPlaceholder="Buscar ou criar..."
                    createLabel="+ Nova localização"
                    onCreateClick={(text) => {
                      setCreateInitialValue(text);
                      setCreateLocationOpen(true);
                    }}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">Grupo</Label>
                  <ComboSearch
                    options={groupOptions}
                    value={form.group}
                    onChange={(v) => set("group", v)}
                    placeholder="Selecionar..."
                    searchPlaceholder="Buscar ou criar..."
                    createLabel="+ Novo grupo"
                    onCreateClick={(text) => {
                      setCreateInitialValue(text);
                      setCreateGroupOpen(true);
                    }}
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Sistema Operacional */}
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Sistema Operacional
              </Label>
              <ComboSearch
                options={OS_OPTIONS}
                value={form.os}
                onChange={(v) => set("os", v)}
                placeholder="Selecionar SO..."
                searchPlaceholder="Buscar sistema..."
              />
            </div>

            <Separator />

            {/* Campanha */}
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1.5">
                <Megaphone className="w-3.5 h-3.5 text-primary" />
                Campanha
              </Label>
              <ComboSearch
                options={[{ value: "__none__", label: "Nenhuma campanha" }, ...campaignOptions]}
                value={form.current_campaign_id || "__none__"}
                onChange={(v) => set("current_campaign_id", v === "__none__" ? "" : v)}
                placeholder="Associar campanha..."
                searchPlaceholder="Buscar campanha..."
              />
            </div>

            <Separator />

            {/* Rádio Indoor */}
            <div className="space-y-3">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1.5">
                <Radio className="w-3.5 h-3.5 text-primary" />
                Rádio Indoor
              </Label>
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Playlist Sonora</Label>
                <ComboSearch
                  options={playlistOptions}
                  value={form.audio_playlist_id || "__none__"}
                  onChange={(v) =>
                    set("audio_playlist_id", v === "__none__" ? "" : v)
                  }
                  placeholder="Sem rádio indoor"
                  searchPlaceholder="Buscar playlist..."
                />
              </div>
              {form.audio_playlist_id && form.audio_playlist_id !== "__none__" && (
                <div className="space-y-1.5">
                  <Label className="text-xs text-muted-foreground">
                    Volume: {Math.round(form.audio_volume * 100)}%
                  </Label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={form.audio_volume}
                    onChange={(e) => set("audio_volume", parseFloat(e.target.value))}
                    className="w-full accent-primary"
                  />
                </div>
              )}
            </div>

            <Separator />

            {/* Observações */}
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Observações
              </Label>
              <Textarea
                value={form.notes}
                onChange={(e) => set("notes", e.target.value)}
                placeholder="Anotações opcionais..."
                rows={2}
                className="resize-none text-sm"
              />
            </div>
          </div>

          <SheetFooter className="px-6 py-4 border-t bg-muted/30 flex-row gap-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancelar
            </Button>
            <Button type="submit" disabled={saving} className="flex-1">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {device ? "Salvar alterações" : "Cadastrar"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>

      <QuickCreateDrawer
        open={createLocationOpen}
        onClose={() => setCreateLocationOpen(false)}
        title="Nova Localização"
        description="A localização ficará disponível em todos os dispositivos."
        label="Nome da localização"
        placeholder="Ex: Recepção, Sala 1..."
        initialValue={createInitialValue}
        onSave={(name) => {
          setExtraLocations((prev) => [...prev, name]);
          set("location", name);
        }}
      />

      <QuickCreateDrawer
        open={createGroupOpen}
        onClose={() => setCreateGroupOpen(false)}
        title="Novo Grupo"
        description="Agrupe dispositivos por filial, andar ou área."
        label="Nome do grupo"
        placeholder="Ex: Matriz, Filial SP..."
        initialValue={createInitialValue}
        onSave={(name) => {
          setExtraGroups((prev) => [...prev, name]);
          set("group", name);
        }}
      />
    </Sheet>
  );
}

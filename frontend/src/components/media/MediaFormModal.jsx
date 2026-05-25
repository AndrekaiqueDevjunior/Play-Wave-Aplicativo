import React, { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { AudioPolicySelector } from "@/components/shared/AudioPolicySelector";
import { recomputarDeteccaoAudio, listarVersoesMidia } from "@/api/midias";
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
import { Loader2, Upload, X, Image, Film, Link2, Music, History } from "lucide-react";
import { substituirArquivoMidia, uploadMidia } from "@/api/midias";
import { detectUrlMediaType } from "@/utils/mediaUtils";

const DEFAULT_FORM = {
  name: "",
  description: "",
  type: "image",
  file_url: "",
  duration: 10,
  duration_seconds: null,
  display_duration_seconds: "",
  starts_at: "",
  ends_at: "",
  tags: "",
  notes: "",
  category: "",
  is_active: true,
  audio_policy: null,  // SPEC 005
  has_audio: null,     // SPEC 005
};

// image precisa de tempo de exibição. video/audio tocam até o fim natural
// do arquivo (onEnded dispara o avanço) — duration manual é descartada
// para esses tipos. external_url (link/iframe) usa duration como tempo.
const TYPES_USING_DURATION = new Set(["image", "external_url"]);

export default function MediaFormModal({ open, onClose, onSave, onUploaded, media }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [mode, setMode] = useState("upload"); // upload | url
  const fileRef = useRef(null);

  const { data: versions = [] } = useQuery({
    queryKey: ["media-versions", media?.id],
    queryFn: () => listarVersoesMidia(media.id),
    enabled: !!media?.id && open,
  });

  useEffect(() => {
    if (media) {
      setForm({
        name: media.name || "",
        description: media.description || "",
        type: media.type || "image",
        file_url: media.file_url || "",
        duration: media.duration || media.display_duration_seconds || 10,
        duration_seconds: media.duration_seconds || null,
        display_duration_seconds: media.display_duration_seconds || "",
        starts_at: media.starts_at ? media.starts_at.slice(0, 10) : "",
        ends_at: media.ends_at ? media.ends_at.slice(0, 10) : "",
        tags: (media.tags || []).join(", "),
        notes: media.notes || "",
        category: media.category || "",
        is_active: media.is_active !== false,
        audio_policy: media.audio_policy || null,  // SPEC 005
        has_audio: media.has_audio ?? null,         // SPEC 005
      });
      setMode(media.type === "external_url" ? "url" : "upload");
    } else {
      setForm(DEFAULT_FORM);
      setFile(null);
      setMode("upload");
    }
  }, [media, open]);

  const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));

  const ALLOWED_MIMES = [
    "image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif", "image/svg+xml",
    "video/mp4", "video/webm", "video/quicktime", "video/x-matroska", "video/x-msvideo", "video/avi",
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/m4a", "audio/x-m4a",
  ];

  const handleFile = (f) => {
    const MAX = 500 * 1024 * 1024;
    if (f.size > MAX) {
      alert("Arquivo maior que 500MB");
      return;
    }
    if (!ALLOWED_MIMES.includes(f.type)) {
      alert(`Tipo de arquivo não permitido: ${f.type}`);
      return;
    }
    setFile(f);
    if (!form.name) set("name", f.name.replace(/\.[^/.]+$/, ""));
    set(
      "type",
      f.type.startsWith("video") ? "video"
        : f.type.startsWith("audio") ? "audio"
        : "image",
    );
    set("mime_type", f.type);
  };

  const handleUrlChange = (url) => {
    set("file_url", url);
    if (!url) return;
    const detected = detectUrlMediaType(url);
    if (detected === "youtube" || detected === "vimeo") {
      set("type", "external_url");
    } else if (detected !== "external_url") {
      set("type", detected);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const tags = form.tags
        ? form.tags.split(",").map((t) => t.trim()).filter(Boolean)
        : [];
      const usesDuration = TYPES_USING_DURATION.has(form.type);
      const customDuration = Number(form.display_duration_seconds) || null;
      const durationValue = usesDuration ? Number(form.duration) || customDuration || null : customDuration;

      // ── Caminho UPLOAD: cria via /media/upload com TODOS os campos ─────
      // (antes o modal criava o registro via upload e DEPOIS chamava onSave,
      //  que criava um SEGUNDO registro via /media — gerando duplicatas.)
      if (file && mode === "upload" && !media) {
        setUploading(true);
        try {
          const uploaded = await uploadMidia(file, {
            name: form.name,
            type: form.type,
            description: form.description || undefined,
            category: form.category || undefined,
            tags: tags.length ? tags.join(",") : undefined,
            duration: durationValue,
            display_duration_seconds: durationValue,
            starts_at: form.starts_at || undefined,
            ends_at: form.ends_at || undefined,
            notes: form.notes || undefined,
          });
          if (onUploaded) onUploaded(uploaded);
        } finally {
          setUploading(false);
        }
        return;
      }

      // ── Caminho URL EXTERNA ou EDIT: chama onSave ──────────────────────
      await onSave({
        name: form.name,
        description: form.description,
        type: form.type,
        file_url: form.file_url,
        thumbnail_url: form.file_url,
        duration: durationValue,
        display_duration_seconds: durationValue,
        starts_at: form.starts_at || null,
        ends_at: form.ends_at || null,
        file_size: media?.file_size || 0,
        tags,
        notes: form.notes,
        category: form.category,
        is_active: form.is_active,
        status: "available",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{media ? "Editar Mídia" : "Nova Mídia"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          {!media && (
            <div className="flex gap-2">
              <Button
                type="button"
                variant={mode === "upload" ? "default" : "outline"}
                size="sm"
                onClick={() => setMode("upload")}
              >
                <Upload className="w-4 h-4 mr-1.5" />
                Upload
              </Button>
              <Button
                type="button"
                variant={mode === "url" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setMode("url");
                  set("type", "external_url");
                }}
              >
                <Link2 className="w-4 h-4 mr-1.5" />
                URL externa
              </Button>
            </div>
          )}

          {mode === "upload" && !media && (
            <div>
              {!file ? (
                <div
                  onClick={() => fileRef.current?.click()}
                  className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer hover:border-primary/50 transition-colors"
                >
                  <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm font-medium">
                    Clique ou arraste o arquivo
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    JPG, PNG, WEBP, GIF, SVG, MP4, WEBM, MOV, MP3, WAV, OGG, M4A · Máx 500MB
                  </p>
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/*,video/mp4,video/webm,video/quicktime,video/x-matroska,audio/mpeg,audio/wav,audio/ogg,audio/m4a"
                    className="hidden"
                    onChange={(e) =>
                      e.target.files[0] && handleFile(e.target.files[0])
                    }
                  />
                </div>
              ) : (
                <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                  <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                    {form.type === "video" ? (
                      <Film className="w-4 h-4 text-primary" />
                    ) : form.type === "audio" ? (
                      <Music className="w-4 h-4 text-primary" />
                    ) : (
                      <Image className="w-4 h-4 text-primary" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1048576).toFixed(1)} MB
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    type="button"
                    onClick={() => setFile(null)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>
          )}

          {media && (
            <div className="space-y-2 rounded-md border p-3">
              <Label>Substituir arquivo</Label>
              <Input
                type="file"
                accept="image/*,video/mp4,video/webm,video/quicktime,video/x-matroska,audio/mpeg,audio/wav,audio/ogg,audio/m4a"
                onChange={async (event) => {
                  const selected = event.target.files?.[0];
                  if (!selected) return;
                  setUploading(true);
                  try {
                    const updated = await substituirArquivoMidia(media.id, selected);
                    if (onUploaded) onUploaded(updated);
                  } finally {
                    setUploading(false);
                    event.target.value = "";
                  }
                }}
              />
              <p className="text-xs text-muted-foreground">
                Mantém o mesmo cadastro e os vínculos com campanhas, mas gera nova versão para o player baixar.
              </p>
            </div>
          )}

          {versions.length > 0 && (
            <div className="space-y-2 rounded-md border p-3">
              <div className="flex items-center gap-2 text-sm font-medium">
                <History className="w-4 h-4 text-muted-foreground" />
                Histórico de versões
              </div>
              <div className="divide-y text-xs">
                {versions.map((v) => (
                  <div key={v.id} className="flex items-center justify-between py-1.5 gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-1.5 py-0.5 rounded font-mono ${v.is_current ? "bg-green-100 text-green-700" : "bg-muted text-muted-foreground"}`}>
                        v{v.version_number}
                      </span>
                      {v.duration_seconds && (
                        <span className="text-muted-foreground">{v.duration_seconds}s</span>
                      )}
                      {v.file_hash && (
                        <span className="text-muted-foreground font-mono">{v.file_hash.slice(0, 8)}</span>
                      )}
                    </div>
                    <span className="text-muted-foreground shrink-0">
                      {new Date(v.created_at).toLocaleDateString("pt-BR")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {mode === "url" && (
            <div className="space-y-2">
              <Label>URL do arquivo</Label>
              <Input
                value={form.file_url}
                onChange={(e) => handleUrlChange(e.target.value)}
                placeholder="https:// · YouTube · Vimeo · imagem · vídeo..."
                required={mode === "url"}
              />
              {form.file_url && (
                <p className="text-xs text-muted-foreground">
                  Tipo detectado: <span className="font-medium">{detectUrlMediaType(form.file_url)}</span>
                </p>
              )}
            </div>
          )}

          <div className="space-y-2">
            <Label>Nome *</Label>
            <Input
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Descrição</Label>
            <Textarea
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
              rows={2}
              placeholder="Descrição opcional..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Tipo</Label>
              <Select value={form.type} onValueChange={(v) => set("type", v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="image">Imagem</SelectItem>
                  <SelectItem value="video">Vídeo</SelectItem>
                  <SelectItem value="audio">Áudio</SelectItem>
                  <SelectItem value="external_url">URL externa</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {TYPES_USING_DURATION.has(form.type) ? (
              <div className="space-y-2">
                <Label>Duração (s)</Label>
                <Input
                  type="number"
                  min="1"
                  value={form.duration}
                  onChange={(e) => {
                    set("duration", e.target.value);
                    set("display_duration_seconds", e.target.value);
                  }}
                />
                <p className="text-xs text-muted-foreground">
                  Tempo de exibição em tela.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Duração</Label>
                <div className="h-10 px-3 rounded-md border border-input bg-muted/40 flex items-center text-sm text-muted-foreground">
                  {form.duration_seconds ? `Detectada: ${form.duration_seconds}s` : "Até o fim do arquivo"}
                </div>
                <p className="text-xs text-muted-foreground">
                  Reprodução padrão até o fim do arquivo. Use duração personalizada só para cortar antes.
                </p>
              </div>
            )}
          </div>
          {!TYPES_USING_DURATION.has(form.type) && (
            <div className="space-y-2">
              <Label>Duração personalizada opcional (s)</Label>
              <Input
                type="number"
                min="1"
                value={form.display_duration_seconds}
                onChange={(e) => set("display_duration_seconds", e.target.value)}
                placeholder="Ex: 30"
              />
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Início de exibição</Label>
              <Input
                type="date"
                value={form.starts_at}
                onChange={(e) => set("starts_at", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Fim de exibição</Label>
              <Input
                type="date"
                value={form.ends_at}
                onChange={(e) => set("ends_at", e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Categoria</Label>
              <Input
                value={form.category}
                onChange={(e) => set("category", e.target.value)}
                placeholder="Ex: Promoções"
              />
            </div>
            <div className="space-y-2">
              <Label>Tags</Label>
              <Input
                value={form.tags}
                onChange={(e) => set("tags", e.target.value)}
                placeholder="tag1, tag2"
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Observações</Label>
            <Textarea
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              rows={2}
              placeholder="Anotações..."
            />
          </div>

          {/* SPEC 005 — política de áudio */}
          <div className="border-t pt-4 space-y-3">
            <AudioPolicySelector
              value={form.audio_policy}
              onChange={(v) => set("audio_policy", v)}
              allowNull
              inheritedLabel="Usar política da campanha"
            />

            {form.type === "video" && (
              <div className="p-3 bg-gray-50 rounded-lg text-sm space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-gray-700">
                    Áudio nativo:{" "}
                    <span className="font-medium">
                      {form.has_audio === null
                        ? "não detectado"
                        : form.has_audio
                          ? "presente"
                          : "ausente"}
                    </span>
                  </span>
                  {media?.id && (
                    <button
                      type="button"
                      className="text-blue-600 hover:underline text-xs"
                      onClick={async () => {
                        try {
                          const res = await recomputarDeteccaoAudio(media.id);
                          set("has_audio", res.has_audio);
                        } catch {
                          /* silencioso */
                        }
                      }}
                    >
                      Recalcular
                    </button>
                  )}
                </div>
                {form.has_audio === null && (
                  <p className="text-xs text-amber-600">
                    Esta mídia ainda não foi analisada. Salve e clique em
                    "Recalcular" para detectar automaticamente.
                  </p>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={
                saving || uploading || (!file && !form.file_url && !media)
              }
            >
              {(saving || uploading) && (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              )}
              {uploading
                ? "Enviando..."
                : saving
                  ? "Salvando..."
                  : media
                    ? "Salvar"
                    : "Adicionar"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

import React, { useState, useEffect, useRef } from "react";
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
import { Loader2, Upload, X, Image, Film, Link2, Music } from "lucide-react";
import { uploadMidia } from "@/api/midias";

const DEFAULT_FORM = {
  name: "",
  description: "",
  type: "image",
  file_url: "",
  duration: 10,
  tags: "",
  notes: "",
  category: "",
};

export default function MediaFormModal({ open, onClose, onSave, media }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [mode, setMode] = useState("upload"); // upload | url
  const fileRef = useRef(null);

  useEffect(() => {
    if (media) {
      setForm({
        name: media.name || "",
        description: media.description || "",
        type: media.type || "image",
        file_url: media.file_url || "",
        duration: media.duration || 10,
        tags: (media.tags || []).join(", "),
        notes: media.notes || "",
        category: media.category || "",
      });
      setMode(media.type === "external_url" ? "url" : "upload");
    } else {
      setForm(DEFAULT_FORM);
      setFile(null);
      setMode("upload");
    }
  }, [media, open]);

  const set = (k, v) => setForm((prev) => ({ ...prev, [k]: v }));

  const handleFile = (f) => {
    const MAX = 100 * 1024 * 1024;
    if (f.size > MAX) {
      alert("Arquivo maior que 100MB");
      return;
    }
    const allowed = [
      "image/jpeg",
      "image/png",
      "image/webp",
      "video/mp4",
      "audio/mpeg",
      "audio/wav",
    ];
    if (!allowed.includes(f.type)) {
      alert("Tipo de arquivo não permitido");
      return;
    }
    setFile(f);
    if (!form.name) set("name", f.name.replace(/\.[^/.]+$/, ""));
    set(
      "type",
      f.type.startsWith("video")
        ? "video"
        : f.type.startsWith("audio")
          ? "audio"
          : "image",
    );
    set("mime_type", f.type);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    let file_url = form.file_url;
    let file_size = media?.file_size || 0;

    if (file && mode === "upload") {
      setUploading(true);
      const uploaded = await uploadMidia(file, { name: form.name, type: form.type });
      file_url = uploaded?.file_url || "";
      file_size = file.size;
      setUploading(false);
    }

    const tags = form.tags
      ? form.tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean)
      : [];
    await onSave({
      name: form.name,
      description: form.description,
      type: form.type,
      file_url,
      thumbnail_url: file_url,
      duration: Number(form.duration),
      file_size,
      tags,
      notes: form.notes,
      category: form.category,
      status: "available",
    });
    setSaving(false);
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
                    JPG, PNG, WEBP, MP4, MP3 · Máx 100MB
                  </p>
                  <input
                    ref={fileRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp,video/mp4,audio/mpeg,audio/wav"
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

          {mode === "url" && (
            <div className="space-y-2">
              <Label>URL do arquivo</Label>
              <Input
                value={form.file_url}
                onChange={(e) => set("file_url", e.target.value)}
                placeholder="https://..."
                required={mode === "url"}
              />
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
            <div className="space-y-2">
              <Label>Duração (s)</Label>
              <Input
                type="number"
                min="1"
                value={form.duration}
                onChange={(e) => set("duration", e.target.value)}
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

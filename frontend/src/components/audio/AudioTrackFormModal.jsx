import React, { useState, useEffect } from "react";
import { base44 } from "@/api/base44Client";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
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
import { Upload, Music, Loader2 } from "lucide-react";

const CATEGORY_LABELS = {
  music: "Música",
  jingle: "Jingle",
  announcement: "Anúncio",
  ambient: "Ambiente",
  other: "Outro",
};

const MAX_SIZE_MB = 50;

export default function AudioTrackFormModal({ track, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "music",
    status: "active",
    notes: "",
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (track) {
      setForm({
        name: track.name || "",
        description: track.description || "",
        category: track.category || "music",
        status: track.status || "active",
        notes: track.notes || "",
      });
    }
  }, [track]);

  function handleFile(e) {
    const f = e.target.files[0];
    if (!f) return;
    if (!f.type.includes("audio")) {
      setError("Apenas arquivos de áudio são permitidos.");
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Arquivo muito grande. Máximo: ${MAX_SIZE_MB}MB`);
      return;
    }
    setError("");
    setFile(f);
    if (!form.name)
      setForm((prev) => ({ ...prev, name: f.name.replace(/\.[^.]+$/, "") }));
  }

  async function handleSave() {
    if (!form.name.trim()) {
      setError("Nome obrigatório.");
      return;
    }
    if (!track && !file) {
      setError("Selecione um arquivo MP3.");
      return;
    }

    setLoading(true);
    setError("");

    let fileData = {};

    if (file) {
      const { file_url } = await base44.integrations.Core.UploadFile({ file });
      // Tenta extrair duração via Audio API
      const duration_seconds = await new Promise((resolve) => {
        const a = new Audio();
        a.src = URL.createObjectURL(file);
        a.onloadedmetadata = () => resolve(Math.round(a.duration));
        a.onerror = () => resolve(null);
      });

      fileData = {
        file_url,
        mime_type: file.type,
        file_size: file.size,
        duration_seconds,
      };
    }

    const data = { ...form, ...fileData };

    if (track) {
      await base44.entities.AudioTrack.update(track.id, data);
    } else {
      await base44.entities.AudioTrack.create(data);
    }

    setLoading(false);
    onSaved();
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {track ? "Editar Faixa" : "Upload de Áudio"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Upload */}
          {!track && (
            <div>
              <Label>Arquivo MP3 *</Label>
              <label className="mt-1.5 flex flex-col items-center justify-center gap-2 border-2 border-dashed border-border rounded-lg p-6 cursor-pointer hover:border-primary transition-colors">
                <Music className="w-8 h-8 text-muted-foreground" />
                {file ? (
                  <span className="text-sm font-medium text-foreground">
                    {file.name}
                  </span>
                ) : (
                  <span className="text-sm text-muted-foreground">
                    Clique para selecionar MP3 (máx. {MAX_SIZE_MB}MB)
                  </span>
                )}
                <input
                  type="file"
                  accept="audio/*"
                  className="hidden"
                  onChange={handleFile}
                />
              </label>
            </div>
          )}

          <div>
            <Label>Nome *</Label>
            <Input
              className="mt-1.5"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: Música ambiente 1"
            />
          </div>

          <div>
            <Label>Descrição</Label>
            <Textarea
              className="mt-1.5"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Categoria</Label>
              <Select
                value={form.category}
                onValueChange={(v) => setForm({ ...form, category: v })}
              >
                <SelectTrigger className="mt-1.5">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CATEGORY_LABELS).map(([v, l]) => (
                    <SelectItem key={v} value={v}>
                      {l}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setForm({ ...form, status: v })}
              >
                <SelectTrigger className="mt-1.5">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Ativo</SelectItem>
                  <SelectItem value="inactive">Inativo</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                {track ? "Salvar" : "Fazer Upload"}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

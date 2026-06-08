import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { uploadFaixa, atualizarFaixa, listarCategoriasAudio } from "@/api/audio";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Upload, Music, Loader2, FileAudio } from "lucide-react";

const MAX_SIZE_MB = 100;

const ACCEPTED_TYPES = [
  "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
  "audio/wave", "audio/ogg", "audio/opus", "audio/m4a",
  "audio/x-m4a", "audio/mp4", "audio/aac", "audio/flac",
  "audio/webm", "audio/x-flac",
  "video/mpeg",
];

const AUDIO_EXTENSIONS = /\.(mp3|wav|ogg|opus|m4a|aac|flac|weba|mp4|mpeg|mpg)$/i;

const ACCEPT_ATTR = [
  ".mp3", ".wav", ".ogg", ".opus", ".m4a", ".aac",
  ".flac", ".weba", ".mp4", ".mpeg", ".mpg",
  ...ACCEPTED_TYPES,
].join(",");

const FORMAT_DESC = "MP3, MPEG, WAV, OGG, OPUS (WhatsApp), M4A, AAC, FLAC · máx. 100 MB";

export default function AudioTrackFormModal({ track, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "music",
    category_id: null,
    status: "active",
    notes: "",
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { data: categories = [] } = useQuery({
    queryKey: ["audio-categories"],
    queryFn: () => listarCategoriasAudio(),
  });

  useEffect(() => {
    if (track) {
      setForm({
        name: track.name || "",
        description: track.description || "",
        category: track.category || "music",
        category_id: track.category_id || null,
        status: track.status || "active",
        notes: track.notes || "",
      });
    }
  }, [track]);

  // Valor combinado do select: custom:<id> (categoria personalizada) ou
  // default:<slug> (categoria padrão).
  const selectedCategoryValue = form.category_id
    ? `custom:${form.category_id}`
    : `default:${form.category}`;

  function handleCategoryChange(value) {
    if (value.startsWith("custom:")) {
      setForm((prev) => ({ ...prev, category_id: value.slice(7) }));
    } else {
      setForm((prev) => ({
        ...prev,
        category: value.slice(8),
        category_id: null,
      }));
    }
  }

  function handleFile(e) {
    const f = e.target.files[0];
    if (!f) return;
    const isAudio =
      f.type.startsWith("audio/") ||
      ACCEPTED_TYPES.includes(f.type) ||
      AUDIO_EXTENSIONS.test(f.name);
    if (!isAudio) {
      setError("Formato não suportado. Use: MP3, MPEG, WAV, OGG, OPUS, M4A, AAC ou FLAC.");
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Arquivo muito grande. Máximo: ${MAX_SIZE_MB} MB`);
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
      setError("Selecione um arquivo de áudio.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      if (track) {
        await atualizarFaixa(track.id, form);
      } else {
        const duration_seconds = await new Promise((resolve) => {
          const a = new Audio();
          a.src = URL.createObjectURL(file);
          a.onloadedmetadata = () => resolve(Math.round(a.duration));
          a.onerror = () => resolve(null);
        });
        await uploadFaixa(file, {
          ...form,
          duration_seconds,
          mime_type: file.type,
          file_size: file.size,
        });
      }

      onSaved();
    } catch (err) {
      setError(err?.message || "Erro ao salvar faixa de áudio.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Sheet open onOpenChange={onClose}>
      <SheetContent side="right" className="w-full sm:max-w-[480px] flex flex-col p-0 overflow-y-auto">
        <SheetHeader className="px-6 pt-6 pb-4 border-b">
          <SheetTitle className="flex items-center gap-2 text-base">
            <FileAudio className="w-4 h-4 text-primary" />
            {track ? "Editar Faixa" : "Upload de Áudio"}
          </SheetTitle>
          <SheetDescription className="text-xs">
            {track
              ? "Edite as informações da faixa de áudio."
              : "Envie arquivos de áudio para o Rádio Indoor."}
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {/* Upload */}
          {!track && (
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Arquivo de Áudio *
              </Label>
              <label className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-border rounded-xl p-8 cursor-pointer hover:border-primary hover:bg-primary/5 transition-colors">
                {file ? (
                  <>
                    <Music className="w-8 h-8 text-primary" />
                    <div className="text-center">
                      <p className="text-sm font-medium text-foreground">{file.name}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {(file.size / (1024 * 1024)).toFixed(1)} MB · {file.type || "áudio"}
                      </p>
                    </div>
                    <span className="text-xs text-primary underline">Trocar arquivo</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-8 h-8 text-muted-foreground" />
                    <div className="text-center">
                      <p className="text-sm font-medium">Arraste ou clique para selecionar</p>
                      <p className="text-xs text-muted-foreground mt-1">{FORMAT_DESC}</p>
                    </div>
                  </>
                )}
                <input
                  type="file"
                  accept={ACCEPT_ATTR}
                  className="hidden"
                  onChange={handleFile}
                />
              </label>
            </div>
          )}

          <Separator />

          <div className="space-y-1.5">
            <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Nome *</Label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: Música ambiente 1"
            />
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Descrição</Label>
            <Textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
              className="resize-none text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Categoria</Label>
              <Select
                value={selectedCategoryValue}
                onValueChange={handleCategoryChange}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories
                    .filter((c) => c.is_default)
                    .map((c) => (
                      <SelectItem key={c.slug} value={`default:${c.slug}`}>
                        {c.name}
                      </SelectItem>
                    ))}
                  {categories
                    .filter((c) => !c.is_default)
                    .map((c) => (
                      <SelectItem key={c.id} value={`custom:${c.id}`}>
                        {c.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setForm({ ...form, status: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Ativo</SelectItem>
                  <SelectItem value="inactive">Inativo</SelectItem>
                  <SelectItem value="archived">Arquivado</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <SheetFooter className="px-6 py-4 border-t bg-muted/30 flex-row gap-2">
          <Button type="button" variant="outline" onClick={onClose} className="flex-1">
            Cancelar
          </Button>
          <Button onClick={handleSave} disabled={loading} className="flex-1">
            {loading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Salvando...</>
            ) : (
              <><Upload className="w-4 h-4 mr-2" />{track ? "Salvar" : "Fazer Upload"}</>
            )}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

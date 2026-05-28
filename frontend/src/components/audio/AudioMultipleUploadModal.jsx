import React, { useState, useRef } from "react";
import { uploadMultipleFaixas } from "@/api/audio";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Upload, 
  Music, 
  Loader2, 
  FileAudio, 
  X, 
  CheckCircle2, 
  AlertCircle,
  Trash2 
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

const CATEGORY_LABELS = {
  music: "Música",
  jingle: "Jingle",
  announcement: "Anúncio",
  ambient: "Ambiente",
  other: "Outro",
};

const MAX_SIZE_MB = 100;

const ACCEPTED_TYPES = [
  "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
  "audio/wave", "audio/ogg", "audio/opus", "audio/m4a",
  "audio/x-m4a", "audio/mp4", "audio/aac", "audio/flac",
  "audio/webm", "audio/x-flac",
];

const AUDIO_EXTENSIONS = /\.(mp3|wav|ogg|opus|m4a|aac|flac|weba|mp4|mpeg|mpg)$/i;

const ACCEPT_ATTR = [
  ".mp3", ".wav", ".ogg", ".opus", ".m4a", ".aac",
  ".flac", ".weba", ".mp4", ".mpeg", ".mpg",
  ...ACCEPTED_TYPES,
].join(",");

const FORMAT_DESC = "MP3, MPEG, WAV, OGG, OPUS, M4A, AAC, FLAC · máx. 100 MB cada";

export default function AudioMultipleUploadModal({ onClose, onSaved }) {
  const [files, setFiles] = useState([]);
  const [category, setCategory] = useState("music");
  const [status, setStatus] = useState("active");
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const dropped = e.dataTransfer.files;
    if (dropped?.length) processFileList(dropped);
  }

  function handleFiles(e) {
    if (e.target.files?.length) processFileList(e.target.files);
  }

  function processFileList(fileList) {
    const selectedFiles = Array.from(fileList);
    const validFiles = [];
    const errors = [];

    selectedFiles.forEach(f => {
      const isAudio =
        f.type.startsWith("audio/") ||
        ACCEPTED_TYPES.includes(f.type) ||
        AUDIO_EXTENSIONS.test(f.name);
      
      if (!isAudio) {
        errors.push(`${f.name}: Formato não suportado`);
        return;
      }
      
      if (f.size > MAX_SIZE_MB * 1024 * 1024) {
        errors.push(`${f.name}: Arquivo muito grande (máx. ${MAX_SIZE_MB} MB)`);
        return;
      }
      
      validFiles.push(f);
    });

    if (errors.length > 0) {
      setError(errors.join("\n"));
    } else {
      setError("");
    }

    setFiles(prev => [...prev, ...validFiles]);
  }

  function removeFile(index) {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }

  function formatSize(bytes) {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  async function handleUpload() {
    if (files.length === 0) {
      setError("Selecione pelo menos um arquivo.");
      return;
    }

    setLoading(true);
    setError("");
    setUploadProgress(0);

    try {
      const formData = new FormData();
      
      files.forEach(file => {
        formData.append('files', file);
      });
      
      formData.append('category', category);
      formData.append('status', status);

      // Simular progresso (o backend não retorna progresso real)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await uploadMultipleFaixas(formData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setResults(result);

      // Se todos foram sucesso, fechar após 2 segundos
      if (!result.errors || result.errors.length === 0) {
        setTimeout(() => {
          onSaved();
        }, 2000);
      }
    } catch (err) {
      setError(err?.message || "Erro ao fazer upload dos arquivos.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Sheet open onOpenChange={onClose}>
      <SheetContent 
        side="right" 
        className="w-full sm:max-w-[600px] flex flex-col p-0 overflow-y-auto"
      >
        <SheetHeader className="px-6 pt-6 pb-4 border-b">
          <SheetTitle className="flex items-center gap-2 text-base">
            <FileAudio className="w-4 h-4 text-primary" />
            Upload Múltiplo de Áudios
          </SheetTitle>
          <SheetDescription className="text-xs">
            Envie vários arquivos de áudio de uma vez para o Rádio Indoor.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {/* Upload Area */}
          {!results && (
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Arquivos de Áudio *
              </Label>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => !loading && fileInputRef.current?.click()}
                className={`flex flex-col items-center justify-center gap-3 border-2 border-dashed rounded-xl p-8 cursor-pointer transition-colors ${
                  dragActive
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary hover:bg-primary/5"
                }`}
              >
                <Upload className={`w-8 h-8 ${dragActive ? "text-primary" : "text-muted-foreground"}`} />
                <div className="text-center">
                  <p className="text-sm font-medium">
                    Arraste ou clique para selecionar múltiplos arquivos
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">{FORMAT_DESC}</p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPT_ATTR}
                  multiple
                  className="hidden"
                  onChange={handleFiles}
                  disabled={loading}
                />
              </div>
            </div>
          )}

          {/* File List */}
          {files.length > 0 && !results && (
            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Arquivos Selecionados ({files.length})
              </Label>
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 border rounded-lg bg-card"
                  >
                    <Music className="w-4 h-4 text-primary flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatSize(file.size)} · {file.type || "áudio"}
                      </p>
                    </div>
                    {!loading && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="flex-shrink-0"
                        onClick={() => removeFile(index)}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Settings */}
          {files.length > 0 && !results && (
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Categoria Padrão</Label>
                <Select value={category} onValueChange={setCategory} disabled={loading}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(CATEGORY_LABELS).map(([v, l]) => (
                      <SelectItem key={v} value={v}>{l}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-muted-foreground">Status Padrão</Label>
                <Select value={status} onValueChange={setStatus} disabled={loading}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Ativo</SelectItem>
                    <SelectItem value="inactive">Inativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Upload Progress */}
          {loading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Fazendo upload...</span>
                <span className="font-medium">{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <h3 className="font-semibold">Upload Concluído</h3>
              </div>

              {results.uploaded && results.uploaded.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs font-semibold uppercase tracking-wide text-emerald-600">
                    Sucesso ({results.uploaded.length})
                  </Label>
                  <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {results.uploaded.map((track, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-2 p-2 rounded bg-emerald-50 dark:bg-emerald-950/20"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        <span className="text-sm truncate">{track.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {results.errors && results.errors.length > 0 && (
                <div className="space-y-2">
                  <Label className="text-xs font-semibold uppercase tracking-wide text-destructive">
                    Erros ({results.errors.length})
                  </Label>
                  <div className="space-y-1 max-h-[200px] overflow-y-auto">
                    {results.errors.map((err, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-2 p-2 rounded bg-destructive/10"
                      >
                        <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium">{err.filename}</p>
                          <p className="text-xs text-muted-foreground">{err.error}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive whitespace-pre-line">{error}</p>
            </div>
          )}
        </div>

        <SheetFooter className="px-6 py-4 border-t bg-muted/30 flex-row gap-2">
          {!results ? (
            <>
              <Button 
                type="button" 
                variant="outline" 
                onClick={onClose} 
                className="flex-1"
                disabled={loading}
              >
                Cancelar
              </Button>
              <Button 
                onClick={handleUpload} 
                disabled={loading || files.length === 0} 
                className="flex-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Enviando {files.length} arquivo(s)...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Fazer Upload ({files.length})
                  </>
                )}
              </Button>
            </>
          ) : (
            <Button onClick={onSaved} className="flex-1">
              Concluir
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}

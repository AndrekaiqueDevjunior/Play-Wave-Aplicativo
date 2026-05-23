import React, { useState, useRef } from "react";
import { uploadMultipleTracksAPI } from "@/api/audio";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
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
  X,
  CheckCircle,
  AlertCircle,
  FileAudio,
} from "lucide-react";
import { cn } from "@/lib/utils";

const CATEGORY_OPTIONS = [
  { value: "music", label: "Música" },
  { value: "jingle", label: "Jingle" },
  { value: "announcement", label: "Anúncio" },
  { value: "ambient", label: "Ambiente" },
  { value: "other", label: "Outro" },
];

const ACCEPTED_TYPES = [
  "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
  "audio/wave", "audio/ogg", "audio/opus", "audio/m4a",
  "audio/x-m4a", "audio/mp4", "audio/aac", "audio/flac",
  "audio/webm", "audio/x-flac",
];

const MAX_FILES = 50;
const MAX_SIZE_MB = 100;

export default function MultiAudioUploadDialog({ open, onOpenChange, onSuccess }) {
  const [files, setFiles] = useState([]);
  const [category, setCategory] = useState("music");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [results, setResults] = useState(null);
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const dropped = Array.from(e.dataTransfer.files);
    addFiles(dropped);
  };

  const handleFileInput = (e) => {
    const selected = Array.from(e.target.files || []);
    addFiles(selected);
  };

  const addFiles = (newFiles) => {
    const validFiles = newFiles.filter((f) => {
      if (!ACCEPTED_TYPES.includes(f.type)) {
        console.warn(`Tipo inválido: ${f.name} (${f.type})`);
        return false;
      }
      if (f.size > MAX_SIZE_MB * 1024 * 1024) {
        console.warn(`Arquivo muito grande: ${f.name}`);
        return false;
      }
      return true;
    });

    const updated = [...files, ...validFiles];
    if (updated.length > MAX_FILES) {
      alert(`Máximo ${MAX_FILES} arquivos por vez`);
      return;
    }

    setFiles(updated);
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert("Selecione pelo menos um arquivo");
      return;
    }

    setUploading(true);
    setUploadProgress({});

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });
      formData.append("category", category);

      const response = await uploadMultipleTracksAPI(formData);

      setResults({
        uploaded: response.uploaded || [],
        errors: response.errors || [],
      });

      if (response.uploaded && response.uploaded.length > 0) {
        onSuccess?.(response.uploaded);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setResults({
        uploaded: [],
        errors: [{ filename: "geral", error: error.message }],
      });
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading && !results) {
      setFiles([]);
      setCategory("music");
      onOpenChange?.(false);
    }
  };

  const handleReset = () => {
    setFiles([]);
    setCategory("music");
    setResults(null);
    onOpenChange?.(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Múltiplo de Áudio</DialogTitle>
          <DialogDescription>
            Envie várias faixas de uma vez. Máximo {MAX_FILES} arquivos, {MAX_SIZE_MB}MB cada.
          </DialogDescription>
        </DialogHeader>

        {!results ? (
          <div className="space-y-6 py-4">
            {/* Categoria */}
            <div className="space-y-2">
              <Label htmlFor="category">Categoria</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger id="category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Área de drag-drop */}
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={cn(
                "relative rounded-lg border-2 border-dashed p-8 transition-colors",
                dragActive
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-300 bg-gray-50 hover:border-gray-400"
              )}
            >
              <div className="flex flex-col items-center justify-center space-y-2">
                <Upload className="h-8 w-8 text-gray-400" />
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-700">
                    Arraste arquivos aqui ou clique para selecionar
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    MP3, WAV, OGG, M4A, FLAC e outros · máx. 100 MB cada
                  </p>
                </div>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept={ACCEPTED_TYPES.join(",")}
                onChange={handleFileInput}
                className="absolute inset-0 cursor-pointer opacity-0"
              />
            </div>

            {/* Lista de arquivos selecionados */}
            {files.length > 0 && (
              <div className="space-y-2">
                <Label>
                  Arquivos Selecionados ({files.length}/{MAX_FILES})
                </Label>
                <div className="space-y-2 max-h-60 overflow-y-auto border rounded-lg p-3">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <FileAudio className="h-4 w-4 text-blue-500 flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium truncate">
                            {file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(file.size / 1024 / 1024).toFixed(1)} MB
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeFile(index)}
                        disabled={uploading}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Resultados */
          <div className="space-y-4 py-4">
            {results.uploaded.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <h3 className="font-medium">
                    Sucesso ({results.uploaded.length})
                  </h3>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {results.uploaded.map((track) => (
                    <p key={track.id} className="text-sm text-green-700 pl-7">
                      ✓ {track.name}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {results.errors && results.errors.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                  <h3 className="font-medium">
                    Erros ({results.errors.length})
                  </h3>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {results.errors.map((err, idx) => (
                    <p key={idx} className="text-sm text-red-700 pl-7">
                      ✗ {err.filename}: {err.error}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          {!results ? (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancelar
              </Button>
              <Button
                onClick={handleUpload}
                disabled={files.length === 0 || uploading}
              >
                {uploading && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Upload ({files.length})
              </Button>
            </>
          ) : (
            <Button onClick={handleReset}>Fechar</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

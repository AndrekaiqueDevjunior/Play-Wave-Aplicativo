import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Upload, Image, Film, X, CheckCircle2, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { uploadMidia } from "@/api/midias";

export default function MidiaUpload() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const fileRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [form, setForm] = useState({
    name: "",
    duration: 10,
    tags: "",
    notes: "",
  });
  const [saving, setSaving] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) handleFile(droppedFile);
  };

  const handleFile = (f) => {
    setFile(f);
    setForm((prev) => ({ ...prev, name: f.name.split(".")[0] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const tags = form.tags
      ? form.tags.split(",").map((t) => t.trim()).filter(Boolean)
      : [];
    await uploadMidia(file, {
      name: form.name,
      type: isVideo ? "video" : "image",
      // Vídeo: sem duration manual — toca até o fim natural do arquivo.
      duration: isVideo ? null : form.duration,
      notes: form.notes,
      tags: JSON.stringify(tags),
      status: "available",
    });
    toast({
      title: "Mídia enviada!",
      description: `${form.name} foi enviada com sucesso.`,
    });
    navigate("/midias");
  };

  const isVideo = file?.type?.startsWith("video");

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-bold">Upload de Mídia</h2>
        <p className="text-sm text-muted-foreground">
          Envie imagens e vídeos para sua biblioteca
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Arquivo</CardTitle>
        </CardHeader>
        <CardContent>
          {!file ? (
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragActive(true);
              }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
                dragActive
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50"
              }`}
            >
              <Upload className="w-10 h-10 mx-auto mb-3 text-muted-foreground" />
              <p className="text-sm font-medium">
                Arraste e solte aqui ou clique para selecionar
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                JPG, PNG, WEBP, MP4 · Máximo 100MB
              </p>
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,video/mp4"
                className="hidden"
                onChange={(e) =>
                  e.target.files[0] && handleFile(e.target.files[0])
                }
              />
            </div>
          ) : (
            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                {isVideo ? (
                  <Film className="w-5 h-5 text-primary" />
                ) : (
                  <Image className="w-5 h-5 text-primary" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(file.size / 1048576).toFixed(1)} MB ·{" "}
                  {isVideo ? "Vídeo" : "Imagem"}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setFile(null)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Informações</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Nome da Mídia</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            {!isVideo && (
              <div className="space-y-2">
                <Label>Duração padrão (segundos)</Label>
                <Input
                  type="number"
                  min="1"
                  value={form.duration}
                  onChange={(e) =>
                    setForm({ ...form, duration: parseInt(e.target.value) })
                  }
                />
                <p className="text-xs text-muted-foreground">
                  Tempo de exibição para imagens
                </p>
              </div>
            )}
            <div className="space-y-2">
              <Label>Tags</Label>
              <Input
                placeholder="Ex: promoção, abril, destaque"
                value={form.tags}
                onChange={(e) => setForm({ ...form, tags: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Observação</Label>
              <Textarea
                placeholder="Anotações sobre esta mídia..."
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/midias")}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={!file || saving}>
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    Enviar Mídia
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card className="bg-muted/50">
        <CardContent className="p-4">
          <p className="text-xs font-medium text-muted-foreground mb-2">
            Formatos aceitos
          </p>
          <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
            <div>Imagens: JPG, PNG, WEBP</div>
            <div>Vídeos: MP4</div>
            <div>Resolução recomendada: 1920x1080</div>
            <div>Tamanho máximo: 100MB</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

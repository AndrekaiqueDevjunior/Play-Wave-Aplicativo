import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  listarFaixas,
  criarPlaylistAudio,
  atualizarPlaylistAudio,
} from "@/api/audio";
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
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Music2, GripVertical, X, Plus, Loader2, Volume2 } from "lucide-react";
import AudioTrackSelector from "./AudioTrackSelector";

export default function AudioPlaylistFormModal({ playlist, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: "",
    description: "",
    status: "active",
    volume_default: 0.7,
    loop_enabled: true,
    shuffle_enabled: false,
    track_ids: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [draggingIdx, setDraggingIdx] = useState(null);

  const { data: allTracks = [], isLoading: tracksLoading } = useQuery({
    queryKey: ["audio-tracks"],
    queryFn: () => listarFaixas({ status: "active", limit: 1000 }),
  });

  useEffect(() => {
    if (playlist) {
      setForm({
        name: playlist.name || "",
        description: playlist.description || "",
        status: playlist.status || "active",
        volume_default: playlist.volume_default ?? 0.7,
        loop_enabled: playlist.loop_enabled ?? true,
        shuffle_enabled: playlist.shuffle_enabled ?? false,
        track_ids: playlist.track_ids || [],
      });
    }
  }, [playlist]);

  function addTrack(id) {
    if (!form.track_ids.includes(id)) {
      setForm((prev) => ({ ...prev, track_ids: [...prev.track_ids, id] }));
    }
  }

  function removeTrack(id) {
    setForm((prev) => ({
      ...prev,
      track_ids: prev.track_ids.filter((x) => x !== id),
    }));
  }

  function handleDragStart(idx) {
    setDraggingIdx(idx);
  }
  function handleDragOver(e, idx) {
    e.preventDefault();
    if (draggingIdx === null || draggingIdx === idx) return;
    const ids = [...form.track_ids];
    const [moved] = ids.splice(draggingIdx, 1);
    ids.splice(idx, 0, moved);
    setDraggingIdx(idx);
    setForm((prev) => ({ ...prev, track_ids: ids }));
  }
  function handleDragEnd() {
    setDraggingIdx(null);
  }

  async function handleSave() {
    if (!form.name.trim()) {
      setError("Nome obrigatório.");
      return;
    }
    setLoading(true);
    setError("");
    if (playlist) {
      await atualizarPlaylistAudio(playlist.id, form);
    } else {
      await criarPlaylistAudio(form);
    }
    setLoading(false);
    onSaved();
  }

  const orderedTracks = form.track_ids
    .map((id) => allTracks.find((t) => t.id === id))
    .filter(Boolean);
  const availableToAdd = allTracks.filter(
    (t) => !form.track_ids.includes(t.id),
  );

  const categoryLabels = {
    music: "Música",
    jingle: "Jingle",
    announcement: "Anúncio",
    ambient: "Ambiente",
    other: "Outro",
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl w-[90vw] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {playlist ? "Editar Playlist" : "Nova Playlist Sonora"}
          </DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="info">
          <TabsList className="w-full">
            <TabsTrigger value="info" className="flex-1">
              Informações
            </TabsTrigger>
            <TabsTrigger value="tracks" className="flex-1">
              Faixas ({form.track_ids.length})
            </TabsTrigger>
          </TabsList>

          {/* ABA INFO */}
          <TabsContent value="info" className="space-y-4 mt-4">
            <div>
              <Label>Nome *</Label>
              <Input
                className="mt-1.5"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Ex: Rádio Indoor Loja Centro"
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

            <div>
              <Label className="flex items-center gap-2">
                <Volume2 className="w-4 h-4" />
                Volume padrão: {Math.round(form.volume_default * 100)}%
              </Label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={form.volume_default}
                onChange={(e) =>
                  setForm({
                    ...form,
                    volume_default: parseFloat(e.target.value),
                  })
                }
                className="mt-2 w-full accent-primary"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium text-sm">Loop</p>
                  <p className="text-xs text-muted-foreground">
                    Repetir ao terminar
                  </p>
                </div>
                <Switch
                  checked={form.loop_enabled}
                  onCheckedChange={(v) => setForm({ ...form, loop_enabled: v })}
                />
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium text-sm">Shuffle</p>
                  <p className="text-xs text-muted-foreground">
                    Ordem aleatória
                  </p>
                </div>
                <Switch
                  checked={form.shuffle_enabled}
                  onCheckedChange={(v) =>
                    setForm({ ...form, shuffle_enabled: v })
                  }
                />
              </div>
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
          </TabsContent>

          {/* ABA FAIXAS */}
          <TabsContent value="tracks" className="mt-4 space-y-4">
            {/* Seleção múltipla com checkbox */}
            <div>
              <Label>Selecionar faixas</Label>
              <p className="text-xs text-muted-foreground mb-2">
                Marque as faixas que farão parte desta playlist
              </p>
              <AudioTrackSelector
                tracks={allTracks}
                selectedIds={form.track_ids}
                onSelectionChange={(ids) => setForm((prev) => ({ ...prev, track_ids: ids }))}
                loading={tracksLoading}
                showCategory
                showDuration
              />
            </div>

            {/* Ordem das faixas */}
            <div>
              <Label>Ordem de reprodução</Label>
              {orderedTracks.length === 0 ? (
                <p className="mt-2 text-sm text-muted-foreground text-center py-6 border rounded-lg border-dashed">
                  Nenhuma faixa adicionada. Selecione acima.
                </p>
              ) : (
                <div className="mt-1.5 border rounded-lg divide-y">
                  {orderedTracks.map((track, idx) => (
                    <div
                      key={track.id}
                      draggable
                      onDragStart={() => handleDragStart(idx)}
                      onDragOver={(e) => handleDragOver(e, idx)}
                      onDragEnd={handleDragEnd}
                      className={`flex items-center gap-3 px-3 py-2.5 cursor-grab ${draggingIdx === idx ? "opacity-50 bg-accent" : ""}`}
                    >
                      <GripVertical className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <span className="w-5 text-xs text-muted-foreground text-center">
                        {idx + 1}
                      </span>
                      <Music2 className="w-4 h-4 text-primary flex-shrink-0" />
                      <span className="flex-1 text-sm font-medium truncate">
                        {track.name}
                      </span>
                      <Badge
                        variant="outline"
                        className="text-xs hidden sm:inline-flex"
                      >
                        {categoryLabels[track.category] || track.category}
                      </Badge>
                      <button
                        onClick={() => removeTrack(track.id)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        {error && <p className="text-sm text-destructive">{error}</p>}

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
              "Salvar Playlist"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

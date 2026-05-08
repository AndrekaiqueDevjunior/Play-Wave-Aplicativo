import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listarPlaylistsAudio,
  atualizarPlaylistAudio,
  listarFaixas,
} from "@/api/audio";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Plus,
  ListMusic,
  Edit2,
  Trash2,
  Search,
  Music2,
  Volume2,
  Repeat,
} from "lucide-react";
import AudioPlaylistFormModal from "@/components/audio/AudioPlaylistsFormModal";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import StatusBadge from "@/components/shared/StatusBadge";

export default function PlaylistsSonoras() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const { data: playlists = [], isLoading } = useQuery({
    queryKey: ["audio-playlists"],
    queryFn: () => listarPlaylistsAudio(),
  });

  const { data: tracks = [] } = useQuery({
    queryKey: ["audio-tracks"],
    queryFn: () => listarFaixas(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => atualizarPlaylistAudio(id, { status: "archived" }),
    onSuccess: () => {
      qc.invalidateQueries(["audio-playlists"]);
      setDeleteTarget(null);
    },
  });

  const filtered = playlists.filter(
    (p) => !search || p.name.toLowerCase().includes(search.toLowerCase()),
  );

  function handleEdit(pl) {
    setEditing(pl);
    setFormOpen(true);
  }
  function handleNew() {
    setEditing(null);
    setFormOpen(true);
  }

  function getTrackCount(pl) {
    return pl.track_ids?.length || 0;
  }

  function getTotalDuration(pl) {
    if (!pl.track_ids?.length) return "0:00";
    const total = pl.track_ids.reduce((acc, id) => {
      const t = tracks.find((x) => x.id === id);
      return acc + (t?.duration_seconds || 0);
    }, 0);
    const m = Math.floor(total / 60);
    const s = Math.floor(total % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Playlists Sonoras
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Crie e gerencie playlists de Rádio Indoor
          </p>
        </div>
        <Button onClick={handleNew}>
          <Plus className="w-4 h-4 mr-2" />
          Nova Playlist
        </Button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Buscar playlist..."
          className="pl-9"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <ListMusic className="w-12 h-12 text-muted-foreground mb-3" />
            <p className="font-medium text-muted-foreground">
              Nenhuma playlist criada
            </p>
            <Button className="mt-4" onClick={handleNew}>
              <Plus className="w-4 h-4 mr-2" />
              Nova Playlist
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((pl) => (
            <Card key={pl.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <ListMusic className="w-5 h-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <CardTitle className="text-base truncate">
                        {pl.name}
                      </CardTitle>
                      {pl.description && (
                        <p className="text-xs text-muted-foreground truncate mt-0.5">
                          {pl.description}
                        </p>
                      )}
                    </div>
                  </div>
                  <StatusBadge status={pl.status} />
                </div>
              </CardHeader>
              <CardContent className="pt-0 space-y-3">
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Music2 className="w-3.5 h-3.5" />
                    {getTrackCount(pl)} faixas
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Volume2 className="w-3.5 h-3.5" />
                    {Math.round((pl.volume_default ?? 0.7) * 100)}%
                  </span>
                  {pl.loop_enabled && (
                    <span className="flex items-center gap-1.5 text-primary">
                      <Repeat className="w-3.5 h-3.5" />
                      Loop
                    </span>
                  )}
                </div>
                <div className="text-xs text-muted-foreground">
                  Duração total: {getTotalDuration(pl)}
                </div>
                <div className="flex items-center gap-1 pt-1 border-t">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => handleEdit(pl)}
                  >
                    <Edit2 className="w-3.5 h-3.5 mr-1.5" />
                    Editar
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setDeleteTarget(pl)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {formOpen && (
        <AudioPlaylistFormModal
          playlist={editing}
          onClose={() => setFormOpen(false)}
          onSaved={() => {
            qc.invalidateQueries(["audio-playlists"]);
            setFormOpen(false);
          }}
        />
      )}
      {deleteTarget && (
        <ConfirmDialog
          title="Arquivar playlist"
          description={`Arquivar "${deleteTarget.name}"? Dispositivos vinculados não receberão mais áudio.`}
          confirmLabel="Arquivar"
          variant="destructive"
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
        />
      )}
    </div>
  );
}

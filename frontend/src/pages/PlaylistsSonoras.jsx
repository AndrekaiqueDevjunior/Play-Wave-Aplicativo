import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  listarPlaylistsAudio,
  atualizarPlaylistAudio,
  deletarPlaylistAudio,
  listarFaixas,
} from "@/api/audio";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Plus,
  ListMusic,
  Edit2,
  Trash2,
  Search,
  Music2,
  Volume2,
  Repeat,
  Settings2,
  CheckSquare,
  Square,
  X,
  Archive,
  ArchiveRestore,
} from "lucide-react";
import AudioPlaylistFormModal from "@/components/audio/AudioPlaylistsFormModal";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import StatusBadge from "@/components/shared/StatusBadge";
import { useToast } from "@/components/ui/use-toast";

export default function PlaylistsSonoras() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [archiveTarget, setArchiveTarget] = useState(null);
  const [hardDeleteTarget, setHardDeleteTarget] = useState(null);

  // Seleção múltipla
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);

  const { data: playlists = [], isLoading } = useQuery({
    queryKey: ["audio-playlists"],
    // include_archived=true — SPEC 017: por padrão o backend esconde
    // arquivadas (para não aparecerem em seletores de device/campanha), mas
    // esta é a tela de gerenciamento, onde o admin precisa ver/restaurar
    // arquivadas via o filtro de status abaixo.
    queryFn: () => listarPlaylistsAudio({ include_archived: true }),
  });

  const { data: tracks = [] } = useQuery({
    queryKey: ["audio-tracks"],
    queryFn: () => listarFaixas({ limit: 1000 }),
  });

  const archiveMutation = useMutation({
    mutationFn: (id) => atualizarPlaylistAudio(id, { status: "archived" }),
    onSuccess: () => {
      qc.invalidateQueries(["audio-playlists"]);
      setArchiveTarget(null);
      toast({ title: "Playlist arquivada." });
    },
    onError: (err) => {
      const msg =
        err?.detail ||
        err?.message ||
        (typeof err === "string" ? err : "Erro ao arquivar playlist.");
      toast({ title: "Erro ao arquivar", description: msg, variant: "destructive" });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (id) => atualizarPlaylistAudio(id, { status: "active" }),
    onSuccess: () => {
      qc.invalidateQueries(["audio-playlists"]);
      toast({ title: "Playlist restaurada." });
    },
    onError: (err) => {
      const msg =
        err?.detail ||
        err?.message ||
        (typeof err === "string" ? err : "Erro ao restaurar playlist.");
      toast({ title: "Erro ao restaurar", description: msg, variant: "destructive" });
    },
  });

  const hardDeleteMutation = useMutation({
    mutationFn: (id) => deletarPlaylistAudio(id),
    onSuccess: () => {
      qc.invalidateQueries(["audio-playlists"]);
      setHardDeleteTarget(null);
      toast({ title: "Playlist excluída definitivamente." });
    },
    onError: (err) => {
      // Backend retorna 409 com mensagem clara quando a playlist está
      // vinculada a um device/campanha — ver crud_audio_playlist.get_in_use_references.
      const msg =
        err?.detail ||
        err?.message ||
        (typeof err === "string" ? err : "Erro ao excluir playlist.");
      toast({ title: "Não foi possível excluir", description: msg, variant: "destructive" });
    },
  });

  const bulkArchiveMutation = useMutation({
    mutationFn: async (ids) => {
      await Promise.all(
        ids.map((id) => atualizarPlaylistAudio(id, { status: "archived" })),
      );
    },
    onSuccess: (_data, ids) => {
      qc.invalidateQueries(["audio-playlists"]);
      setSelectedIds(new Set());
      setSelectionMode(false);
      setBulkDeleteOpen(false);
      toast({
        title: `${ids.length} playlist${ids.length === 1 ? "" : "s"} arquivada${ids.length === 1 ? "" : "s"}.`,
      });
    },
    onError: (err) => {
      const msg =
        err?.detail ||
        err?.message ||
        (typeof err === "string" ? err : "Erro ao arquivar playlists.");
      toast({ title: "Erro ao arquivar", description: msg, variant: "destructive" });
    },
  });

  const filtered = playlists.filter((p) => {
    if (filterStatus !== "all" && p.status !== filterStatus) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  function handleEdit(pl) {
    setEditing(pl);
    setFormOpen(true);
  }
  function handleNew() {
    setEditing(null);
    setFormOpen(true);
  }

  function toggleSelection(id) {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  }

  function selectAll() {
    setSelectedIds(new Set(filtered.map((p) => p.id)));
  }

  function clearSelection() {
    setSelectedIds(new Set());
    setSelectionMode(false);
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
        <div className="flex gap-2">
          {!selectionMode && (
            <Button variant="outline" onClick={() => setSelectionMode(true)}>
              <CheckSquare className="w-4 h-4 mr-2" />
              Selecionar
            </Button>
          )}
          <Button onClick={handleNew}>
            <Plus className="w-4 h-4 mr-2" />
            Nova Playlist
          </Button>
        </div>
      </div>

      {selectionMode && (
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4 flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-4">
              <span className="font-medium text-foreground">
                {selectedIds.size === 0
                  ? "Nenhuma playlist selecionada"
                  : `${selectedIds.size} ${selectedIds.size === 1 ? "playlist selecionada" : "playlists selecionadas"}`}
              </span>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={selectAll}>
                  Selecionar Todas ({filtered.length})
                </Button>
                <Button size="sm" variant="outline" onClick={clearSelection}>
                  Limpar Seleção
                </Button>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {selectedIds.size > 0 && (
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => setBulkDeleteOpen(true)}
                  disabled={bulkArchiveMutation.isPending}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Arquivar ({selectedIds.size})
                </Button>
              )}
              <Button size="sm" variant="ghost" onClick={clearSelection}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Buscar playlist..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos</SelectItem>
            <SelectItem value="active">Ativo</SelectItem>
            <SelectItem value="inactive">Inativo</SelectItem>
            <SelectItem value="archived">Arquivado</SelectItem>
          </SelectContent>
        </Select>
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
            <Card
              key={pl.id}
              className={`hover:shadow-md transition-shadow ${
                selectedIds.has(pl.id) ? "ring-2 ring-primary bg-primary/5" : ""
              }`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {selectionMode && (
                      <button
                        onClick={() => toggleSelection(pl.id)}
                        className="w-9 h-9 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-colors hover:bg-primary/10"
                      >
                        {selectedIds.has(pl.id) ? (
                          <CheckSquare className="w-5 h-5 text-primary" />
                        ) : (
                          <Square className="w-5 h-5 text-muted-foreground" />
                        )}
                      </button>
                    )}
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
                {!selectionMode && (
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
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/radio/playlists/${pl.id}`)}
                      title="Pastas, agenda e spots"
                    >
                      <Settings2 className="w-3.5 h-3.5" />
                    </Button>
                    {pl.status === "archived" ? (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Restaurar"
                          onClick={() => restoreMutation.mutate(pl.id)}
                          disabled={restoreMutation.isPending}
                        >
                          <ArchiveRestore className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          title="Excluir definitivamente"
                          className="text-destructive hover:text-destructive"
                          onClick={() => setHardDeleteTarget(pl)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </>
                    ) : (
                      <Button
                        variant="ghost"
                        size="icon"
                        title="Arquivar"
                        className="text-destructive hover:text-destructive"
                        onClick={() => setArchiveTarget(pl)}
                      >
                        <Archive className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                )}
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
      {archiveTarget && (
        <ConfirmDialog
          open={!!archiveTarget}
          title="Arquivar playlist"
          description={`Arquivar "${archiveTarget.name}"? Dispositivos/campanhas vinculados não receberão mais áudio dela, mas a playlist pode ser restaurada depois.`}
          confirmLabel="Arquivar"
          variant="destructive"
          onClose={() => setArchiveTarget(null)}
          onConfirm={() => archiveMutation.mutate(archiveTarget.id)}
        />
      )}
      {hardDeleteTarget && (
        <ConfirmDialog
          open={!!hardDeleteTarget}
          title="Excluir playlist definitivamente"
          description={`Excluir "${hardDeleteTarget.name}" de forma definitiva? Esta ação não pode ser desfeita. Se a playlist estiver vinculada a algum dispositivo ou campanha, a exclusão será bloqueada.`}
          confirmLabel="Excluir definitivamente"
          variant="destructive"
          onClose={() => setHardDeleteTarget(null)}
          onConfirm={() => hardDeleteMutation.mutate(hardDeleteTarget.id)}
        />
      )}
      {bulkDeleteOpen && (
        <ConfirmDialog
          open={bulkDeleteOpen}
          title="Arquivar playlists"
          description={`Arquivar ${selectedIds.size} playlist${selectedIds.size === 1 ? "" : "s"} selecionada${selectedIds.size === 1 ? "" : "s"}? Dispositivos vinculados não receberão mais áudio.`}
          confirmLabel="Arquivar"
          variant="destructive"
          onClose={() => setBulkDeleteOpen(false)}
          onConfirm={() => bulkArchiveMutation.mutate(Array.from(selectedIds))}
        />
      )}
    </div>
  );
}

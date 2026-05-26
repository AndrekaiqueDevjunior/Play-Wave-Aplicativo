import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  buscarPlaylistAudio,
  listarFaixas,
  listarPastas,
  criarPasta,
  atualizarPasta,
  deletarPasta,
  listarFaixasDaPasta,
  adicionarFaixasNaPasta,
  removerFaixaDaPasta,
  listarFolderSchedules,
  criarFolderSchedule,
  atualizarFolderSchedule,
  deletarFolderSchedule,
  listarSpots,
  criarSpot,
  atualizarSpot,
  deletarSpot,
  listarSpotSchedules,
  criarSpotSchedule,
  atualizarSpotSchedule,
  deletarSpotSchedule,
} from "@/api/audio";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2, Folder, Clock, Volume2 } from "lucide-react";
import AudioFolderManager from "@/components/audio/AudioFolderManager";
import AudioScheduleBuilder from "@/components/audio/AudioScheduleBuilder";
import AudioSpotScheduleManager from "@/components/audio/AudioSpotScheduleManager";

export default function PlaylistDetalhe() {
  const { id: playlistId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [folderManagerOpen, setFolderManagerOpen] = useState(false);
  const [editingFolder, setEditingFolder] = useState(null);

  // ── Dados base ─────────────────────────────────────────────────────────────
  const { data: playlist, isLoading: loadingPlaylist } = useQuery({
    queryKey: ["audio-playlist", playlistId],
    queryFn: () => buscarPlaylistAudio(playlistId),
    enabled: !!playlistId,
  });

  const { data: allTracks = [] } = useQuery({
    queryKey: ["audio-tracks"],
    queryFn: () => listarFaixas({ status: "active" }),
  });

  const { data: folders = [], isLoading: loadingFolders } = useQuery({
    queryKey: ["audio-folders"],
    queryFn: () => listarPastas({ status: "active" }),
  });

  const { data: folderSchedules = [], isLoading: loadingSchedules } = useQuery({
    queryKey: ["folder-schedules", playlistId],
    queryFn: () => listarFolderSchedules(playlistId),
    enabled: !!playlistId,
  });

  const { data: spots = [], isLoading: loadingSpots } = useQuery({
    queryKey: ["audio-spots"],
    queryFn: () => listarSpots({ status: "active" }),
  });

  const { data: spotSchedules = [], isLoading: loadingSpotSchedules } = useQuery({
    queryKey: ["spot-schedules", playlistId],
    queryFn: () => listarSpotSchedules(playlistId),
    enabled: !!playlistId,
  });

  // ── Mutações de pasta ──────────────────────────────────────────────────────
  const createFolderMut = useMutation({
    mutationFn: async ({ folder, trackIds }) => {
      const created = await criarPasta(folder);
      if (trackIds?.length) {
        await adicionarFaixasNaPasta(created.id, trackIds);
      }
      return created;
    },
    onSuccess: () => {
      qc.invalidateQueries(["audio-folders"]);
      setFolderManagerOpen(false);
      setEditingFolder(null);
    },
  });

  const updateFolderMut = useMutation({
    mutationFn: async ({ folderId, folder, currentTrackIds }) => {
      await atualizarPasta(folderId, folder);
      const existingItems = await listarFaixasDaPasta(folderId).catch(() => []);
      const existingTrackIds = existingItems.map((i) => String(i.track_id || i.id));
      const wanted = (currentTrackIds || []).map(String);
      const toAdd = wanted.filter((id) => !existingTrackIds.includes(id));
      const toRemove = existingItems.filter((i) => !wanted.includes(String(i.track_id || i.id)));
      if (toAdd.length) await adicionarFaixasNaPasta(folderId, toAdd);
      if (toRemove.length) {
        await Promise.all(toRemove.map((item) => removerFaixaDaPasta(folderId, item.id)));
      }
    },
    onSuccess: () => {
      qc.invalidateQueries(["audio-folders"]);
      setFolderManagerOpen(false);
      setEditingFolder(null);
    },
  });

  const deleteFolderMut = useMutation({
    mutationFn: (folderId) => deletarPasta(folderId),
    onSuccess: () => {
      qc.invalidateQueries(["audio-folders"]);
      setFolderManagerOpen(false);
      setEditingFolder(null);
    },
  });

  // ── Mutações de folder schedule ────────────────────────────────────────────
  const addScheduleMut = useMutation({
    mutationFn: (payload) => criarFolderSchedule(playlistId, payload),
    onSuccess: () => qc.invalidateQueries(["folder-schedules", playlistId]),
  });

  const updateScheduleMut = useMutation({
    mutationFn: ({ id, ...payload }) => atualizarFolderSchedule(playlistId, id, payload),
    onSuccess: () => qc.invalidateQueries(["folder-schedules", playlistId]),
  });

  const deleteScheduleMut = useMutation({
    mutationFn: (id) => deletarFolderSchedule(playlistId, id),
    onSuccess: () => qc.invalidateQueries(["folder-schedules", playlistId]),
  });

  // ── Mutações de spots ──────────────────────────────────────────────────────
  const createSpotMut = useMutation({
    mutationFn: (payload) => criarSpot(payload),
    onSuccess: () => qc.invalidateQueries(["audio-spots"]),
  });

  const updateSpotMut = useMutation({
    mutationFn: ({ id, ...payload }) => atualizarSpot(id, payload),
    onSuccess: () => qc.invalidateQueries(["audio-spots"]),
  });

  const deleteSpotMut = useMutation({
    mutationFn: (id) => deletarSpot(id),
    onSuccess: () => qc.invalidateQueries(["audio-spots"]),
  });

  // ── Mutações de spot schedule ──────────────────────────────────────────────
  const addSpotScheduleMut = useMutation({
    mutationFn: (payload) => criarSpotSchedule(playlistId, payload),
    onSuccess: () => qc.invalidateQueries(["spot-schedules", playlistId]),
  });

  const updateSpotScheduleMut = useMutation({
    mutationFn: ({ id, ...payload }) => atualizarSpotSchedule(playlistId, id, payload),
    onSuccess: () => qc.invalidateQueries(["spot-schedules", playlistId]),
  });

  const deleteSpotScheduleMut = useMutation({
    mutationFn: (id) => deletarSpotSchedule(playlistId, id),
    onSuccess: () => qc.invalidateQueries(["spot-schedules", playlistId]),
  });

  // handlers com mutateAsync para fechar dialog após sucesso
  const handleCreateSpot    = (payload) => createSpotMut.mutateAsync(payload);
  const handleUpdateSpot    = (id, payload) => updateSpotMut.mutateAsync({ id, ...payload });
  const handleDeleteSpot    = (id) => deleteSpotMut.mutate(id);
  const handleCreateSchedule = (payload) => addSpotScheduleMut.mutateAsync(payload);
  const handleUpdateSchedule = (id, payload) => updateSpotScheduleMut.mutateAsync({ id, ...payload });
  const handleDeleteSchedule = (id) => deleteSpotScheduleMut.mutate(id);

  if (loadingPlaylist) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!playlist) {
    return (
      <div className="p-6 text-center text-muted-foreground">
        Playlist não encontrada.
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="text-xl font-semibold">{playlist.name}</h1>
          <p className="text-sm text-muted-foreground">
            Configuração avançada da playlist sonora
          </p>
        </div>
      </div>

      <Tabs defaultValue="pastas">
        <TabsList>
          <TabsTrigger value="pastas" className="gap-2">
            <Folder className="w-4 h-4" /> Pastas
          </TabsTrigger>
          <TabsTrigger value="agenda" className="gap-2">
            <Clock className="w-4 h-4" /> Agenda de pastas
          </TabsTrigger>
          <TabsTrigger value="spots" className="gap-2">
            <Volume2 className="w-4 h-4" /> Spots
          </TabsTrigger>
        </TabsList>

        {/* ── Aba: Pastas ─────────────────────────────────────────────────── */}
        <TabsContent value="pastas" className="mt-4">
          <div className="flex justify-end mb-4">
            <Button onClick={() => { setEditingFolder(null); setFolderManagerOpen(true); }}>
              <Folder className="w-4 h-4 mr-2" /> Nova pasta
            </Button>
          </div>

          {loadingFolders ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : folders.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              Nenhuma pasta criada. Crie pastas para organizar faixas por horário.
            </p>
          ) : (
            <div className="grid gap-3">
              {folders.map((folder) => (
                <div
                  key={folder.id}
                  className="flex items-center justify-between p-4 border rounded-lg"
                >
                  <div>
                    <p className="font-medium">{folder.name}</p>
                    {folder.description && (
                      <p className="text-sm text-muted-foreground">{folder.description}</p>
                    )}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => { setEditingFolder(folder); setFolderManagerOpen(true); }}
                  >
                    Editar
                  </Button>
                </div>
              ))}
            </div>
          )}

          <AudioFolderManager
            open={folderManagerOpen}
            onOpenChange={setFolderManagerOpen}
            folders={folders}
            tracks={allTracks}
            loading={createFolderMut.isPending || updateFolderMut.isPending}
            onSave={(folderData, trackIds) =>
              createFolderMut.mutateAsync({ folder: folderData, trackIds })
            }
            onUpdate={(folderId, folderData, currentTrackIds) =>
              updateFolderMut.mutateAsync({ folderId, folder: folderData, currentTrackIds })
            }
            onDelete={(folderId) => deleteFolderMut.mutate(folderId)}
          />
        </TabsContent>

        {/* ── Aba: Agenda de pastas ────────────────────────────────────────── */}
        <TabsContent value="agenda" className="mt-4">
          <AudioScheduleBuilder
            playlistId={playlistId}
            schedules={folderSchedules}
            folders={folders}
            loading={loadingSchedules || addScheduleMut.isPending}
            onAdd={(payload) => addScheduleMut.mutate(payload)}
            onUpdate={(payload) => updateScheduleMut.mutate(payload)}
            onDelete={(id) => deleteScheduleMut.mutate(id)}
          />
        </TabsContent>

        {/* ── Aba: Spots ───────────────────────────────────────────────────── */}
        <TabsContent value="spots" className="mt-4">
          <AudioSpotScheduleManager
            playlistId={playlistId}
            spots={spots}
            spotSchedules={spotSchedules}
            tracks={allTracks}
            loading={createSpotMut.isPending || updateSpotMut.isPending || addSpotScheduleMut.isPending || updateSpotScheduleMut.isPending}
            onCreateSpot={handleCreateSpot}
            onUpdateSpot={handleUpdateSpot}
            onDeleteSpot={handleDeleteSpot}
            onCreateSchedule={handleCreateSchedule}
            onUpdateSchedule={handleUpdateSchedule}
            onDeleteSchedule={handleDeleteSchedule}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

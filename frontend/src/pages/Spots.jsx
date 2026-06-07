import React, { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Loader2, Volume2, Search, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import {
  listarSpots,
  criarSpot,
  atualizarSpot,
  deletarSpot,
  listarSpotSchedules,
  criarSpotSchedule,
  atualizarSpotSchedule,
  deletarSpotSchedule,
} from "@/api/audio";
import { listarPlaylistsAudio } from "@/api/audio";
import { listarFaixas } from "@/api/audio";
import SpotSchedulePanel from "@/components/audio/SpotSchedulePanel";

const INSERTION_LABELS = {
  interrupt: "Interrompe música",
  wait_silence: "Aguarda silêncio",
};

const ALL_STATUS = "all";
const NO_PLAYLIST = "none";

export default function Spots() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("active");
  const [selectedPlaylistId, setSelectedPlaylistId] = useState("");

  const { data: spots = [], isLoading: loadingSpots } = useQuery({
    queryKey: ["audio-spots", statusFilter],
    queryFn: () => listarSpots(statusFilter === ALL_STATUS ? {} : { status: statusFilter }),
  });

  const { data: playlists = [] } = useQuery({
    queryKey: ["audio-playlists"],
    queryFn: () => listarPlaylistsAudio({ status: "active" }),
  });

  const { data: tracks = [] } = useQuery({
    queryKey: ["audio-tracks-active"],
    queryFn: () => listarFaixas({ status: "active" }),
  });

  const { data: schedules = [], refetch: refetchSchedules } = useQuery({
    queryKey: ["spot-schedules-global", selectedPlaylistId],
    queryFn: () => selectedPlaylistId ? listarSpotSchedules(selectedPlaylistId) : Promise.resolve([]),
    enabled: !!selectedPlaylistId,
  });

  const filtered = spots.filter((s) =>
    !search || s.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreateSpot = async (payload) => {
    await criarSpot(payload);
    qc.invalidateQueries({ queryKey: ["audio-spots"] });
  };

  const handleUpdateSpot = async (id, payload) => {
    await atualizarSpot(id, payload);
    qc.invalidateQueries({ queryKey: ["audio-spots"] });
  };

  const handleDeleteSpot = async (id) => {
    await deletarSpot(id);
    qc.invalidateQueries({ queryKey: ["audio-spots"] });
  };

  const handleCreateSchedule = async (payload) => {
    if (!selectedPlaylistId) throw new Error("Selecione uma playlist");
    await criarSpotSchedule(selectedPlaylistId, payload);
    refetchSchedules();
  };

  const handleUpdateSchedule = async (scheduleId, payload) => {
    if (!selectedPlaylistId) return;
    await atualizarSpotSchedule(selectedPlaylistId, scheduleId, payload);
    refetchSchedules();
  };

  const handleDeleteSchedule = async (scheduleId) => {
    if (!selectedPlaylistId) return;
    await deletarSpotSchedule(selectedPlaylistId, scheduleId);
    refetchSchedules();
  };

  return (
    <div className="p-6 space-y-6">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <Volume2 className="w-5 h-5" />
            Spots de Áudio
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Gerencie jingles e anúncios para inserção automática na rádio
          </p>
        </div>
      </div>

      {/* Painel principal: biblioteca + agendamentos */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Gerenciador de Spots e Agendamentos</CardTitle>
          <div className="flex gap-3 flex-wrap mt-2">
            <div className="flex-1 min-w-48">
              <Select
                value={selectedPlaylistId || NO_PLAYLIST}
                onValueChange={(v) => setSelectedPlaylistId(v === NO_PLAYLIST ? "" : v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione uma playlist para agendar..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NO_PLAYLIST}>— Nenhuma playlist selecionada —</SelectItem>
                  {playlists.map((p) => (
                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedPlaylistId && (
              <Link
                to={`/radio/playlists/${selectedPlaylistId}`}
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline self-center"
              >
                Abrir playlist
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <SpotSchedulePanel
            scope="playlist"
            scopeId={selectedPlaylistId}
            playlistId={selectedPlaylistId}
            spots={spots}
            schedules={schedules}
            tracks={tracks}
            onCreateSpot={handleCreateSpot}
            onUpdateSpot={handleUpdateSpot}
            onDeleteSpot={handleDeleteSpot}
            onCreateSchedule={handleCreateSchedule}
            onUpdateSchedule={handleUpdateSchedule}
            onDeleteSchedule={handleDeleteSchedule}
          />
        </CardContent>
      </Card>

      {/* Resumo: todos os spots por status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-3">
            <CardTitle className="text-base">
              Todos os Spots ({filtered.length})
            </CardTitle>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar..."
                  className="pl-8 h-9 w-44"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="h-9 w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_STATUS}>Todos</SelectItem>
                  <SelectItem value="active">Ativos</SelectItem>
                  <SelectItem value="inactive">Inativos</SelectItem>
                  <SelectItem value="archived">Arquivados</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loadingSpots ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <Volume2 className="w-10 h-10 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">Nenhum spot encontrado</p>
              <p className="text-xs text-muted-foreground/70 mt-1">
                Use o gerenciador acima para criar spots
              </p>
            </div>
          ) : (
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((spot) => (
                <div
                  key={spot.id}
                  className="flex flex-col gap-2 p-3 border rounded-lg hover:bg-muted/20 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-sm truncate">{spot.name}</p>
                    <Badge
                      variant={spot.status === "active" ? "default" : "secondary"}
                      className="text-xs flex-shrink-0"
                    >
                      {spot.status === "active" ? "Ativo" : spot.status === "inactive" ? "Inativo" : "Arquivado"}
                    </Badge>
                  </div>
                  {spot.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {spot.description}
                    </p>
                  )}
                  <div className="flex gap-1.5 flex-wrap">
                    <Badge variant="outline" className="text-xs">
                      {INSERTION_LABELS[spot.insertion_policy] || spot.insertion_policy}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

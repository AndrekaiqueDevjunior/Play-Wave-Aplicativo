import React, { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listarFaixas, atualizarFaixa } from "@/api/audio";
import { assetUrl } from "@/utils/mediaUtils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Music,
  Upload,
  Play,
  Pause,
  Trash2,
  Edit2,
  Search,
  Clock,
  HardDrive,
} from "lucide-react";
import AudioTrackFormModal from "@/components/audio/AudioTrackFormModal";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import StatusBadge from "@/components/shared/StatusBadge";

const categoryLabels = {
  music: "Música",
  jingle: "Jingle",
  announcement: "Anúncio",
  ambient: "Ambiente",
  other: "Outro",
};

function formatSize(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(seconds) {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function FaixasAudio() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [playingId, setPlayingId] = useState(null);
  const audioRef = useRef(null);

  const { data: tracks = [], isLoading } = useQuery({
    queryKey: ["audio-tracks"],
    queryFn: () => listarFaixas(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => atualizarFaixa(id, { status: "archived" }),
    onSuccess: () => {
      qc.invalidateQueries(["audio-tracks"]);
      setDeleteTarget(null);
    },
  });

  const filtered = tracks.filter((t) => {
    if (filterStatus !== "all" && t.status !== filterStatus) return false;
    if (filterCategory !== "all" && t.category !== filterCategory) return false;
    if (search && !t.name.toLowerCase().includes(search.toLowerCase()))
      return false;
    return true;
  });

  function togglePlay(track) {
    if (!audioRef.current) audioRef.current = new Audio();
    const audio = audioRef.current;
    if (playingId === track.id) {
      audio.pause();
      setPlayingId(null);
    } else {
      audio.src = assetUrl(track.file_url);
      audio.play();
      setPlayingId(track.id);
      audio.onended = () => setPlayingId(null);
    }
  }

  function handleEdit(track) {
    setEditing(track);
    setFormOpen(true);
  }
  function handleNew() {
    setEditing(null);
    setFormOpen(true);
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Faixas de Áudio
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Gerencie faixas de áudio para Rádio Indoor · MP3, WAV, OGG, OPUS, AAC, FLAC
          </p>
        </div>
        <Button onClick={handleNew}>
          <Upload className="w-4 h-4 mr-2" />
          Upload de Áudio
        </Button>
      </div>

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Buscar faixa..."
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
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Categoria" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas</SelectItem>
            {Object.entries(categoryLabels).map(([v, l]) => (
              <SelectItem key={v} value={v}>
                {l}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total", value: tracks.length, color: "text-foreground" },
          {
            label: "Ativas",
            value: tracks.filter((t) => t.status === "active").length,
            color: "text-emerald-600",
          },
          {
            label: "Inativas",
            value: tracks.filter((t) => t.status === "inactive").length,
            color: "text-amber-600",
          },
          {
            label: "Arquivadas",
            value: tracks.filter((t) => t.status === "archived").length,
            color: "text-slate-500",
          },
        ].map((s) => (
          <Card key={s.label}>
            <CardContent className="p-4">
              <p className="text-sm text-muted-foreground">{s.label}</p>
              <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <Music className="w-12 h-12 text-muted-foreground mb-3" />
            <p className="font-medium text-muted-foreground">
              Nenhuma faixa encontrada
            </p>
            <Button className="mt-4" onClick={handleNew}>
              <Upload className="w-4 h-4 mr-2" />
              Upload de Áudio
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {filtered.map((track) => (
            <Card key={track.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4 flex items-center gap-4">
                <button
                  onClick={() => togglePlay(track)}
                  className="w-10 h-10 rounded-full bg-primary/10 hover:bg-primary/20 flex items-center justify-center text-primary flex-shrink-0 transition-colors"
                >
                  {playingId === track.id ? (
                    <Pause className="w-4 h-4" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                </button>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-foreground truncate">
                      {track.name}
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {categoryLabels[track.category] || track.category}
                    </Badge>
                    <StatusBadge status={track.status} />
                  </div>
                  {track.description && (
                    <p className="text-xs text-muted-foreground mt-0.5 truncate">
                      {track.description}
                    </p>
                  )}
                </div>
                <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {formatDuration(track.duration_seconds)}
                  </span>
                  <span className="flex items-center gap-1">
                    <HardDrive className="w-3.5 h-3.5" />
                    {formatSize(track.file_size)}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleEdit(track)}
                  >
                    <Edit2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setDeleteTarget(track)}
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
        <AudioTrackFormModal
          track={editing}
          onClose={() => setFormOpen(false)}
          onSaved={() => {
            qc.invalidateQueries(["audio-tracks"]);
            setFormOpen(false);
          }}
        />
      )}
      {deleteTarget && (
        <ConfirmDialog
          title="Arquivar faixa"
          description={`Arquivar "${deleteTarget.name}"? A faixa será removida das playlists ativas.`}
          confirmLabel="Arquivar"
          variant="destructive"
          onClose={() => setDeleteTarget(null)}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
        />
      )}
    </div>
  );
}

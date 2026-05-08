import React, { useState } from "react";
import {
  Plus,
  Search,
  Image,
  Film,
  Music,
  Link2,
  MoreHorizontal,
  Eye,
  Pencil,
  Trash2,
  LayoutGrid,
  List,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import StatusBadge from "@/components/shared/StatusBadge";
import EmptyState from "@/components/shared/EmptyState";
import ConfirmDialog from "@/components/shared/ConfirmDialog";
import MediaFormModal from "@/components/media/MediaFormModal";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { base44 } from "@/api/base44Client";
import { useToast } from "@/components/ui/use-toast";

const TYPE_ICON = {
  image: Image,
  video: Film,
  audio: Music,
  external_url: Link2,
};
const TYPE_LABEL = {
  image: "Imagem",
  video: "Vídeo",
  audio: "Áudio",
  external_url: "URL",
};

function formatSize(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

export default function BibliotecaMidias() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [view, setView] = useState("grid");
  const [modalOpen, setModalOpen] = useState(false);
  const [editMedia, setEditMedia] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [previewMedia, setPreviewMedia] = useState(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: mediaList = [], isLoading } = useQuery({
    queryKey: ["media"],
    queryFn: () => base44.entities.Media.list("-created_date"),
  });

  const categories = [
    ...new Set(mediaList.map((m) => m.category).filter(Boolean)),
  ];

  const filtered = mediaList.filter((m) => {
    const q = search.toLowerCase();
    const matchSearch =
      (m.name || "").toLowerCase().includes(q) ||
      (m.tags || []).some((t) => t.toLowerCase().includes(q));
    const matchType = typeFilter === "all" || m.type === typeFilter;
    const matchCat = categoryFilter === "all" || m.category === categoryFilter;
    return matchSearch && matchType && matchCat;
  });

  const handleSave = async (form) => {
    if (editMedia) {
      await base44.entities.Media.update(editMedia.id, form);
      toast({ title: "Mídia atualizada!" });
    } else {
      await base44.entities.Media.create(form);
      toast({
        title: "Mídia adicionada!",
        description: `${form.name} está disponível.`,
      });
    }
    queryClient.invalidateQueries({ queryKey: ["media"] });
    setModalOpen(false);
    setEditMedia(null);
  };

  const handleDelete = async () => {
    await base44.entities.Media.delete(deleteTarget.id);
    queryClient.invalidateQueries({ queryKey: ["media"] });
    toast({ title: "Mídia excluída." });
    setDeleteTarget(null);
  };

  const openEdit = (m) => {
    setEditMedia(m);
    setModalOpen(true);
  };
  const openNew = () => {
    setEditMedia(null);
    setModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold">Biblioteca de Mídias</h2>
          <p className="text-sm text-muted-foreground">
            {mediaList.length} arquivo(s) cadastrado(s)
          </p>
        </div>
        <Button onClick={openNew}>
          <Plus className="w-4 h-4 mr-2" />
          Adicionar Mídia
        </Button>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nome ou tag..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-36">
            <SelectValue placeholder="Tipo" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos tipos</SelectItem>
            <SelectItem value="image">Imagens</SelectItem>
            <SelectItem value="video">Vídeos</SelectItem>
            <SelectItem value="audio">Áudios</SelectItem>
            <SelectItem value="external_url">URL externa</SelectItem>
          </SelectContent>
        </Select>
        {categories.length > 0 && (
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="w-full sm:w-40">
              <SelectValue placeholder="Categoria" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas categorias</SelectItem>
              {categories.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        <div className="flex border rounded-md overflow-hidden">
          <Button
            variant={view === "grid" ? "secondary" : "ghost"}
            size="icon"
            className="rounded-none h-9"
            onClick={() => setView("grid")}
          >
            <LayoutGrid className="w-4 h-4" />
          </Button>
          <Button
            variant={view === "list" ? "secondary" : "ghost"}
            size="icon"
            className="rounded-none h-9"
            onClick={() => setView("list")}
          >
            <List className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Image}
          title="Nenhuma mídia encontrada"
          description="Adicione a primeira mídia ou ajuste os filtros."
        />
      ) : view === "grid" ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((media) => {
            const TypeIcon = TYPE_ICON[media.type] || Image;
            return (
              <Card
                key={media.id}
                className="overflow-hidden group hover:shadow-md transition-shadow"
              >
                <div className="relative aspect-video bg-muted overflow-hidden">
                  {media.thumbnail_url || media.file_url ? (
                    <img
                      src={media.thumbnail_url || media.file_url}
                      alt={media.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <TypeIcon className="w-10 h-10 text-muted-foreground/40" />
                    </div>
                  )}
                  <div className="absolute top-2 left-2">
                    <Badge
                      variant="secondary"
                      className="text-xs bg-black/60 text-white border-0"
                    >
                      <TypeIcon className="w-3 h-3 mr-1" />
                      {TYPE_LABEL[media.type] || media.type}
                    </Badge>
                  </div>
                  {media.duration && (
                    <div className="absolute top-2 right-2">
                      <Badge
                        variant="secondary"
                        className="text-xs bg-black/60 text-white border-0"
                      >
                        {media.duration}s
                      </Badge>
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                    <Button
                      size="icon"
                      variant="secondary"
                      className="h-8 w-8"
                      onClick={() => setPreviewMedia(media)}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button
                      size="icon"
                      variant="secondary"
                      className="h-8 w-8"
                      onClick={() => openEdit(media)}
                    >
                      <Pencil className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">
                        {media.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatSize(media.file_size)}
                        {media.resolution ? ` · ${media.resolution}` : ""}
                      </p>
                      {media.category && (
                        <p className="text-xs text-muted-foreground">
                          {media.category}
                        </p>
                      )}
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 shrink-0"
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={() => setPreviewMedia(media)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          Visualizar
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => openEdit(media)}>
                          <Pencil className="w-4 h-4 mr-2" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => setDeleteTarget(media)}
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Excluir
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <div className="mt-2 flex items-center gap-2 flex-wrap">
                    <StatusBadge status={media.status} />
                    {(media.tags || []).slice(0, 2).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mídia</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead className="hidden md:table-cell">Duração</TableHead>
                <TableHead className="hidden md:table-cell">Tamanho</TableHead>
                <TableHead className="hidden lg:table-cell">
                  Categoria
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((media) => {
                const TypeIcon = TYPE_ICON[media.type] || Image;
                return (
                  <TableRow key={media.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-8 rounded bg-muted overflow-hidden shrink-0">
                          {media.thumbnail_url || media.file_url ? (
                            <img
                              src={media.thumbnail_url || media.file_url}
                              alt={media.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <TypeIcon className="w-4 h-4 text-muted-foreground" />
                            </div>
                          )}
                        </div>
                        <p className="text-sm font-medium truncate max-w-[200px]">
                          {media.name}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        <TypeIcon className="w-3 h-3 mr-1" />
                        {TYPE_LABEL[media.type]}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm">
                      {media.duration ? `${media.duration}s` : "—"}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                      {formatSize(media.file_size)}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                      {media.category || "—"}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={media.status} />
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                          >
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => setPreviewMedia(media)}
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            Visualizar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEdit(media)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Editar
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteTarget(media)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Excluir
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      )}

      <MediaFormModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setEditMedia(null);
        }}
        onSave={handleSave}
        media={editMedia}
      />
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Excluir mídia?"
        description={`"${deleteTarget?.name}" será removida permanentemente.`}
      />

      <Dialog open={!!previewMedia} onOpenChange={() => setPreviewMedia(null)}>
        <DialogContent className="max-w-3xl p-0 overflow-hidden bg-black">
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-2 right-2 z-10 text-white hover:bg-white/20"
            onClick={() => setPreviewMedia(null)}
          >
            <X className="w-5 h-5" />
          </Button>
          {previewMedia?.type === "video" ? (
            <video
              src={previewMedia.file_url}
              controls
              autoPlay
              className="w-full max-h-[80vh]"
            />
          ) : previewMedia?.type === "audio" ? (
            <div className="p-8 flex flex-col items-center gap-4">
              <Music className="w-16 h-16 text-white/50" />
              <p className="text-white font-medium">{previewMedia.name}</p>
              <audio src={previewMedia.file_url} controls className="w-full" />
            </div>
          ) : (
            <img
              src={previewMedia?.file_url || previewMedia?.thumbnail_url}
              alt={previewMedia?.name}
              className="w-full max-h-[80vh] object-contain"
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

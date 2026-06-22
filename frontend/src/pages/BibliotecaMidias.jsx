import React, { useState, useRef } from "react";
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
  RefreshCw,
  Loader2,
  CheckSquare,
  Square,
  Archive,
  ArchiveRestore,
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
import MediaThumb from "@/components/media/MediaThumb";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listarMidias,
  criarMidiaExterna,
  atualizarMidia,
  deletarMidia,
  substituirArquivoMidia,
  arquivarMidiasEmMassa,
  excluirMidiasEmMassa,
} from "@/api/midias";
import { useToast } from "@/components/ui/use-toast";
import { assetUrl } from "@/utils/mediaUtils";

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

function formatDuration(media) {
  if (media.display_duration_seconds) return `${media.display_duration_seconds}s`;
  if (media.duration_seconds) return `${media.duration_seconds}s`;
  if (media.duration) return `${media.duration}s`;
  if (media.type === "video" || media.type === "audio") return "Até o fim";
  return "—";
}

function formatPeriod(media) {
  const start = media.starts_at ? new Date(media.starts_at).toLocaleDateString("pt-BR") : "Agora";
  const end = media.ends_at ? new Date(media.ends_at).toLocaleDateString("pt-BR") : "Sem fim";
  return `${start} - ${end}`;
}

const AVAILABILITY_LABEL = {
  active: "Ativa",
  scheduled: "Agendada",
  expired: "Expirada",
  inactive: "Inativa",
  processing: "Processando",
  error: "Com erro",
};

export default function BibliotecaMidias() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [view, setView] = useState("grid");
  const [modalOpen, setModalOpen] = useState(false);
  const [editMedia, setEditMedia] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [previewMedia, setPreviewMedia] = useState(null);
  const [replacingMedia, setReplacingMedia] = useState(null);
  const replaceFileRef = useRef(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // SPEC 018 — seleção em massa
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkArchiveOpen, setBulkArchiveOpen] = useState(false);
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);

  const { data: mediaList = [], isLoading } = useQuery({
    queryKey: ["media"],
    // include_archived=true — SPEC 018: por padrão o backend esconde
    // arquivadas (para não aparecerem em seletores de campanha), mas esta é
    // a tela de gerenciamento, onde o admin precisa ver/restaurar
    // arquivadas via o filtro de status abaixo.
    queryFn: () => listarMidias({ include_archived: true }),
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
    const matchStatus = statusFilter === "all" || m.status === statusFilter;
    return matchSearch && matchType && matchCat && matchStatus;
  });

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
    setSelectedIds(new Set(filtered.map((m) => m.id)));
  }

  function clearSelection() {
    setSelectedIds(new Set());
    setSelectionMode(false);
  }

  function describeBulkResult(action, result) {
    const { requested, succeeded, failed, results } = result;
    if (failed === 0) {
      toast({ title: `${succeeded} mídia(s) ${action === "archive" ? "arquivada(s)" : "excluída(s)"}.` });
      return;
    }
    const reasons = results
      .filter((r) => !r.success)
      .map((r) => {
        const media = mediaList.find((m) => m.id === r.media_id);
        return `${media?.name || r.media_id}: ${r.reason}`;
      })
      .join(" · ");
    toast({
      title: `${succeeded}/${requested} ${action === "archive" ? "arquivada(s)" : "excluída(s)"}, ${failed} falharam`,
      description: reasons,
      variant: failed === requested ? "destructive" : "default",
    });
  }

  async function handleBulkArchive() {
    setBulkLoading(true);
    try {
      const result = await arquivarMidiasEmMassa(Array.from(selectedIds));
      queryClient.invalidateQueries({ queryKey: ["media"] });
      describeBulkResult("archive", result);
      clearSelection();
    } catch (error) {
      toast({
        title: "Erro ao arquivar em massa",
        description: error?.message || "Tente novamente.",
        variant: "destructive",
      });
    } finally {
      setBulkLoading(false);
      setBulkArchiveOpen(false);
    }
  }

  async function handleBulkDelete() {
    setBulkLoading(true);
    try {
      const result = await excluirMidiasEmMassa(Array.from(selectedIds));
      queryClient.invalidateQueries({ queryKey: ["media"] });
      describeBulkResult("delete", result);
      clearSelection();
    } catch (error) {
      toast({
        title: "Erro ao excluir em massa",
        description: error?.message || "Tente novamente.",
        variant: "destructive",
      });
    } finally {
      setBulkLoading(false);
      setBulkDeleteOpen(false);
    }
  }

  const handleSave = async (form) => {
    if (editMedia) {
      await atualizarMidia(editMedia.id, form);
      toast({ title: "Mídia atualizada!" });
    } else {
      await criarMidiaExterna(form);
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
    try {
      await deletarMidia(deleteTarget.id);
      queryClient.invalidateQueries({ queryKey: ["media"] });
      toast({ title: "Mídia excluída." });
      setDeleteTarget(null);
    } catch (error) {
      toast({
        title: "Mídia em uso",
        description: error?.message || "Esta mídia está vinculada a campanhas. Remova os vínculos antes de excluir.",
        variant: "destructive",
      });
    }
  };

  const handleRestore = async (media) => {
    try {
      await atualizarMidia(media.id, { status: "available" });
      queryClient.invalidateQueries({ queryKey: ["media"] });
      toast({ title: "Mídia restaurada." });
    } catch (error) {
      toast({
        title: "Erro ao restaurar",
        description: error?.message || "Tente novamente.",
        variant: "destructive",
      });
    }
  };

  const handleArchive = async (media) => {
    try {
      await atualizarMidia(media.id, { status: "archived" });
      queryClient.invalidateQueries({ queryKey: ["media"] });
      toast({ title: "Mídia arquivada." });
    } catch (error) {
      toast({
        title: "Erro ao arquivar",
        description: error?.message || "Tente novamente.",
        variant: "destructive",
      });
    }
  };

  const openEdit = (m) => {
    setEditMedia(m);
    setModalOpen(true);
  };
  const openNew = () => {
    setEditMedia(null);
    setModalOpen(true);
  };

  const handleReplaceFile = async (e) => {
    const newFile = e.target.files?.[0];
    if (!newFile || !replacingMedia) return;
    try {
      await substituirArquivoMidia(replacingMedia.id, newFile);
      queryClient.invalidateQueries({ queryKey: ["media"] });
      toast({ title: "Arquivo substituído!", description: `${replacingMedia.name} foi atualizada.` });
    } catch {
      toast({ title: "Erro ao substituir arquivo", variant: "destructive" });
    } finally {
      setReplacingMedia(null);
      e.target.value = "";
    }
  };

  const openReplaceFile = (m) => {
    setReplacingMedia(m);
    replaceFileRef.current?.click();
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
        <div className="flex gap-2">
          {!selectionMode && (
            <Button variant="outline" onClick={() => setSelectionMode(true)}>
              <CheckSquare className="w-4 h-4 mr-2" />
              Selecionar
            </Button>
          )}
          <Button onClick={openNew}>
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Mídia
          </Button>
        </div>
      </div>

      {selectionMode && (
        <Card className="bg-primary/5 border-primary/20">
          <div className="p-4 flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-4">
              <span className="font-medium text-foreground">
                {selectedIds.size === 0
                  ? "Nenhuma mídia selecionada"
                  : `${selectedIds.size} ${selectedIds.size === 1 ? "mídia selecionada" : "mídias selecionadas"}`}
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
                <>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setBulkArchiveOpen(true)}
                    disabled={bulkLoading}
                  >
                    {bulkLoading ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Archive className="w-4 h-4 mr-2" />
                    )}
                    Arquivar ({selectedIds.size})
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => setBulkDeleteOpen(true)}
                    disabled={bulkLoading}
                  >
                    {bulkLoading ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4 mr-2" />
                    )}
                    Excluir ({selectedIds.size})
                  </Button>
                </>
              )}
              <Button size="sm" variant="ghost" onClick={clearSelection}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      )}

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
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos status</SelectItem>
            <SelectItem value="available">Disponível</SelectItem>
            <SelectItem value="processing">Processando</SelectItem>
            <SelectItem value="error">Com erro</SelectItem>
            <SelectItem value="archived">Arquivada</SelectItem>
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
                className={`overflow-hidden group hover:shadow-md transition-shadow ${
                  selectedIds.has(media.id) ? "ring-2 ring-primary bg-primary/5" : ""
                }`}
              >
                <div className="relative aspect-video bg-muted overflow-hidden">
                  <MediaThumb
                    media={media}
                    className="group-hover:scale-105 transition-transform duration-300"
                  />
                  {selectionMode && (
                    <button
                      onClick={() => toggleSelection(media.id)}
                      className="absolute top-2 left-2 w-7 h-7 rounded-md border-2 bg-white/90 flex items-center justify-center z-10"
                    >
                      {selectedIds.has(media.id) ? (
                        <CheckSquare className="w-4 h-4 text-primary" />
                      ) : (
                        <Square className="w-4 h-4 text-muted-foreground" />
                      )}
                    </button>
                  )}
                  <div className={`absolute top-2 ${selectionMode ? "left-11" : "left-2"}`}>
                    <Badge
                      variant="secondary"
                      className="text-xs bg-black/60 text-white border-0"
                    >
                      <TypeIcon className="w-3 h-3 mr-1" />
                      {TYPE_LABEL[media.type] || media.type}
                    </Badge>
                  </div>
                  {formatDuration(media) !== "—" && (
                    <div className="absolute top-2 right-2">
                      <Badge
                        variant="secondary"
                        className="text-xs bg-black/60 text-white border-0"
                      >
                        {formatDuration(media)}
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
                      <p className="text-xs text-muted-foreground">
                        {formatPeriod(media)}
                      </p>
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
                        {media.type !== "external_url" && (
                          <DropdownMenuItem onClick={() => openReplaceFile(media)}>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Substituir arquivo
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        {media.status === "archived" ? (
                          <DropdownMenuItem onClick={() => handleRestore(media)}>
                            <ArchiveRestore className="w-4 h-4 mr-2" />
                            Restaurar
                          </DropdownMenuItem>
                        ) : (
                          <DropdownMenuItem onClick={() => handleArchive(media)}>
                            <Archive className="w-4 h-4 mr-2" />
                            Arquivar
                          </DropdownMenuItem>
                        )}
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={() => setDeleteTarget(media)}
                        >
                          <Trash2 className="w-4 h-4 mr-2" />
                          Excluir definitivamente
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                  <div className="mt-2 flex items-center gap-2 flex-wrap">
                    <StatusBadge status={media.status} />
                    {media.availability_status && (
                      <Badge variant="outline" className="text-xs">
                        {AVAILABILITY_LABEL[media.availability_status] || media.availability_status}
                      </Badge>
                    )}
                    {media.usage_count > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        Em {media.usage_count} campanha(s)
                      </Badge>
                    )}
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
                {selectionMode && <TableHead className="w-10"></TableHead>}
                <TableHead>Mídia</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead className="hidden md:table-cell">Duração</TableHead>
                <TableHead className="hidden lg:table-cell">Período</TableHead>
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
                  <TableRow
                    key={media.id}
                    className={selectedIds.has(media.id) ? "bg-primary/5" : ""}
                  >
                    {selectionMode && (
                      <TableCell>
                        <button onClick={() => toggleSelection(media.id)}>
                          {selectedIds.has(media.id) ? (
                            <CheckSquare className="w-4 h-4 text-primary" />
                          ) : (
                            <Square className="w-4 h-4 text-muted-foreground" />
                          )}
                        </button>
                      </TableCell>
                    )}
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-8 rounded bg-muted overflow-hidden shrink-0">
                          <MediaThumb media={media} />
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
                      {formatDuration(media)}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                      {formatPeriod(media)}
                    </TableCell>
                    <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                      {formatSize(media.file_size)}
                    </TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">
                      {media.category || "—"}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <StatusBadge status={media.status} />
                        {media.availability_status && (
                          <span className="text-xs text-muted-foreground">
                            {AVAILABILITY_LABEL[media.availability_status] || media.availability_status}
                          </span>
                        )}
                      </div>
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
                          {media.type !== "external_url" && (
                            <DropdownMenuItem onClick={() => openReplaceFile(media)}>
                              <RefreshCw className="w-4 h-4 mr-2" />
                              Substituir arquivo
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {media.status === "archived" ? (
                            <DropdownMenuItem onClick={() => handleRestore(media)}>
                              <ArchiveRestore className="w-4 h-4 mr-2" />
                              Restaurar
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem onClick={() => handleArchive(media)}>
                              <Archive className="w-4 h-4 mr-2" />
                              Arquivar
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteTarget(media)}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Excluir definitivamente
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
        onUploaded={(uploaded) => {
          queryClient.invalidateQueries({ queryKey: ["media"] });
          toast({
            title: "Mídia enviada!",
            description: `${uploaded?.name || "Arquivo"} foi adicionado.`,
          });
          setModalOpen(false);
          setEditMedia(null);
        }}
        media={editMedia}
      />
      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title="Excluir mídia?"
        description={`"${deleteTarget?.name}" será removida permanentemente.`}
      />
      <ConfirmDialog
        open={bulkArchiveOpen}
        onClose={() => setBulkArchiveOpen(false)}
        onConfirm={handleBulkArchive}
        title="Arquivar mídias selecionadas?"
        description={`Arquivar ${selectedIds.size} mídia${selectedIds.size === 1 ? "" : "s"} selecionada${selectedIds.size === 1 ? "" : "s"}? Elas deixam de aparecer nas seleções de campanha e podem ser restauradas depois.`}
        confirmLabel="Arquivar"
        variant="destructive"
      />
      <ConfirmDialog
        open={bulkDeleteOpen}
        onClose={() => setBulkDeleteOpen(false)}
        onConfirm={handleBulkDelete}
        title="Excluir mídias selecionadas definitivamente?"
        description={`Excluir ${selectedIds.size} mídia${selectedIds.size === 1 ? "" : "s"} selecionada${selectedIds.size === 1 ? "" : "s"} de forma definitiva? Esta ação não pode ser desfeita. Mídias em uso por campanhas serão reportadas como falha e não excluídas.`}
        confirmLabel="Excluir definitivamente"
        variant="destructive"
      />

      {/* Input oculto para substituição de arquivo */}
      <input
        ref={replaceFileRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,video/mp4,audio/*"
        className="hidden"
        onChange={handleReplaceFile}
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
              src={assetUrl(previewMedia.file_url)}
              controls
              autoPlay
              className="w-full max-h-[80vh]"
            />
          ) : previewMedia?.type === "audio" ? (
            <div className="p-8 flex flex-col items-center gap-4">
              <Music className="w-16 h-16 text-white/50" />
              <p className="text-white font-medium">{previewMedia.name}</p>
              <audio src={assetUrl(previewMedia.file_url)} controls className="w-full" />
            </div>
          ) : (
            <img
              src={assetUrl(previewMedia?.thumbnail_url || previewMedia?.file_url)}
              alt={previewMedia?.name}
              className="w-full max-h-[80vh] object-contain"
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

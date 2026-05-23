import React, { useState, useEffect } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Folder,
  Plus,
  Trash2,
  Edit,
  Loader2,
  Music,
} from "lucide-react";
import AudioTrackSelector from "./AudioTrackSelector";

const FOLDER_STATUS = {
  active: "Ativo",
  inactive: "Inativo",
  archived: "Arquivado",
};

export default function AudioFolderManager({
  open,
  onOpenChange,
  folders = [],
  tracks = [],
  onSave,
  onDelete,
  onUpdate,
  loading = false,
}) {
  const [editingFolder, setEditingFolder] = useState(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    status: "active",
    start_time: "00:00",
    end_time: "23:59",
    is_active: true,
  });
  const [selectedTracks, setSelectedTracks] = useState([]);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleNewFolder = () => {
    setEditingFolder(null);
    setForm({
      name: "",
      description: "",
      status: "active",
      start_time: "00:00",
      end_time: "23:59",
      is_active: true,
    });
    setSelectedTracks([]);
  };

  const handleEditFolder = (folder) => {
    setEditingFolder(folder);
    setForm({
      name: folder.name || "",
      description: folder.description || "",
      status: folder.status || "active",
      start_time: folder.start_time || "00:00",
      end_time: folder.end_time || "23:59",
      is_active: folder.is_active ?? true,
    });
    setSelectedTracks((folder.tracks || []).map((t) => t.id));
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      alert("Nome da pasta é obrigatório");
      return;
    }

    const payload = {
      ...form,
      track_ids: selectedTracks,
    };

    if (editingFolder) {
      await onUpdate?.(editingFolder.id, payload);
    } else {
      await onSave?.(payload);
    }

    setEditingFolder(null);
  };

  const handleDeleteFolder = async () => {
    if (deleteConfirm) {
      await onDelete?.(deleteConfirm.id);
      setDeleteConfirm(null);
    }
  };

  const folderTracks = editingFolder
    ? editingFolder.tracks || []
    : [];

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="max-w-2xl overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Gerenciar Pastas de Áudio</SheetTitle>
            <SheetDescription>
              Organize suas faixas em pastas por hora do dia
            </SheetDescription>
          </SheetHeader>

          {!editingFolder ? (
            /* Lista de pastas */
            <div className="space-y-4 py-6">
              <Button onClick={handleNewFolder} className="w-full">
                <Plus className="mr-2 h-4 w-4" />
                Nova Pasta
              </Button>

              {loading ? (
                <div className="flex justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : folders.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Folder className="h-8 w-8 text-gray-300 mb-2" />
                  <p className="text-gray-500 text-sm">Nenhuma pasta criada</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {folders.map((folder) => (
                    <div
                      key={folder.id}
                      className="flex items-start justify-between p-3 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex-1">
                        <h4 className="font-medium">{folder.name}</h4>
                        <p className="text-xs text-gray-500 line-clamp-1">
                          {folder.description}
                        </p>
                        <div className="flex gap-2 mt-2 flex-wrap">
                          <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                            {folder.start_time} - {folder.end_time}
                          </span>
                          <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">
                            {FOLDER_STATUS[folder.status]}
                          </span>
                          <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                            {(folder.tracks || []).length} faixa
                            {(folder.tracks || []).length !== 1 ? "s" : ""}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-1 flex-shrink-0">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditFolder(folder)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteConfirm(folder)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            /* Formulário de edição */
            <Tabs defaultValue="info" className="py-6">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="info">Informações</TabsTrigger>
                <TabsTrigger value="tracks">Faixas</TabsTrigger>
              </TabsList>

              <TabsContent value="info" className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="folder-name">Nome *</Label>
                  <Input
                    id="folder-name"
                    value={form.name}
                    onChange={(e) =>
                      setForm({ ...form, name: e.target.value })
                    }
                    placeholder="Ex: Manhã, Tarde, Noite"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="folder-desc">Descrição</Label>
                  <Textarea
                    id="folder-desc"
                    value={form.description}
                    onChange={(e) =>
                      setForm({ ...form, description: e.target.value })
                    }
                    placeholder="Descrição opcional da pasta"
                    rows={3}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="start-time">Início</Label>
                    <Input
                      id="start-time"
                      type="time"
                      value={form.start_time}
                      onChange={(e) =>
                        setForm({ ...form, start_time: e.target.value })
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="end-time">Fim</Label>
                    <Input
                      id="end-time"
                      type="time"
                      value={form.end_time}
                      onChange={(e) =>
                        setForm({ ...form, end_time: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="folder-status">Status</Label>
                  <Select
                    value={form.status}
                    onValueChange={(v) =>
                      setForm({ ...form, status: v })
                    }
                  >
                    <SelectTrigger id="folder-status">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(FOLDER_STATUS).map(([key, label]) => (
                        <SelectItem key={key} value={key}>
                          {label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center gap-2">
                  <Checkbox
                    id="is-active"
                    checked={form.is_active}
                    onCheckedChange={(checked) =>
                      setForm({ ...form, is_active: checked })
                    }
                  />
                  <Label htmlFor="is-active" className="cursor-pointer">
                    Pasta ativa
                  </Label>
                </div>
              </TabsContent>

              <TabsContent value="tracks" className="space-y-4">
                <div className="text-sm text-gray-600">
                  Selecione as faixas que pertencem a esta pasta
                </div>
                <AudioTrackSelector
                  tracks={tracks}
                  selectedIds={selectedTracks}
                  onSelectionChange={setSelectedTracks}
                  loading={loading}
                  showCategory={true}
                  showDuration={true}
                />
              </TabsContent>
            </Tabs>
          )}

          {editingFolder && (
            <SheetFooter className="pt-6 border-t">
              <Button
                variant="outline"
                onClick={() => setEditingFolder(null)}
              >
                Cancelar
              </Button>
              <Button onClick={handleSave} disabled={loading}>
                {loading && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Salvar
              </Button>
            </SheetFooter>
          )}
        </SheetContent>
      </Sheet>

      {/* Confirmação de exclusão */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={(open) => !open && setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir pasta?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir "<strong>{deleteConfirm?.name}</strong>"?
              Isso não deletará as faixas, apenas a pasta.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="flex gap-2 justify-end">
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteFolder}
              className="bg-red-600 hover:bg-red-700"
            >
              Excluir
            </AlertDialogAction>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

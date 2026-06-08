import React, { useState, useMemo } from "react";
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Plus,
  Trash2,
  Edit2,
  Loader2,
  Music,
  Search,
} from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import useAudioCategories from "@/hooks/useAudioCategories";

/**
 * AudioCategoryDrawer — Gerenciador de categorias de áudio (TASK 02)
 *
 * Drawer lateral com:
 * - Input para criar categoria
 * - Search para filtrar
 * - Lista de categorias (padrão + personalizadas)
 * - Botões para editar/deletar (só custom)
 */
export default function AudioCategoryDrawer({ open, onOpenChange }) {
  const { toast } = useToast();
  const {
    categories,
    defaultCategories,
    customCategories,
    loading,
    createCategory,
    updateCategory,
    deleteCategory,
  } = useAudioCategories();

  const [newCategoryName, setNewCategoryName] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editingName, setEditingName] = useState("");
  const [creatingLoading, setCreatingLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  // Filtrar categorias por search
  const filteredCategories = useMemo(() => {
    if (!searchTerm.trim()) return categories;
    const term = searchTerm.toLowerCase();
    return categories.filter(cat => cat.name.toLowerCase().includes(term));
  }, [categories, searchTerm]);

  // Separar filtrados em padrão e custom
  const filteredDefaults = filteredCategories.filter(cat => cat.is_default);
  const filteredCustom = filteredCategories.filter(cat => !cat.is_default);

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) {
      toast({
        title: "Campo obrigatório",
        description: "Informe o nome da categoria",
        variant: "destructive",
      });
      return;
    }

    setCreatingLoading(true);
    try {
      await createCategory(newCategoryName);
      setNewCategoryName("");
      toast({
        title: "Categoria criada",
        description: `"${newCategoryName}" foi criada com sucesso`,
      });
    } catch (err) {
      toast({
        title: "Erro ao criar categoria",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setCreatingLoading(false);
    }
  };

  const handleStartEdit = (category) => {
    setEditingId(category.id);
    setEditingName(category.name);
  };

  const handleSaveEdit = async () => {
    if (!editingName.trim()) {
      toast({
        title: "Campo obrigatório",
        description: "Informe o nome da categoria",
        variant: "destructive",
      });
      return;
    }

    try {
      await updateCategory(editingId, editingName);
      setEditingId(null);
      toast({
        title: "Categoria atualizada",
        description: "Nome alterado com sucesso",
      });
    } catch (err) {
      toast({
        title: "Erro ao atualizar",
        description: err.message,
        variant: "destructive",
      });
    }
  };

  const handleDeleteCategory = async () => {
    if (!deleteConfirm) return;
    try {
      await deleteCategory(deleteConfirm.id);
      setDeleteConfirm(null);
      toast({
        title: "Categoria removida",
        description: `"${deleteConfirm.name}" foi removida`,
      });
    } catch (err) {
      toast({
        title: "Erro ao remover",
        description: err.message,
        variant: "destructive",
      });
    }
  };

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full sm:max-w-md">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Music className="w-5 h-5" />
              Categorias de Áudio
            </SheetTitle>
            <SheetDescription>
              Crie e organize categorias personalizadas para suas faixas
            </SheetDescription>
          </SheetHeader>

          <div className="space-y-6 py-6">
            {/* Criar categoria */}
            <div className="space-y-3 border-b pb-6">
              <Label>Criar nova categoria</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Nome da categoria"
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") handleCreateCategory();
                  }}
                  disabled={creatingLoading}
                />
                <Button
                  onClick={handleCreateCategory}
                  disabled={creatingLoading || !newCategoryName.trim()}
                  size="sm"
                >
                  {creatingLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Plus className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Search */}
            <div className="space-y-3">
              <Label>Filtrar</Label>
              <div className="relative">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar categoria"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            {/* Categorias padrão */}
            {filteredDefaults.length > 0 && (
              <div className="space-y-3">
                <Label className="text-xs text-muted-foreground">
                  CATEGORIAS PADRÃO ({filteredDefaults.length})
                </Label>
                <div className="space-y-2">
                  {filteredDefaults.map((cat) => (
                    <div
                      key={cat.slug}
                      className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border"
                    >
                      <span className="font-medium text-sm">{cat.name}</span>
                      <span className="text-xs text-muted-foreground">
                        Padrão
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Categorias personalizadas */}
            {filteredCustom.length > 0 && (
              <div className="space-y-3">
                <Label className="text-xs text-muted-foreground">
                  MINHAS CATEGORIAS ({filteredCustom.length})
                </Label>
                <div className="space-y-2">
                  {filteredCustom.map((cat) => (
                    <div key={cat.id}>
                      {editingId === cat.id ? (
                        // Modo edição
                        <div className="flex gap-2">
                          <Input
                            value={editingName}
                            onChange={(e) => setEditingName(e.target.value)}
                            onKeyPress={(e) => {
                              if (e.key === "Enter") handleSaveEdit();
                            }}
                            autoFocus
                          />
                          <Button
                            onClick={handleSaveEdit}
                            size="sm"
                            variant="default"
                          >
                            Salvar
                          </Button>
                          <Button
                            onClick={() => setEditingId(null)}
                            size="sm"
                            variant="outline"
                          >
                            Cancelar
                          </Button>
                        </div>
                      ) : (
                        // Modo visualização
                        <div className="flex items-center justify-between p-3 bg-blue-50/50 rounded-lg border border-blue-200/50">
                          <span className="font-medium text-sm">{cat.name}</span>
                          <div className="flex gap-1">
                            <Button
                              onClick={() => handleStartEdit(cat)}
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0"
                            >
                              <Edit2 className="w-4 h-4" />
                            </Button>
                            <Button
                              onClick={() => setDeleteConfirm(cat)}
                              size="sm"
                              variant="ghost"
                              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Estado vazio */}
            {loading && (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {!loading && categories.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                <Music className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Nenhuma categoria ainda</p>
              </div>
            )}

            {!loading && filteredCategories.length === 0 && searchTerm && (
              <div className="text-center py-8 text-muted-foreground">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Nenhuma categoria encontrada</p>
              </div>
            )}
          </div>

          <SheetFooter>
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Fechar
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>

      {/* Confirm delete */}
      <AlertDialog open={!!deleteConfirm} onOpenChange={(open) => !open && setDeleteConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover categoria?</AlertDialogTitle>
            <AlertDialogDescription>
              A categoria "{deleteConfirm?.name}" será removida. As faixas vinculadas
              perderão a categoria, mas não serão deletadas.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteCategory} className="bg-destructive hover:bg-destructive/90">
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

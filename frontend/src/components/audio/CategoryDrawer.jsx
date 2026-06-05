import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listarCategoriasAudio,
  criarCategoriaAudio,
  deletarCategoriaAudio,
} from "@/api/audio";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Trash2, Tag, Loader2 } from "lucide-react";

/**
 * CategoryDrawer — drawer lateral para gerenciar categorias de áudio (TASK 02).
 * Input (nome) + botão "Criar categoria" + busca + lista (padrão + personalizadas).
 */
export default function CategoryDrawer({ open, onOpenChange }) {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const { data: categories = [], isLoading } = useQuery({
    queryKey: ["audio-categories"],
    queryFn: () => listarCategoriasAudio(),
    enabled: open,
  });

  const createMutation = useMutation({
    mutationFn: (categoryName) => criarCategoriaAudio({ name: categoryName }),
    onSuccess: () => {
      qc.invalidateQueries(["audio-categories"]);
      setName("");
      setError("");
    },
    onError: (err) => setError(err?.message || "Erro ao criar categoria"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => deletarCategoriaAudio(id),
    onSuccess: () => qc.invalidateQueries(["audio-categories"]),
  });

  function handleCreate(e) {
    e?.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Informe um nome para a categoria");
      return;
    }
    createMutation.mutate(trimmed);
  }

  const filtered = categories.filter((c) =>
    c.name.toLowerCase().includes(search.trim().toLowerCase())
  );
  const defaults = filtered.filter((c) => c.is_default);
  const custom = filtered.filter((c) => !c.is_default);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex flex-col gap-4 w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Tag className="w-5 h-5 text-primary" />
            Categorias de áudio
          </SheetTitle>
          <SheetDescription>
            Crie categorias personalizadas para organizar faixas, pastas e playlists.
          </SheetDescription>
        </SheetHeader>

        {/* Criar categoria */}
        <form onSubmit={handleCreate} className="space-y-2">
          <div className="flex gap-2">
            <Input
              placeholder="Nome da categoria (ex: Promoções)"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (error) setError("");
              }}
              maxLength={100}
            />
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              <span className="ml-2 hidden sm:inline">Criar categoria</span>
            </Button>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </form>

        {/* Busca */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Buscar categoria..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Lista */}
        <div className="flex-1 overflow-y-auto -mx-1 px-1 space-y-4">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : (
            <>
              {custom.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Personalizadas
                  </p>
                  {custom.map((cat) => (
                    <div
                      key={cat.id}
                      className="flex items-center justify-between rounded-md border px-3 py-2 hover:bg-muted/50"
                    >
                      <div className="min-w-0">
                        <span className="font-medium text-foreground truncate block">
                          {cat.name}
                        </span>
                        <span className="text-xs text-muted-foreground">{cat.slug}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:text-destructive flex-shrink-0"
                        onClick={() => deleteMutation.mutate(cat.id)}
                        disabled={deleteMutation.isPending}
                        title="Remover categoria"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Padrão
                </p>
                {defaults.map((cat) => (
                  <div
                    key={cat.slug}
                    className="flex items-center justify-between rounded-md border px-3 py-2 bg-muted/30"
                  >
                    <span className="font-medium text-foreground">{cat.name}</span>
                    <Badge variant="outline" className="text-xs">
                      Padrão
                    </Badge>
                  </div>
                ))}
              </div>

              {filtered.length === 0 && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Nenhuma categoria encontrada.
                </p>
              )}
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

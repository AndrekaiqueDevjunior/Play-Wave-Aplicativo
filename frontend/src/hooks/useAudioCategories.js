import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/api/http";

/**
 * Hook para gerenciar categorias de áudio (TASK 02)
 *
 * Carrega categorias do servidor (padrão + personalizadas)
 * Permite criar, editar e deletar categorias
 */
export function useAudioCategories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Carregar categorias do servidor
  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch("/audio/categories/?include_defaults=true");
      setCategories(response || []);
    } catch (err) {
      setError(err.message || "Erro ao carregar categorias");
      console.error("[useAudioCategories] Error loading:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Criar categoria
  const createCategory = useCallback(async (name) => {
    if (!name?.trim()) {
      throw new Error("Nome da categoria é obrigatório");
    }

    try {
      const response = await apiFetch("/audio/categories", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
        }),
      });
      setCategories(prev => [...prev, response]);
      return response;
    } catch (err) {
      const message = err.message || "Erro ao criar categoria";
      throw new Error(message);
    }
  }, []);

  // Renomear categoria
  const updateCategory = useCallback(async (categoryId, newName) => {
    if (!newName?.trim()) {
      throw new Error("Nome da categoria é obrigatório");
    }

    try {
      const response = await apiFetch(`/audio/categories/${categoryId}`, {
        method: "PUT",
        body: JSON.stringify({
          name: newName.trim(),
        }),
      });
      setCategories(prev =>
        prev.map(cat => (cat.id === categoryId ? response : cat))
      );
      return response;
    } catch (err) {
      const message = err.message || "Erro ao atualizar categoria";
      throw new Error(message);
    }
  }, []);

  // Deletar categoria
  const deleteCategory = useCallback(async (categoryId) => {
    try {
      await apiFetch(`/audio/categories/${categoryId}`, {
        method: "DELETE",
      });
      setCategories(prev => prev.filter(cat => cat.id !== categoryId));
    } catch (err) {
      const message = err.message || "Erro ao deletar categoria";
      throw new Error(message);
    }
  }, []);

  // Carregamento inicial
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  // Filtrar categorias padrão e personalizadas
  const defaultCategories = categories.filter(cat => cat.is_default);
  const customCategories = categories.filter(cat => !cat.is_default);

  return {
    categories,
    defaultCategories,
    customCategories,
    loading,
    error,
    loadCategories,
    createCategory,
    updateCategory,
    deleteCategory,
  };
}

export default useAudioCategories;

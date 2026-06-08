import React, { useState, useEffect, useMemo } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Music, Search, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import useAudioCategories from "@/hooks/useAudioCategories";

// Rótulos das categorias padrão (legado, enum fixo `category`).
// Faixas com `category_id` (categoria personalizada) usam o nome real —
// ver `customCategoryName`/`trackCategoryLabel` abaixo.
const CATEGORY_LABELS = {
  music: "Música",
  jingle: "Jingle",
  announcement: "Anúncio",
  ambient: "Ambiente",
  other: "Outro",
};

const formatDuration = (seconds) => {
  if (!seconds) return "—";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

export default function AudioTrackSelector({
  tracks = [],
  selectedIds = [],
  onSelectionChange,
  loading = false,
  maxSelection = null,
  searchPlaceholder = "Buscar faixas...",
  showCategory = true,
  showDuration = true,
}) {
  const [search, setSearch] = useState("");
  // "all" | `default:<slug>` | `custom:<id>`
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [checked, setChecked] = useState(new Set(selectedIds || []));

  const { categories } = useAudioCategories();

  // Mapa id->nome das categorias personalizadas para exibir no badge da faixa.
  const customCategoryName = useMemo(() => {
    const map = {};
    categories.forEach((c) => {
      if (c.id) map[c.id] = c.name;
    });
    return map;
  }, [categories]);

  function trackCategoryLabel(track) {
    if (track.category_id && customCategoryName[track.category_id]) {
      return customCategoryName[track.category_id];
    }
    return CATEGORY_LABELS[track.category] || track.category;
  }

  useEffect(() => {
    setChecked(new Set(selectedIds || []));
  }, [selectedIds]);

  const filteredTracks = tracks.filter((track) => {
    const matchSearch =
      !search ||
      track.name.toLowerCase().includes(search.toLowerCase()) ||
      (track.description || "").toLowerCase().includes(search.toLowerCase());

    let matchCategory = true;
    if (selectedCategory.startsWith("custom:")) {
      matchCategory = track.category_id === selectedCategory.slice(7);
    } else if (selectedCategory.startsWith("default:")) {
      matchCategory =
        !track.category_id && track.category === selectedCategory.slice(8);
    }

    return matchSearch && matchCategory;
  });

  const handleToggle = (trackId) => {
    const newChecked = new Set(checked);

    if (newChecked.has(trackId)) {
      newChecked.delete(trackId);
    } else {
      if (maxSelection && newChecked.size >= maxSelection) {
        alert(`Máximo ${maxSelection} faixa(s) permitida(s)`);
        return;
      }
      newChecked.add(trackId);
    }

    setChecked(newChecked);
    onSelectionChange?.([...newChecked]);
  };

  const handleSelectAll = () => {
    if (checked.size === filteredTracks.length) {
      setChecked(new Set());
      onSelectionChange?.([]);
    } else {
      const newChecked = new Set(
        filteredTracks.map((t) => t.id).slice(0, maxSelection || undefined)
      );
      setChecked(newChecked);
      onSelectionChange?.([...newChecked]);
    }
  };

  return (
    <div className="space-y-4">
      {/* Controles */}
      <div className="flex gap-3 flex-wrap items-end">
        <div className="flex-1 min-w-60">
          <Input
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9"
            icon={<Search className="h-4 w-4" />}
          />
        </div>

        {showCategory && (
          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-40 h-9">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as Categorias</SelectItem>
              {categories
                .filter((c) => c.is_default)
                .map((c) => (
                  <SelectItem key={c.slug} value={`default:${c.slug}`}>
                    {c.name}
                  </SelectItem>
                ))}
              {categories
                .filter((c) => !c.is_default)
                .map((c) => (
                  <SelectItem key={c.id} value={`custom:${c.id}`}>
                    {c.name}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        )}

        {filteredTracks.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleSelectAll}
            disabled={loading}
          >
            {checked.size === filteredTracks.length
              ? "Desselecionar Tudo"
              : "Selecionar Tudo"}
          </Button>
        )}
      </div>

      {/* Contador */}
      <div className="text-sm text-gray-600">
        {checked.size} faixa{checked.size !== 1 ? "s" : ""} selecionada
        {checked.size !== 1 ? "s" : ""}
        {filteredTracks.length > 0 && ` de ${filteredTracks.length}`}
      </div>

      {/* Lista de faixas */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </div>
      ) : filteredTracks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Music className="h-8 w-8 text-gray-300 mb-2" />
          <p className="text-gray-500 text-sm">
            {tracks.length === 0
              ? "Nenhuma faixa disponível"
              : "Nenhuma faixa encontrada"}
          </p>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden bg-white max-h-96 overflow-y-auto">
          {filteredTracks.map((track) => (
            <div
              key={track.id}
              className="flex items-center gap-3 px-4 py-3 border-b last:border-b-0 hover:bg-gray-50 transition-colors"
            >
              <Checkbox
                checked={checked.has(track.id)}
                onCheckedChange={() => handleToggle(track.id)}
                disabled={loading}
              />

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{track.name}</p>
                <p className="text-xs text-gray-500 truncate">
                  {track.description}
                </p>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                {showCategory && (
                  <span className="text-xs px-2 py-1 bg-gray-100 rounded whitespace-nowrap">
                    {trackCategoryLabel(track)}
                  </span>
                )}

                {showDuration && (
                  <span className="text-xs text-gray-600 whitespace-nowrap">
                    {formatDuration(track.duration_seconds)}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

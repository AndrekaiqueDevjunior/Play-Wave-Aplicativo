import React, { useMemo, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  Clock,
  CopyPlus,
  GripVertical,
  ListVideo,
  Plus,
  Repeat,
  Search,
  Trash2,
  Upload,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import MediaThumb from "@/components/media/MediaThumb";
import { cn } from "@/lib/utils";
import { uploadMidia } from "@/api/midias";

const TYPE_LABEL = {
  image: "Imagem",
  video: "Video",
  audio: "Audio",
  external_url: "URL",
};

function localId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatDuration(media) {
  if (!media) return "Duracao herdada";
  const seconds =
    media.display_duration_seconds || media.duration_seconds || media.duration;
  if (!seconds) {
    return media.type === "video" || media.type === "audio"
      ? "Ate o fim"
      : "Duracao herdada";
  }
  return `${seconds}s`;
}

function itemKey(item) {
  return item.id || item.local_id;
}

export function normalizeCampaignPlaylistItems(items = []) {
  return items.map((item, index) => ({
    id: item.id || null,
    local_id: item.local_id || localId(),
    media_id: item.media_id,
    order_index: index * 10,
    display_duration_seconds:
      item.display_duration_seconds === "" || item.display_duration_seconds == null
        ? null
        : Number(item.display_duration_seconds),
    starts_at: item.starts_at || null,
    ends_at: item.ends_at || null,
    is_active: item.is_active !== false,
    repeat_count: Math.max(1, Number(item.repeat_count) || 1),
  }));
}

export function itemsFromCampaignLegacy(campaign, mediaList = []) {
  const ids = Array.isArray(campaign?.media_ids) ? campaign.media_ids : [];
  return ids.map((mediaId, index) => {
    const media = mediaList.find((m) => m.id === mediaId);
    return {
      local_id: localId(),
      media_id: mediaId,
      order_index: index * 10,
      display_duration_seconds: null,
      starts_at: "",
      ends_at: "",
      is_active: true,
      repeat_count: 1,
      media,
    };
  });
}

export function itemsFromApi(apiItems = [], mediaList = []) {
  return apiItems.map((item, index) => ({
    id: item.id,
    local_id: localId(),
    media_id: item.media_id,
    order_index: item.order_index ?? index * 10,
    display_duration_seconds: item.display_duration_seconds || "",
    starts_at: item.starts_at ? item.starts_at.slice(0, 16) : "",
    ends_at: item.ends_at ? item.ends_at.slice(0, 16) : "",
    is_active: item.is_active !== false,
    repeat_count: item.repeat_count || 1,
    media: mediaList.find((m) => m.id === item.media_id),
  }));
}

export default function CampaignPlaylistBuilder({
  items,
  onChange,
  mediaList = [],
  onMediaUploaded,
  loading = false,
}) {
  const [search, setSearch] = useState("");
  const [draggingIndex, setDraggingIndex] = useState(null);
  const [uploading, setUploading] = useState(false);
  const uploadRef = useRef(null);

  const mediaById = useMemo(
    () => new Map((mediaList || []).map((media) => [media.id, media])),
    [mediaList],
  );

  const availableMedia = useMemo(() => {
    const q = search.trim().toLowerCase();
    return (mediaList || [])
      .filter((media) => !media.status || media.status === "available")
      .filter((media) => {
        if (!q) return true;
        return (
          (media.name || "").toLowerCase().includes(q) ||
          (media.category || "").toLowerCase().includes(q) ||
          (media.tags || []).some((tag) => String(tag).toLowerCase().includes(q))
        );
      });
  }, [mediaList, search]);

  const enrichedItems = (items || []).map((item) => ({
    ...item,
    media: item.media || mediaById.get(item.media_id),
  }));

  const totalSeconds = enrichedItems.reduce((sum, item) => {
    const media = item.media;
    const duration =
      Number(item.display_duration_seconds) ||
      media?.display_duration_seconds ||
      media?.duration_seconds ||
      media?.duration ||
      0;
    return sum + duration * (Number(item.repeat_count) || 1);
  }, 0);

  const totalLabel = totalSeconds
    ? `${Math.floor(totalSeconds / 60)}m ${String(totalSeconds % 60).padStart(2, "0")}s`
    : "variavel";

  function commit(nextItems) {
    onChange(normalizeCampaignPlaylistItems(nextItems));
  }

  async function handleQuickUpload(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploading(true);
    try {
      for (const file of files) {
        const isVideo = file.type.startsWith("video/");
        const uploaded = await uploadMidia(file, {
          name: file.name.replace(/\.[^/.]+$/, ""),
          type: isVideo ? "video" : "image",
          status: "available",
        });
        if (uploaded?.id) onMediaUploaded?.(uploaded);
      }
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  function addMedia(media) {
    commit([
      ...enrichedItems,
      {
        local_id: localId(),
        media_id: media.id,
        order_index: enrichedItems.length * 10,
        display_duration_seconds: "",
        starts_at: "",
        ends_at: "",
        is_active: true,
        repeat_count: 1,
        media,
      },
    ]);
  }

  function updateItem(index, patch) {
    const next = enrichedItems.map((item, idx) =>
      idx === index ? { ...item, ...patch } : item,
    );
    commit(next);
  }

  function removeItem(index) {
    commit(enrichedItems.filter((_, idx) => idx !== index));
  }

  function moveItem(index, direction) {
    const target = index + direction;
    if (target < 0 || target >= enrichedItems.length) return;
    const next = [...enrichedItems];
    const [moved] = next.splice(index, 1);
    next.splice(target, 0, moved);
    commit(next);
  }

  function handleDragOver(event, targetIndex) {
    event.preventDefault();
    if (draggingIndex === null || draggingIndex === targetIndex) return;
    const next = [...enrichedItems];
    const [moved] = next.splice(draggingIndex, 1);
    next.splice(targetIndex, 0, moved);
    setDraggingIndex(targetIndex);
    commit(next);
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <p className="text-sm font-medium">Itens da playlist</p>
          <p className="text-xs text-muted-foreground">
            {enrichedItems.length} item(ns) · duracao estimada {totalLabel}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
          Carregando itens...
        </div>
      ) : enrichedItems.length === 0 ? (
        <div className="rounded-lg border border-dashed p-6 text-center">
          <ListVideo className="w-8 h-8 mx-auto text-muted-foreground mb-2" />
          <p className="text-sm font-medium">Nenhuma midia na campanha</p>
          <p className="text-xs text-muted-foreground mt-1">
            Adicione midias pela biblioteca abaixo.
          </p>
        </div>
      ) : (
        <div className="rounded-lg border divide-y overflow-hidden">
          {enrichedItems.map((item, index) => {
            const media = item.media;
            return (
              <div
                key={itemKey(item)}
                draggable
                onDragStart={() => setDraggingIndex(index)}
                onDragOver={(event) => handleDragOver(event, index)}
                onDragEnd={() => setDraggingIndex(null)}
                className={cn(
                  "p-3 bg-background space-y-3",
                  draggingIndex === index && "opacity-70 bg-accent",
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="pt-2 text-muted-foreground cursor-grab">
                    <GripVertical className="w-4 h-4" />
                  </div>
                  <div className="w-20 h-12 rounded-md overflow-hidden bg-muted shrink-0">
                    {media ? <MediaThumb media={media} /> : null}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono text-muted-foreground">
                        #{index + 1}
                      </span>
                      <p className="text-sm font-medium truncate">
                        {media?.name || "Midia removida ou indisponivel"}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {TYPE_LABEL[media?.type] || media?.type || "Midia"}
                      </Badge>
                      {!item.is_active && (
                        <Badge variant="secondary" className="text-xs">
                          Inativo
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Base: {formatDuration(media)}
                      {media?.availability_status ? ` · ${media.availability_status}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      disabled={index === 0}
                      onClick={() => moveItem(index, -1)}
                    >
                      <ArrowUp className="w-4 h-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      disabled={index === enrichedItems.length - 1}
                      onClick={() => moveItem(index, 1)}
                    >
                      <ArrowDown className="w-4 h-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => removeItem(index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pl-0 md:pl-[7.75rem]">
                  <div className="space-y-1">
                    <Label className="text-xs flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Duracao
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      placeholder="Herdar"
                      value={item.display_duration_seconds || ""}
                      onChange={(event) =>
                        updateItem(index, {
                          display_duration_seconds: event.target.value,
                        })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs flex items-center gap-1">
                      <Repeat className="w-3 h-3" />
                      Repetir
                    </Label>
                    <Input
                      type="number"
                      min="1"
                      max="999"
                      value={item.repeat_count || 1}
                      onChange={(event) =>
                        updateItem(index, { repeat_count: event.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Inicio item</Label>
                    <Input
                      type="datetime-local"
                      value={item.starts_at || ""}
                      onChange={(event) =>
                        updateItem(index, { starts_at: event.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Fim item</Label>
                    <Input
                      type="datetime-local"
                      value={item.ends_at || ""}
                      onChange={(event) =>
                        updateItem(index, { ends_at: event.target.value })
                      }
                    />
                  </div>
                  <div className="flex items-end justify-between md:justify-end gap-2">
                    <Label className="text-xs">Ativo</Label>
                    <Switch
                      checked={item.is_active !== false}
                      onCheckedChange={(checked) =>
                        updateItem(index, { is_active: checked })
                      }
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <Label>Biblioteca de midias</Label>
          <div className="flex items-center gap-2">
            <div className="relative w-48 max-w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Buscar midia..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={uploading}
              onClick={() => uploadRef.current?.click()}
            >
              <Upload className="w-3.5 h-3.5 mr-1.5" />
              {uploading ? "Enviando..." : "Upload"}
            </Button>
            <input
              ref={uploadRef}
              type="file"
              multiple
              accept="image/jpeg,image/png,image/webp,video/mp4"
              className="hidden"
              onChange={handleQuickUpload}
            />
          </div>
        </div>
        {availableMedia.length === 0 ? (
          <div className="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
            Nenhuma midia disponivel.
          </div>
        ) : (
          <div className="rounded-lg border divide-y max-h-72 overflow-y-auto">
            {availableMedia.map((media) => (
              <div key={media.id} className="flex items-center gap-3 p-3">
                <div className="w-16 h-10 rounded overflow-hidden bg-muted shrink-0">
                  <MediaThumb media={media} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate">{media.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {TYPE_LABEL[media.type] || media.type} · {formatDuration(media)}
                    {media.category ? ` · ${media.category}` : ""}
                  </p>
                </div>
                <Button type="button" variant="outline" size="sm" onClick={() => addMedia(media)}>
                  <Plus className="w-3.5 h-3.5 mr-1.5" />
                  Adicionar
                </Button>
                <Button type="button" variant="ghost" size="icon" onClick={() => addMedia(media)}>
                  <CopyPlus className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

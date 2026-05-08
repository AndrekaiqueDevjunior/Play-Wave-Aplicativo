import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ArrowLeft,
  GripVertical,
  X,
  Clock,
  Save,
  Image,
  Film,
} from "lucide-react";
import { mockMedia, mockCampaigns } from "@/lib/mockData";
import { useToast } from "@/components/ui/use-toast";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

export default function EditorPlaylist() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const pathId = window.location.pathname.split("/")[2];
  const campaign =
    mockCampaigns.find((c) => c.id === pathId) || mockCampaigns[0];

  const [playlist, setPlaylist] = useState(
    mockMedia
      .filter((m) => campaign.media_ids?.includes(m.id))
      .map((m) => ({ ...m, customDuration: m.duration })),
  );

  const available = mockMedia.filter(
    (m) => !playlist.find((p) => p.id === m.id) && m.status === "available",
  );
  const totalDuration = playlist.reduce(
    (sum, m) => sum + (m.customDuration || m.duration || 10),
    0,
  );

  const addToPlaylist = (media) =>
    setPlaylist((prev) => [
      ...prev,
      { ...media, customDuration: media.duration },
    ]);
  const removeFromPlaylist = (id) =>
    setPlaylist((prev) => prev.filter((m) => m.id !== id));

  const onDragEnd = (result) => {
    if (!result.destination) return;
    const items = [...playlist];
    const [reordered] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reordered);
    setPlaylist(items);
  };

  const updateDuration = (id, duration) => {
    setPlaylist((prev) =>
      prev.map((m) =>
        m.id === id ? { ...m, customDuration: parseInt(duration) || 0 } : m,
      ),
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/campanhas")}
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1">
          <h2 className="text-xl font-bold">Editor de Playlist</h2>
          <p className="text-sm text-muted-foreground">
            {campaign.name} · {playlist.length} mídias · {totalDuration}s total
          </p>
        </div>
        <Button
          onClick={() => {
            toast({ title: "Playlist salva!" });
            navigate("/campanhas");
          }}
        >
          <Save className="w-4 h-4 mr-2" />
          Salvar Playlist
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Mídias Disponíveis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[600px] overflow-y-auto">
            {available.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Todas as mídias já estão na playlist
              </p>
            ) : (
              available.map((media) => (
                <div
                  key={media.id}
                  onClick={() => addToPlaylist(media)}
                  className="flex items-center gap-3 p-2 rounded-lg border border-border hover:border-primary/30 cursor-pointer transition-colors"
                >
                  <img
                    src={media.thumbnail_url}
                    alt={media.name}
                    className="w-14 h-9 rounded object-cover"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate">{media.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {media.duration}s
                    </p>
                  </div>
                  {media.type === "image" ? (
                    <Image className="w-3.5 h-3.5 text-muted-foreground" />
                  ) : (
                    <Film className="w-3.5 h-3.5 text-muted-foreground" />
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Sequência da Playlist</CardTitle>
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Clock className="w-4 h-4" />
                <span>{totalDuration}s</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {playlist.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-12">
                Adicione mídias da lista ao lado
              </p>
            ) : (
              <DragDropContext onDragEnd={onDragEnd}>
                <Droppable droppableId="playlist">
                  {(provided) => (
                    <div
                      {...provided.droppableProps}
                      ref={provided.innerRef}
                      className="space-y-2"
                    >
                      {playlist.map((media, index) => (
                        <Draggable
                          key={media.id}
                          draggableId={media.id}
                          index={index}
                        >
                          {(provided, snapshot) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              className={`flex items-center gap-3 p-3 rounded-lg border ${snapshot.isDragging ? "border-primary bg-primary/5 shadow-lg" : "border-border"}`}
                            >
                              <div {...provided.dragHandleProps}>
                                <GripVertical className="w-4 h-4 text-muted-foreground" />
                              </div>
                              <span className="text-xs font-mono text-muted-foreground w-6">
                                {index + 1}
                              </span>
                              <img
                                src={media.thumbnail_url}
                                alt={media.name}
                                className="w-16 h-10 rounded object-cover"
                              />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium truncate">
                                  {media.name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {media.type === "image" ? "Imagem" : "Vídeo"}
                                </p>
                              </div>
                              <div className="flex items-center gap-1">
                                <Input
                                  type="number"
                                  min="1"
                                  value={media.customDuration}
                                  onChange={(e) =>
                                    updateDuration(media.id, e.target.value)
                                  }
                                  className="w-16 h-8 text-xs text-center"
                                  disabled={media.type === "video"}
                                />
                                <span className="text-xs text-muted-foreground">
                                  s
                                </span>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => removeFromPlaylist(media.id)}
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </DragDropContext>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

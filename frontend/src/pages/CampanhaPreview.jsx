import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Maximize, Pause, Play, SkipForward } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { buscarCampanha } from "@/api/campanhas";
import { listarMidias } from "@/api/midias";

export default function CampanhaPreview() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const { data: campaign, isLoading: loadingCampaign } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => buscarCampanha(id),
    enabled: !!id,
  });
  const { data: mediaList = [] } = useQuery({
    queryKey: ["media"],
    queryFn: () => listarMidias(),
  });

  const medias = useMemo(() => {
    const ids = campaign?.media_order?.length
      ? campaign.media_order.map((item) => item.media_id || item)
      : campaign?.media_ids || [];
    const byId = new Map(mediaList.map((media) => [String(media.id), media]));
    return ids.map((mediaId) => byId.get(String(mediaId))).filter(Boolean);
  }, [campaign, mediaList]);

  useEffect(() => {
    if (!isPlaying || medias.length === 0) return;
    const duration = (medias[currentIndex]?.duration || 10) * 1000;
    const timer = setTimeout(() => {
      setCurrentIndex((prev) => (prev + 1) % medias.length);
    }, duration);
    return () => clearTimeout(timer);
  }, [isPlaying, currentIndex, medias]);

  const currentMedia = medias[currentIndex];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/campanhas")}>
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h2 className="text-xl font-bold">
            Preview: {loadingCampaign ? "Carregando..." : campaign?.name || "Campanha"}
          </h2>
          <p className="text-sm text-muted-foreground">
            {medias.length} mídias · Mídia {medias.length ? currentIndex + 1 : 0} de {medias.length}
          </p>
        </div>
      </div>

      <div className="flex justify-center">
        <div className="w-full max-w-4xl">
          <Card className="overflow-hidden bg-black">
            <div className="relative aspect-video flex items-center justify-center">
              {currentMedia ? (
                currentMedia.type === "video" ? (
                  <video
                    src={currentMedia.file_url}
                    className="w-full h-full object-cover"
                    controls
                  />
                ) : (
                  <img
                    src={currentMedia.thumbnail_url || currentMedia.file_url}
                    alt={currentMedia.name}
                    className="w-full h-full object-cover"
                  />
                )
              ) : (
                <p className="text-white/50">Nenhuma mídia vinculada</p>
              )}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                <p className="text-white text-sm font-medium">{currentMedia?.name}</p>
                <p className="text-white/60 text-xs">
                  {currentMedia ? `${currentMedia.duration || 10}s · ${currentMedia.type === "image" ? "Imagem" : "Vídeo"}` : ""}
                </p>
              </div>
            </div>
          </Card>

          <div className="flex items-center justify-center gap-3 mt-4">
            <Button
              variant="outline"
              size="icon"
              disabled={medias.length === 0}
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
            <Button
              variant="outline"
              size="icon"
              disabled={medias.length === 0}
              onClick={() => setCurrentIndex((currentIndex + 1) % medias.length)}
            >
              <SkipForward className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Maximize className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
            {medias.map((media, index) => (
              <div
                key={media.id}
                onClick={() => setCurrentIndex(index)}
                className={`shrink-0 w-20 h-14 rounded-lg overflow-hidden border-2 cursor-pointer transition-colors ${
                  index === currentIndex
                    ? "border-primary"
                    : "border-transparent opacity-60 hover:opacity-100"
                }`}
              >
                <img
                  src={media.thumbnail_url || media.file_url}
                  alt={media.name}
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

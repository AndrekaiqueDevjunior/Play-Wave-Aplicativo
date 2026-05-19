import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Maximize, Pause, Play, SkipForward } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { buscarCampanha } from "@/api/campanhas";
import { listarMidias } from "@/api/midias";
import { resolveMediaType, resolveMediaUrl, assetUrl } from "@/utils/mediaUtils";
import MediaThumb from "@/components/media/MediaThumb";

export default function CampanhaPreview() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const stageRef = useRef(null);

  const enterFullscreen = () => {
    const el = stageRef.current;
    if (!el) return;
    const req = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen || el.msRequestFullscreen;
    if (req) req.call(el).catch(() => {});
  };

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
            <div ref={stageRef} className="relative aspect-video flex items-center justify-center bg-black">
              {currentMedia ? (
                (() => {
                  const mType = resolveMediaType(currentMedia);
                  const mSrc  = resolveMediaUrl(currentMedia);
                  if (mType === "video") return (
                    <video
                      key={currentMedia.id}
                      src={mSrc}
                      className="w-full h-full object-cover"
                      controls
                      autoPlay
                      loop
                      playsInline
                    />
                  );
                  if (mType === "audio") return (
                    <div className="flex flex-col items-center gap-4 p-8 text-white">
                      <div className="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center">
                        <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>
                        </svg>
                      </div>
                      <p className="text-sm font-medium">{currentMedia.name}</p>
                      <audio key={currentMedia.id} src={mSrc} controls className="w-full max-w-xs" />
                    </div>
                  );
                  if (mType === "youtube" || mType === "vimeo" || mType === "external_url") return (
                    <iframe
                      key={currentMedia.id}
                      src={mSrc}
                      className="w-full h-full border-0"
                      title={currentMedia.name}
                      allow="autoplay; fullscreen; encrypted-media"
                      allowFullScreen
                    />
                  );
                  return (
                    <img
                      key={currentMedia.id}
                      src={assetUrl(currentMedia.thumbnail_url) || mSrc}
                      alt={currentMedia.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.currentTarget.src =
                          "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='112'%3E%3Crect width='200' height='112' fill='%23333'/%3E%3Ctext x='100' y='62' text-anchor='middle' fill='%23999' font-size='13'%3ESem preview%3C/text%3E%3C/svg%3E";
                      }}
                    />
                  );
                })()
              ) : (
                <p className="text-white/50">Nenhuma mídia vinculada</p>
              )}
              {currentMedia && resolveMediaType(currentMedia) !== "audio" && (
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                  <p className="text-white text-sm font-medium">{currentMedia.name}</p>
                  <p className="text-white/60 text-xs">
                    {`${currentMedia.duration || 10}s · ${
                      resolveMediaType(currentMedia) === "video" ? "Vídeo"
                      : resolveMediaType(currentMedia) === "youtube" ? "YouTube"
                      : resolveMediaType(currentMedia) === "vimeo" ? "Vimeo"
                      : resolveMediaType(currentMedia) === "audio" ? "Áudio"
                      : resolveMediaType(currentMedia) === "external_url" ? "Link externo"
                      : "Imagem"
                    }`}
                  </p>
                </div>
              )}
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
            <Button
              variant="outline"
              size="icon"
              disabled={medias.length === 0}
              onClick={enterFullscreen}
              title="Tela cheia"
            >
              <Maximize className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
            {medias.map((media, index) => (
              <div
                key={media.id}
                onClick={() => setCurrentIndex(index)}
                className={`shrink-0 w-20 h-14 rounded-lg overflow-hidden border-2 cursor-pointer transition-colors bg-muted ${
                  index === currentIndex
                    ? "border-primary"
                    : "border-transparent opacity-60 hover:opacity-100"
                }`}
              >
                <MediaThumb media={media} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

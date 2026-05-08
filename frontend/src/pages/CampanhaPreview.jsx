import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ArrowLeft, Play, Pause, SkipForward, Maximize } from "lucide-react";
import { mockCampaigns, mockMedia } from "@/lib/mockData";

export default function CampanhaPreview() {
  const navigate = useNavigate();
  const pathId = window.location.pathname.split("/")[2];
  const campaign =
    mockCampaigns.find((c) => c.id === pathId) || mockCampaigns[0];
  const medias = mockMedia.filter((m) => campaign.media_ids?.includes(m.id));

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

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
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate("/campanhas")}
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h2 className="text-xl font-bold">Preview: {campaign.name}</h2>
          <p className="text-sm text-muted-foreground">
            {medias.length} mídias · Mídia {currentIndex + 1} de {medias.length}
          </p>
        </div>
      </div>

      <div className="flex justify-center">
        <div className="w-full max-w-4xl">
          <Card className="overflow-hidden bg-black">
            <div className="relative aspect-video flex items-center justify-center">
              {currentMedia ? (
                <img
                  src={currentMedia.thumbnail_url || currentMedia.file_url}
                  alt={currentMedia.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <p className="text-white/50">Nenhuma mídia</p>
              )}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                <p className="text-white text-sm font-medium">
                  {currentMedia?.name}
                </p>
                <p className="text-white/60 text-xs">
                  {currentMedia?.duration}s ·{" "}
                  {currentMedia?.type === "image" ? "Imagem" : "Vídeo"}
                </p>
              </div>
            </div>
          </Card>

          <div className="flex items-center justify-center gap-3 mt-4">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? (
                <Pause className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4" />
              )}
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() =>
                setCurrentIndex((currentIndex + 1) % medias.length)
              }
            >
              <SkipForward className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="icon">
              <Maximize className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
            {medias.map((m, i) => (
              <div
                key={m.id}
                onClick={() => setCurrentIndex(i)}
                className={`shrink-0 w-20 h-14 rounded-lg overflow-hidden border-2 cursor-pointer transition-colors ${
                  i === currentIndex
                    ? "border-primary"
                    : "border-transparent opacity-60 hover:opacity-100"
                }`}
              >
                <img
                  src={m.thumbnail_url}
                  alt={m.name}
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

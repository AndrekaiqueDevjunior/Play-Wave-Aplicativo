import React from "react";
import { Image as ImageIcon, Film, Music, Globe, Link2 } from "lucide-react";
import { assetUrl, resolveMediaType } from "@/utils/mediaUtils";
import { cn } from "@/lib/utils";

const ICON_BY_TYPE = {
  image: ImageIcon,
  video: Film,
  audio: Music,
  youtube: Globe,
  vimeo: Globe,
  external_url: Link2,
};

/**
 * Renderiza a melhor pré-visualização possível para um item de mídia.
 *
 * Vídeos sem thumbnail_url renderizam <video preload="metadata"> — o browser
 * baixa só o cabeçalho e mostra o primeiro frame como pôster, sem rodar.
 *
 * Props:
 *   media: objeto de mídia (id, type, file_url, thumbnail_url, name)
 *   className: classes para o wrapper (controle do tamanho/aspect-ratio)
 *   fit: "cover" | "contain" (default "cover")
 */
export default function MediaThumb({ media, className, fit = "cover" }) {
  const type = media ? resolveMediaType(media) : null;
  const objectFit = fit === "contain" ? "object-contain" : "object-cover";

  if (!media) return null;

  if (media.thumbnail_url) {
    return (
      <img
        src={assetUrl(media.thumbnail_url)}
        alt={media.name || ""}
        className={cn("w-full h-full", objectFit, className)}
      />
    );
  }

  if (type === "image") {
    return (
      <img
        src={assetUrl(media.file_url)}
        alt={media.name || ""}
        className={cn("w-full h-full", objectFit, className)}
      />
    );
  }

  if (type === "video") {
    return (
      <video
        src={assetUrl(media.file_url)}
        preload="metadata"
        muted
        playsInline
        // #t=0.5 pede ao browser para posicionar no segundo 0.5 (primeiro frame nítido).
        // Funciona em Chrome/Firefox/Safari como fallback de poster automático.
        poster={undefined}
        className={cn("w-full h-full pointer-events-none", objectFit, className)}
        onLoadedMetadata={(e) => {
          try { e.currentTarget.currentTime = 0.5; } catch { /* ignore */ }
        }}
      />
    );
  }

  const Icon = ICON_BY_TYPE[type] || ImageIcon;
  return (
    <div className={cn("w-full h-full flex items-center justify-center bg-muted", className)}>
      <Icon className="w-8 h-8 text-muted-foreground/50" />
    </div>
  );
}

import React, { useState, useEffect, useRef } from "react";
import { resolveMediaType, resolveMediaUrl, assetUrl } from "@/utils/mediaUtils";

const PLACEHOLDER =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='112'%3E%3Crect width='200' height='112' fill='%23111'/%3E%3Ctext x='100' y='62' text-anchor='middle' fill='%23555' font-size='13' font-family='sans-serif'%3ESem preview%3C/text%3E%3C/svg%3E";

export default function MediaRenderer({ media, onEnded, progress, videoMuted = true }) {
  const [visible, setVisible] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [needsGesture, setNeedsGesture] = useState(false);
  const videoRef = useRef(null);

  useEffect(() => {
    setVisible(false);
    setImgError(false);
    const t = setTimeout(() => setVisible(true), 80);
    return () => clearTimeout(t);
  }, [media?.id, videoMuted]);

  // Após o navegador bloquear autoplay com som, registra listener global
  // one-shot. No primeiro gesto do usuário, des-muta o vídeo atual e retoma.
  useEffect(() => {
    if (!needsGesture) return;
    const unmute = () => {
      const el = videoRef.current;
      if (el) {
        el.muted = false;
        el.play().catch(() => {});
      }
      setNeedsGesture(false);
    };
    window.addEventListener("pointerdown", unmute, { once: true });
    window.addEventListener("keydown", unmute, { once: true });
    window.addEventListener("touchstart", unmute, { once: true });
    return () => {
      window.removeEventListener("pointerdown", unmute);
      window.removeEventListener("keydown", unmute);
      window.removeEventListener("touchstart", unmute);
    };
  }, [needsGesture]);

  if (!media) return null;

  const type    = resolveMediaType(media);
  const src     = resolveMediaUrl(media);
  const fadeClass = `transition-opacity duration-700 ${visible ? "opacity-100" : "opacity-0"}`;

  const renderContent = () => {
    switch (type) {
      case "video":
        return (
          <video
            key={media.id}
            ref={videoRef}
            src={src}
            autoPlay
            muted={videoMuted}
            playsInline
            className={`w-full h-full object-cover ${fadeClass}`}
            onCanPlay={(event) => {
              const el = event.currentTarget;
              el.muted = videoMuted;
              el.play().then(() => {
                if (!videoMuted) setNeedsGesture(false);
              }).catch(() => {
                // Autoplay com som é bloqueado sem user activation.
                // Toca mudo e arma listener pro primeiro gesto desmutar.
                el.muted = true;
                el.play().catch(() => {});
                if (!videoMuted) setNeedsGesture(true);
              });
            }}
            onEnded={onEnded}
            onError={onEnded}
          />
        );

      case "audio":
        return (
          <div className={`flex flex-col items-center justify-center gap-4 w-full h-full bg-zinc-900 text-white ${fadeClass}`}>
            <div className="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center">
              <svg className="w-10 h-10" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
              </svg>
            </div>
            <p className="text-sm font-medium px-4 text-center truncate max-w-xs">{media.name}</p>
            <audio key={media.id} src={src} autoPlay controls className="w-64" onEnded={onEnded} />
          </div>
        );

      case "youtube":
      case "vimeo":
      case "external_url":
        return (
          <iframe
            key={media.id}
            src={src}
            className={`w-full h-full border-0 ${fadeClass}`}
            title={media.name}
            allow="autoplay; fullscreen; encrypted-media"
            allowFullScreen
          />
        );

      default:
        return (
          <img
            key={media.id}
            src={imgError ? PLACEHOLDER : (assetUrl(media.thumbnail_url) || src || PLACEHOLDER)}
            alt={media.name}
            className={`w-full h-full object-cover ${fadeClass}`}
            onError={() => setImgError(true)}
          />
        );
    }
  };

  return (
    <div className="absolute inset-0">
      {renderContent()}
      {needsGesture && (
        <div className="absolute top-4 right-4 px-3 py-1.5 rounded-full bg-black/70 text-white text-xs backdrop-blur-sm pointer-events-none">
          Clique para ativar o som
        </div>
      )}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/10">
        <div
          className="h-full bg-white/40 transition-all duration-1000 ease-linear"
          style={{ width: `${(progress ?? 0) * 100}%` }}
        />
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef, useCallback } from "react";
import { resolveMediaType, resolveMediaUrl, assetUrl } from "@/utils/mediaUtils";
import Platform from "@/player-core/platform";

const PLACEHOLDER =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='112'%3E%3Crect width='200' height='112' fill='%23111'/%3E%3Ctext x='100' y='62' text-anchor='middle' fill='%23555' font-size='13' font-family='sans-serif'%3ESem preview%3C/text%3E%3C/svg%3E";

const VIDEO_EVENTS = [
  "loadstart",
  "loadedmetadata",
  "loadeddata",
  "canplay",
  "canplaythrough",
  "play",
  "playing",
  "pause",
  "waiting",
  "stalled",
  "suspend",
  "error",
  "ended",
];

function capacitorPlatform() {
  return window.Capacitor?.getPlatform?.() || (Platform.isCapacitor ? "capacitor" : "web");
}

function describeMediaError(error) {
  if (!error) return null;
  const names = {
    1: "MEDIA_ERR_ABORTED",
    2: "MEDIA_ERR_NETWORK",
    3: "MEDIA_ERR_DECODE",
    4: "MEDIA_ERR_SRC_NOT_SUPPORTED",
  };
  return {
    code: error.code,
    name: names[error.code] || "MEDIA_ERR_UNKNOWN",
    message: error.message || null,
  };
}

function videoSnapshot(video, { eventName, media, src, type, extra = {} }) {
  return {
    tag: "PLAYER_VIDEO_DEBUG",
    timestamp: new Date().toISOString(),
    event: eventName,
    media_id: media?.id || null,
    media_name: media?.name || null,
    media_type: type,
    url: src,
    duration: Number.isFinite(video?.duration) ? video.duration : null,
    muted: Boolean(video?.muted),
    defaultMuted: Boolean(video?.defaultMuted),
    autoplay: Boolean(video?.autoplay),
    paused: Boolean(video?.paused),
    ended: Boolean(video?.ended),
    readyState: video?.readyState ?? null,
    networkState: video?.networkState ?? null,
    currentTime: video?.currentTime ?? null,
    error: describeMediaError(video?.error),
    platform: Platform.name,
    capacitorPlatform: capacitorPlatform(),
    isCapacitor: Platform.isCapacitor,
    userAgent: navigator.userAgent,
    ...extra,
  };
}

/**
 * Aquece o cache HTTP do navegador para a próxima mídia da fila, enquanto a
 * atual ainda está tocando. Sem isso, o vídeo/imagem seguinte só começa a
 * baixar no instante exato da troca — em conexões lentas ou arquivos grandes
 * isso aparece como travamento/tela preta nos primeiros segundos do item.
 *
 * Não usa <link rel="preload"> (precisaria de `as` correto por tipo e gera
 * warnings de "preloaded but not used" se o item for pulado/trocado antes da
 * vez); em vez disso, cria um elemento offscreen real do mesmo tipo, que o
 * browser já mantém em cache de disco/memória quando o MediaRenderer
 * principal pedir a mesma URL.
 */
function MediaPreloader({ media }) {
  const type = media ? resolveMediaType(media) : null;
  const src = media ? resolveMediaUrl(media) : null;
  if (!src || (type !== "video" && type !== "image" && type !== "audio")) return null;

  const hiddenStyle = { position: "absolute", width: 0, height: 0, opacity: 0, pointerEvents: "none" };

  if (type === "video") {
    return (
      <video key={`preload-${media.id}`} src={src} preload="auto" muted style={hiddenStyle} aria-hidden="true" />
    );
  }
  if (type === "audio") {
    return <audio key={`preload-${media.id}`} src={src} preload="auto" muted style={hiddenStyle} aria-hidden="true" />;
  }
  return (
    <img key={`preload-${media.id}`} src={src} alt="" style={hiddenStyle} aria-hidden="true" />
  );
}

const MediaRenderer = React.memo(function MediaRenderer({
  media,
  nextMedia,
  onEnded,
  onError,
  onDebug,
  progress,
  videoMuted = true,
}) {
  const progressBarRef = useRef(null);
  useEffect(() => {
    if (progressBarRef.current) {
      progressBarRef.current.style.width = `${(progress ?? 0) * 100}%`;
    }
  }, [progress]);

  const [visible, setVisible] = useState(false);
  const [imgError, setImgError] = useState(false);
  const [needsGesture, setNeedsGesture] = useState(false);
  const videoRef = useRef(null);
  const reportedFailureRef = useRef(false);

  const shouldForceMutedAutoplay =
    Platform.isAndroid || Platform.isIOS || Platform.isSmartTV || Platform.isCapacitor;

  const type = media ? resolveMediaType(media) : null;
  const src = media ? resolveMediaUrl(media) : null;
  const fadeClass = `transition-opacity duration-700 ${visible ? "opacity-100" : "opacity-0"}`;

  const emitDebug = useCallback((eventName, extra = {}) => {
    const video = videoRef.current;
    if (!video || type !== "video") return null;
    const payload = videoSnapshot(video, { eventName, media, src, type, extra });
    console.log("[PLAYER_VIDEO_DEBUG]", payload);
    onDebug?.(payload);
    return payload;
  }, [media, onDebug, src, type]);

  const reportVideoFailure = useCallback((reason, extra = {}) => {
    if (reportedFailureRef.current) return;
    reportedFailureRef.current = true;
    const payload = emitDebug(reason, extra) || { event: reason, media, src, type, ...extra };
    console.error("[PLAYER_VIDEO_ERROR]", payload);
    onError?.(payload);
  }, [emitDebug, media, onError, src, type]);

  const attemptPlay = useCallback((reason) => {
    const video = videoRef.current;
    if (!video || type !== "video") return;

    const mustStartMuted = videoMuted || shouldForceMutedAutoplay;
    video.muted = mustStartMuted;
    video.defaultMuted = mustStartMuted;
    video.setAttribute("muted", "");
    video.setAttribute("playsinline", "");
    video.setAttribute("webkit-playsinline", "");

    emitDebug(`play_attempt:${reason}`, { mustStartMuted });

    video.play().then(() => {
      setNeedsGesture(!videoMuted && mustStartMuted);
      emitDebug(`play_success:${reason}`, { mustStartMuted });
    }).catch((error) => {
      console.error("Falha no autoplay:", error);
      emitDebug(`play_failed:${reason}`, {
        mustStartMuted,
        playError: {
          name: error?.name || null,
          message: error?.message || String(error),
        },
      });

      video.muted = true;
      video.defaultMuted = true;
      video.setAttribute("muted", "");
      video.play().then(() => {
        setNeedsGesture(!videoMuted);
        emitDebug(`muted_fallback_success:${reason}`);
      }).catch((fallbackError) => {
        reportVideoFailure("muted_fallback_failed", {
          playError: {
            name: fallbackError?.name || null,
            message: fallbackError?.message || String(fallbackError),
          },
        });
      });
    });
  }, [emitDebug, reportVideoFailure, shouldForceMutedAutoplay, type, videoMuted]);

  useEffect(() => {
    setVisible(false);
    setImgError(false);
    setNeedsGesture(false);
    reportedFailureRef.current = false;
    const t = setTimeout(() => setVisible(true), 80);
    return () => clearTimeout(t);
  }, [media?.id, videoMuted]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || type !== "video") return;

    const handlers = VIDEO_EVENTS.map((eventName) => {
      const handler = () => {
        emitDebug(eventName);
        if (eventName === "canplay" || eventName === "loadeddata") {
          attemptPlay(eventName);
        }
        if (eventName === "error") {
          reportVideoFailure("video_element_error");
        }
        if (eventName === "ended") {
          onEnded?.("ended");
        }
      };
      video.addEventListener(eventName, handler);
      return [eventName, handler];
    });

    video.load();
    if (video.readyState >= 2) {
      attemptPlay("readyState");
    }

    return () => {
      handlers.forEach(([eventName, handler]) => {
        video.removeEventListener(eventName, handler);
      });
    };
  }, [attemptPlay, emitDebug, onEnded, reportVideoFailure, type, media?.id]);

  useEffect(() => {
    if (!needsGesture) return;
    const unmute = () => {
      const video = videoRef.current;
      if (video) {
        video.muted = false;
        video.defaultMuted = false;
        video.removeAttribute("muted");
        video.play().then(() => {
          emitDebug("unmute_after_gesture_success");
        }).catch((error) => {
          console.error("[PLAYER_VIDEO_ERROR] unmute play failed", error);
          emitDebug("unmute_after_gesture_failed", {
            playError: {
              name: error?.name || null,
              message: error?.message || String(error),
            },
          });
        });
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
  }, [emitDebug, needsGesture]);

  if (!media) return null;

  const renderContent = () => {
    switch (type) {
      case "video":
        return (
          <video
            key={media.id}
            ref={videoRef}
            src={src}
            autoPlay
            muted={videoMuted || shouldForceMutedAutoplay}
            defaultMuted={videoMuted || shouldForceMutedAutoplay}
            playsInline
            preload="auto"
            disablePictureInPicture
            controls={false}
            className={`w-full h-full object-cover ${fadeClass}`}
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
            <audio key={media.id} src={src} autoPlay controls className="w-64" onEnded={() => onEnded?.("audio_ended")} />
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
            onError={() => onError?.({ event: "iframe_error", media, src, type })}
          />
        );

      default:
        return (
          <img
            key={media.id}
            src={imgError ? PLACEHOLDER : (assetUrl(media.thumbnail_url) || src || PLACEHOLDER)}
            alt={media.name}
            className={`w-full h-full object-cover ${fadeClass}`}
            onError={() => {
              setImgError(true);
              onError?.({ event: "image_error", media, src, type });
            }}
          />
        );
    }
  };

  return (
    <div className="absolute inset-0">
      {renderContent()}
      {needsGesture && (
        <div className="absolute top-4 right-4 px-3 py-1.5 rounded-full bg-black/70 text-white text-xs backdrop-blur-sm pointer-events-none">
          Toque para ativar o som
        </div>
      )}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/10">
        <div ref={progressBarRef} className="h-full bg-white/40 transition-all duration-1000 ease-linear" />
      </div>
      <MediaPreloader media={nextMedia} />
    </div>
  );
});

export default MediaRenderer;

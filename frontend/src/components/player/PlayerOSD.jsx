import React, { useState, useEffect } from "react";
import { Music, Radio } from "lucide-react";

const DEFAULT_OSD_CONFIG = {
  show_current_audio: true,
  position: "top_right",
  duration_seconds: 0,
  opacity: 0.6,
  font_size: "medium",
};

const POSITION_CLASSES = {
  top_left: "top-16 left-5",
  top_right: "top-16 right-5",
  bottom_left: "bottom-20 left-5",
  bottom_right: "bottom-20 right-5",
};

const FONT_SIZE_CLASSES = {
  small: "text-xs",
  medium: "text-sm",
  large: "text-base",
};

/**
 * On-Screen Display — mostra nome da mídia brevemente ao trocar, e relógio/logo sempre visível.
 */
export default function PlayerOSD({
  media,
  totalItems,
  currentIndex,
  deviceName,
  currentAudioTrack,
  audioEnabled = true,
  radioActive = false,
  osdConfig = DEFAULT_OSD_CONFIG,
}) {
  const [showInfo, setShowInfo] = useState(true);
  const [showAudioOverlay, setShowAudioOverlay] = useState(false);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    setShowInfo(true);
    const t = setTimeout(() => setShowInfo(false), 4000);
    return () => clearTimeout(t);
  }, [media?.file_url]);

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 30_000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    // Show OSD when radio is active OR when audioEnabled (video audio)
    const shouldShow = (radioActive || audioEnabled) && !!currentAudioTrack && osdConfig.show_current_audio;
    if (!shouldShow) {
      setShowAudioOverlay(false);
      return;
    }
    setShowAudioOverlay(true);
    if (osdConfig.duration_seconds > 0) {
      const t = setTimeout(() => setShowAudioOverlay(false), osdConfig.duration_seconds * 1000);
      return () => clearTimeout(t);
    }
  }, [
    currentAudioTrack?.id,
    audioEnabled,
    radioActive,
    osdConfig.show_current_audio,
    osdConfig.duration_seconds,
  ]);

  const positionClass = POSITION_CLASSES[osdConfig.position] || POSITION_CLASSES.top_right;
  const fontClass = FONT_SIZE_CLASSES[osdConfig.font_size] || FONT_SIZE_CLASSES.medium;
  const opacity = Math.max(0, Math.min(1, osdConfig.opacity ?? 0.6));

  return (
    <>
      {/* Top-left: logo + device name */}
      <div className="absolute top-4 left-5 z-10 flex items-center gap-2 opacity-40 hover:opacity-80 transition-opacity">
        <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
          <Radio className="w-3.5 h-3.5 text-white" />
        </div>
        {deviceName && (
          <span className="text-white text-xs font-medium tracking-wide">
            {deviceName}
          </span>
        )}
      </div>

      {/* Top-right: clock */}
      <div className="absolute top-4 right-5 z-10 opacity-40 hover:opacity-80 transition-opacity">
        <span className="text-white text-sm font-mono tabular-nums">
          {time.toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {currentAudioTrack && (
        <div
          className={`absolute ${positionClass} z-20 transition-opacity duration-300 ${
            showAudioOverlay ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          <div
            className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 backdrop-blur-sm ${fontClass}`}
            style={{ backgroundColor: `rgba(0, 0, 0, ${opacity})` }}
          >
            <Music className="w-3.5 h-3.5 text-white flex-shrink-0" />
            <span className="max-w-[30vw] truncate text-white font-medium">
              {currentAudioTrack.name}
            </span>
          </div>
        </div>
      )}

      {/* Bottom: media info — appears briefly on media change */}
      <div
        className={`absolute bottom-4 left-5 right-5 z-10 transition-all duration-500 ${showInfo ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}
      >
        <div className="inline-flex items-center gap-3 bg-black/50 backdrop-blur-sm rounded-xl px-4 py-2.5">
          <div>
            <p className="text-white text-sm font-medium leading-tight">
              {media?.name}
            </p>
            <p className="text-white/50 text-xs mt-0.5">
              {currentIndex + 1} / {totalItems} ·{" "}
              {media?.type === "video" ? "Vídeo" : "Imagem"}
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

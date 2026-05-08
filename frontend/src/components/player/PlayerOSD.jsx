import React, { useState, useEffect } from "react";
import { Radio } from "lucide-react";

/**
 * On-Screen Display — mostra nome da mídia brevemente ao trocar, e relógio/logo sempre visível.
 */
export default function PlayerOSD({
  media,
  totalItems,
  currentIndex,
  deviceName,
}) {
  const [showInfo, setShowInfo] = useState(true);
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

  return (
    <>
      {/* Top-left: logo + device name */}
      <div className="absolute top-4 left-5 flex items-center gap-2 opacity-40 hover:opacity-80 transition-opacity">
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
      <div className="absolute top-4 right-5 opacity-40 hover:opacity-80 transition-opacity">
        <span className="text-white text-sm font-mono tabular-nums">
          {time.toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {/* Bottom: media info — appears briefly on media change */}
      <div
        className={`absolute bottom-4 left-5 right-5 transition-all duration-500 ${showInfo ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}
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

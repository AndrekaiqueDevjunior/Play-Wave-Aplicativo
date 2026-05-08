import React, { useState, useEffect } from "react";

export default function MediaRenderer({ media, onEnded, progress }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(false);
    const t = setTimeout(() => setVisible(true), 80);
    return () => clearTimeout(t);
  }, [media?.file_url]);

  if (!media) return null;

  return (
    <div className="absolute inset-0">
      {media.type === "video" ? (
        <video
          key={media.file_url}
          src={media.file_url}
          autoPlay
          muted
          playsInline
          className={`w-full h-full object-cover transition-opacity duration-700 ${visible ? "opacity-100" : "opacity-0"}`}
          onEnded={onEnded}
        />
      ) : (
        <img
          key={media.file_url}
          src={media.file_url}
          alt={media.name}
          className={`w-full h-full object-cover transition-opacity duration-700 ${visible ? "opacity-100" : "opacity-0"}`}
        />
      )}

      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/10">
        <div
          className="h-full bg-white/40 transition-all duration-1000 ease-linear"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </div>
  );
}

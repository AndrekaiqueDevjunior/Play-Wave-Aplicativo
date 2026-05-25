import { Music } from "lucide-react";

const DEFAULT_CONFIG = {
  show_current_audio: true,
  position: "top_right",
  duration_seconds: 8,
  opacity: 0.6,
  font_size: "medium",
};

const POSITION_CLASSES = {
  top_left: "top-3 left-3",
  top_right: "top-3 right-3",
  bottom_left: "bottom-3 left-3",
  bottom_right: "bottom-3 right-3",
};

const FONT_CLASSES = {
  small: "text-[10px]",
  medium: "text-xs",
  large: "text-sm",
};

export function normalizeOSDConfig(config = {}) {
  return {
    ...DEFAULT_CONFIG,
    ...Object.fromEntries(
      Object.entries(config || {}).filter(([, value]) => value !== null && value !== undefined),
    ),
  };
}

export function OSDConfigPreview({ config }) {
  const resolved = normalizeOSDConfig(config);
  const positionClass = POSITION_CLASSES[resolved.position] || POSITION_CLASSES.top_right;
  const fontClass = FONT_CLASSES[resolved.font_size] || FONT_CLASSES.medium;
  const opacity = Math.max(0, Math.min(1, resolved.opacity ?? 0.6));

  return (
    <div className="relative w-full overflow-hidden rounded-md border bg-slate-950 aspect-video">
      <div className="absolute inset-0 bg-[linear-gradient(135deg,#172033,#090d14_55%,#111827)]" />
      <div className="absolute left-4 top-4 h-3 w-24 rounded bg-white/10" />
      <div className="absolute bottom-4 left-4 h-8 w-40 rounded bg-white/10" />

      {resolved.show_current_audio && (
        <div className={`absolute ${positionClass}`}>
          <div
            className={`inline-flex max-w-[70%] items-center gap-1.5 rounded px-2 py-1 ${fontClass}`}
            style={{ backgroundColor: `rgba(0, 0, 0, ${opacity})` }}
          >
            <Music className="h-3 w-3 shrink-0 text-white" />
            <span className="truncate text-white">Nome da Musica Exemplo</span>
          </div>
        </div>
      )}
    </div>
  );
}

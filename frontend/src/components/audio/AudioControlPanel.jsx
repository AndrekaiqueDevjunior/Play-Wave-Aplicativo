import React from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  Shuffle,
  Repeat,
  Radio,
} from "lucide-react";
import { useAudioManager, useAudioVolume } from "@/hooks/useAudioManager";
import { AUDIO_STATE, AUDIO_MODE } from "@/lib/audioManager";
import { cn } from "@/lib/utils";

const formatTime = (seconds) => {
  if (!seconds) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

export default function AudioControlPanel({ className = "" }) {
  const {
    current,
    isPlaying,
    currentTime,
    duration,
    radioMode,
    pause,
    resume,
    nextTrack,
    previousTrack,
    setRadioMode,
  } = useAudioManager();

  const { volume, setVolume } = useAudioVolume();

  const isRadio = current === AUDIO_STATE.RADIO;

  return (
    <div className={cn("bg-white border rounded-lg p-4 space-y-4", className)}>
      {/* Status */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-blue-500" />
          <span className="font-medium">
            {current === AUDIO_STATE.SILENT && "Silêncio"}
            {current === AUDIO_STATE.RADIO && "Rádio"}
            {current === AUDIO_STATE.MEDIA_AUDIO && "Vídeo"}
            {current === AUDIO_STATE.SPOT && "Anúncio"}
          </span>
        </div>
        <span className="text-gray-500">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>

      {/* Playback Controls */}
      <div className="flex items-center justify-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={previousTrack}
          disabled={!isRadio}
          title="Faixa anterior"
        >
          <SkipBack className="h-4 w-4" />
        </Button>

        <Button
          size="lg"
          onClick={isPlaying ? pause : resume}
          className="w-16 h-16"
          title={isPlaying ? "Pausar" : "Reproduzir"}
        >
          {isPlaying ? (
            <Pause className="h-6 w-6" />
          ) : (
            <Play className="h-6 w-6" />
          )}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={nextTrack}
          disabled={!isRadio}
          title="Próxima faixa"
        >
          <SkipForward className="h-4 w-4" />
        </Button>
      </div>

      {/* Volume */}
      <div className="flex items-center gap-2">
        <VolumeX className="h-4 w-4 text-gray-500" />
        <Slider
          value={[volume * 100]}
          onValueChange={(v) => setVolume(v[0] / 100)}
          min={0}
          max={100}
          step={1}
          className="flex-1"
        />
        <Volume2 className="h-4 w-4 text-gray-500" />
        <span className="text-sm w-8 text-right">
          {Math.round(volume * 100)}%
        </span>
      </div>

      {/* Radio Mode Selector */}
      {isRadio && (
        <div className="flex gap-2">
          <Button
            variant={radioMode === AUDIO_MODE.SEQUENTIAL ? "default" : "outline"}
            size="sm"
            onClick={() => setRadioMode(AUDIO_MODE.SEQUENTIAL)}
            title="Reprodução sequencial"
            className="flex-1"
          >
            <span>Sequencial</span>
          </Button>

          <Button
            variant={radioMode === AUDIO_MODE.SHUFFLE ? "default" : "outline"}
            size="sm"
            onClick={() => setRadioMode(AUDIO_MODE.SHUFFLE)}
            title="Embaralhado"
            className="flex-1"
          >
            <Shuffle className="h-4 w-4 mr-1" />
            Shuffle
          </Button>

          <Button
            variant={radioMode === AUDIO_MODE.LOOP ? "default" : "outline"}
            size="sm"
            onClick={() => setRadioMode(AUDIO_MODE.LOOP)}
            title="Loop"
            className="flex-1"
          >
            <Repeat className="h-4 w-4 mr-1" />
            Loop
          </Button>
        </div>
      )}
    </div>
  );
}

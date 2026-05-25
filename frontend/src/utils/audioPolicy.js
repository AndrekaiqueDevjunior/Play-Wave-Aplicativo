// @ts-nocheck
/**
 * audioPolicy.js — SPEC 005: constantes e labels de política de áudio.
 *
 * Compartilhado entre o hook useAudioConflictResolver (player) e os
 * componentes admin (AudioPolicySelector, CampaignFormModal, etc.).
 */

export const AUDIO_POLICY = {
  AUTO: "auto",
  RADIO_ONLY: "radio_only",
  MEDIA_AUDIO_ONLY: "media_audio_only",
  MIX: "mix",
  MUTED_VIDEO_WITH_RADIO: "muted_video_with_radio",
};

export const AUDIO_POLICY_OPTIONS = [
  {
    value: AUDIO_POLICY.AUTO,
    label: "Automático (recomendado)",
    description:
      "Se a mídia tem áudio, pausa a rádio. Se não tem, mantém a rádio.",
  },
  {
    value: AUDIO_POLICY.RADIO_ONLY,
    label: "Apenas rádio",
    description: "Vídeo sempre mudo. Rádio sempre ativa.",
  },
  {
    value: AUDIO_POLICY.MEDIA_AUDIO_ONLY,
    label: "Apenas áudio da mídia",
    description: "Rádio pausa enquanto vídeo com áudio toca.",
  },
  {
    value: AUDIO_POLICY.MIX,
    label: "Misturar ambos",
    description:
      "Áudio da mídia + rádio simultaneamente. Pode soar confuso.",
  },
  {
    value: AUDIO_POLICY.MUTED_VIDEO_WITH_RADIO,
    label: "Vídeo mudo com rádio ambiente",
    description: "Vídeo sempre mudo. Rádio ativa quando configurada.",
  },
];

/** Map rápido de value → label para exibição inline. */
export const AUDIO_POLICY_LABEL = Object.fromEntries(
  AUDIO_POLICY_OPTIONS.map((o) => [o.value, o.label])
);

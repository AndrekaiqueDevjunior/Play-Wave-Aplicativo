/**
 * media-gen.ts — gera assets de mídia mínimos e VÁLIDOS em memória, para os
 * uploads não dependerem de binários commitados no repo.
 *
 * - genWav(): WAV PCM de silêncio com duração real (ffprobe consegue ler a
 *   duração → valida o teste de "duração automática").
 * - VIDEO: gerar MP4 válido programaticamente é inviável. Os testes que exigem
 *   vídeo real usam fixtures/media/sample.mp4 se existir; senão, são pulados
 *   com motivo claro (ver helpers/factories.ts).
 */

/** Gera um WAV PCM 16-bit mono de `seconds` de silêncio (8kHz). */
export function genWav(seconds = 2, sampleRate = 8000): { name: string; mimeType: string; buffer: Buffer } {
  const numSamples = Math.max(1, Math.floor(seconds * sampleRate));
  const dataSize = numSamples * 2; // 16-bit mono
  const buffer = Buffer.alloc(44 + dataSize);

  buffer.write("RIFF", 0);
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write("WAVE", 8);
  buffer.write("fmt ", 12);
  buffer.writeUInt32LE(16, 16); // subchunk1 size
  buffer.writeUInt16LE(1, 20); // PCM
  buffer.writeUInt16LE(1, 22); // mono
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * 2, 28); // byte rate
  buffer.writeUInt16LE(2, 32); // block align
  buffer.writeUInt16LE(16, 34); // bits per sample
  buffer.write("data", 36);
  buffer.writeUInt32LE(dataSize, 40);
  // amostras já são zero (silêncio) por Buffer.alloc

  const id = Math.random().toString(36).slice(2, 8);
  return { name: `e2e-audio-${id}.wav`, mimeType: "audio/wav", buffer };
}

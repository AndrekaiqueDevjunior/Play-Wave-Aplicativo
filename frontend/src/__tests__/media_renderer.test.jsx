/**
 * Testes SPEC 014 — MediaRenderer (preload da próxima mídia + memo contra
 * re-render por `progress`).
 */
import React from "react";
import { createRoot } from "react-dom/client";
import { act } from "react-dom/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import MediaRenderer from "../components/player/MediaRenderer";

let root;
let container;

function render(element) {
  if (!container) {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  }
  act(() => {
    root.render(element);
  });
}

beforeEach(() => {
  HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  HTMLMediaElement.prototype.pause = vi.fn();
  HTMLMediaElement.prototype.load = vi.fn();
});

afterEach(() => {
  if (root) {
    act(() => root.unmount());
  }
  root = null;
  container?.remove();
  container = null;
  vi.restoreAllMocks();
});

const videoMedia = {
  id: "media-1",
  type: "video",
  name: "Vídeo atual",
  file_url: "/uploads/media/atual.mp4",
};

const nextVideoMedia = {
  id: "media-2",
  type: "video",
  name: "Próximo vídeo",
  file_url: "/uploads/media/proximo.mp4",
};

const nextImageMedia = {
  id: "media-3",
  type: "image",
  name: "Próxima imagem",
  file_url: "/uploads/media/proxima.jpg",
};

describe("MediaRenderer — preload da próxima mídia", () => {
  it("renderiza um <video> oculto para a próxima mídia quando ela é vídeo", () => {
    render(<MediaRenderer media={videoMedia} nextMedia={nextVideoMedia} progress={0} />);

    const videos = container.querySelectorAll("video");
    // 1 visível (atual) + 1 oculto (preload do próximo)
    expect(videos.length).toBe(2);
    const preloadVideo = Array.from(videos).find((v) => v.src.includes("proximo.mp4"));
    expect(preloadVideo).toBeTruthy();
    expect(preloadVideo.style.opacity).toBe("0");
  });

  it("renderiza um <img> oculto para a próxima mídia quando ela é imagem", () => {
    render(<MediaRenderer media={videoMedia} nextMedia={nextImageMedia} progress={0} />);

    const imgs = container.querySelectorAll("img");
    const preloadImg = Array.from(imgs).find((img) => img.src.includes("proxima.jpg"));
    expect(preloadImg).toBeTruthy();
  });

  it("não renderiza preload quando não há próxima mídia", () => {
    render(<MediaRenderer media={videoMedia} nextMedia={null} progress={0} />);

    const videos = container.querySelectorAll("video");
    // Apenas o vídeo atual, sem elemento extra de preload
    expect(videos.length).toBe(1);
  });

  it("troca o preload quando nextMedia muda (não fica preso na mídia antiga)", () => {
    render(<MediaRenderer media={videoMedia} nextMedia={nextVideoMedia} progress={0} />);
    let videos = container.querySelectorAll("video");
    expect(Array.from(videos).some((v) => v.src.includes("proximo.mp4"))).toBe(true);

    render(<MediaRenderer media={videoMedia} nextMedia={nextImageMedia} progress={0} />);
    videos = container.querySelectorAll("video");
    expect(Array.from(videos).some((v) => v.src.includes("proximo.mp4"))).toBe(false);
    const imgs = container.querySelectorAll("img");
    expect(Array.from(imgs).some((img) => img.src.includes("proxima.jpg"))).toBe(true);
  });
});

describe("MediaRenderer — memo evita re-render quando nenhuma prop muda", () => {
  it("não recria o elemento <video> principal quando as props são as mesmas (re-render do pai sem mudança real)", () => {
    const onEnded = vi.fn();
    render(<MediaRenderer media={videoMedia} nextMedia={null} progress={0} onEnded={onEnded} />);
    const firstVideo = container.querySelector("video");

    // Mesmas props (mesmas referências) — memo deve pular o re-render
    render(<MediaRenderer media={videoMedia} nextMedia={null} progress={0} onEnded={onEnded} />);
    const secondVideo = container.querySelector("video");

    // Mesmo nó DOM — key={media.id} não muda e o memo evitou trabalho extra
    expect(firstVideo).toBe(secondVideo);
  });

  it("atualiza a largura da barra de progresso quando `progress` muda", () => {
    render(<MediaRenderer media={videoMedia} nextMedia={null} progress={0.25} />);
    let bar = container.querySelector(".bg-white\\/40");
    expect(bar.style.width).toBe("25%");

    render(<MediaRenderer media={videoMedia} nextMedia={null} progress={0.75} />);
    bar = container.querySelector(".bg-white\\/40");
    expect(bar.style.width).toBe("75%");
  });

  it("recria o vídeo principal quando `media.id` muda (troca real de conteúdo)", () => {
    render(<MediaRenderer media={videoMedia} nextMedia={null} progress={0} />);
    const firstVideo = container.querySelector("video");

    render(<MediaRenderer media={nextVideoMedia} nextMedia={null} progress={0} />);
    const secondVideo = container.querySelector("video");

    expect(firstVideo).not.toBe(secondVideo);
    expect(secondVideo.src).toContain("proximo.mp4");
  });
});

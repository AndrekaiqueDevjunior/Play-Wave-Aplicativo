import React, { useEffect, useRef, useState } from "react";

const phrases = [
  "Carregando campanhas ativas...",
  "Pareando TVs em tempo real...",
  "Sincronizando mídia visual e áudio...",
  "Preparando experiência em tela cheia...",
];

const syncMessages = [
  "Sincronizando players...",
  "Campanhas atualizadas",
  "TVs conectadas em tempo real",
  "Monitoramento ativo",
];

export default function Apresentacao() {
  const stageRef = useRef(null);
  const spotlightRef = useRef(null);
  const panelRef = useRef(null);
  const [toast, setToast] = useState("");
  const [syncText, setSyncText] = useState(syncMessages[0]);
  const [typingText, setTypingText] = useState("");
  const [counts, setCounts] = useState({ tvs: 0, views: 0, sync: 0 });

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;

    const particles = [];
    for (let i = 0; i < 72; i += 1) {
      const particle = document.createElement("span");
      particle.className = "presentation-particle";
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.animationDuration = `${5 + Math.random() * 9}s`;
      particle.style.animationDelay = `${Math.random() * 7}s`;
      particle.style.opacity = `${0.25 + Math.random() * 0.72}`;
      particle.style.width = `${3 + Math.random() * 6}px`;
      particle.style.height = particle.style.width;
      particle.style.setProperty("--drift", `${-110 + Math.random() * 220}px`);
      stage.appendChild(particle);
      particles.push(particle);
    }

    return () => particles.forEach((particle) => particle.remove());
  }, []);

  useEffect(() => {
    let active = true;
    let phraseIndex = 0;

    const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

    async function typeLoop() {
      while (active) {
        const text = phrases[phraseIndex % phrases.length];
        for (let i = 0; i <= text.length && active; i += 1) {
          setTypingText(text.slice(0, i));
          await sleep(32);
        }
        await sleep(1200);
        for (let i = text.length; i >= 0 && active; i -= 1) {
          setTypingText(text.slice(0, i));
          await sleep(16);
        }
        phraseIndex += 1;
      }
    }

    typeLoop();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let index = 0;
    const interval = window.setInterval(() => {
      index = (index + 1) % syncMessages.length;
      setSyncText(syncMessages[index]);
    }, 2400);

    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    animateCounters();
  }, []);

  const showToast = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2200);
  };

  const animateCounters = () => {
    const start = performance.now();
    const duration = 1400;
    const targets = { tvs: 24, views: 128, sync: 99 };

    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCounts({
        tvs: Math.floor(targets.tvs * eased),
        views: Math.floor(targets.views * eased),
        sync: Math.floor(targets.sync * eased),
      });
      if (progress < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
  };

  const createSparkBurst = (x, y, total = 26) => {
    for (let i = 0; i < total; i += 1) {
      const spark = document.createElement("span");
      const angle = (Math.PI * 2 * i) / total;
      const distance = 42 + Math.random() * 92;
      spark.className = "presentation-spark";
      spark.style.left = `${x}px`;
      spark.style.top = `${y}px`;
      spark.style.setProperty("--tx", `${Math.cos(angle) * distance}px`);
      spark.style.setProperty("--ty", `${Math.sin(angle) * distance}px`);
      document.body.appendChild(spark);
      window.setTimeout(() => spark.remove(), 760);
    }
  };

  const handleMouseMove = (event) => {
    const x = (event.clientX / window.innerWidth) * 100;
    const y = (event.clientY / window.innerHeight) * 100;
    spotlightRef.current?.style.setProperty("--x", `${x}%`);
    spotlightRef.current?.style.setProperty("--y", `${y}%`);

    if (panelRef.current) {
      const rotateX = (event.clientY / window.innerHeight - 0.5) * -4;
      const rotateY = (event.clientX / window.innerWidth - 0.5) * 5;
      panelRef.current.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
    }
  };

  const handleMouseLeave = () => {
    if (panelRef.current) {
      panelRef.current.style.transform = "rotateX(0deg) rotateY(0deg)";
    }
  };

  const handleStart = (event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    createSparkBurst(rect.left + rect.width / 2, rect.top + rect.height / 2);
    animateCounters();
    showToast("Apresentação iniciada com sucesso");
  };

  const handleFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
        showToast("Modo tela cheia ativado");
      } else {
        await document.exitFullscreen();
        showToast("Modo tela cheia desativado");
      }
    } catch {
      showToast("Não foi possível ativar a tela cheia");
    }
  };

  return (
    <>
      <style>{presentationStyles}</style>
      <main
        className="presentation-stage"
        ref={stageRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <div className="presentation-cinema-flash" />
        <div className="presentation-grid" />
        <div className="presentation-aurora presentation-one" />
        <div className="presentation-aurora presentation-two" />
        <div className="presentation-aurora presentation-three" />
        <div className="presentation-energy-beam" />
        <div className="presentation-spotlight" ref={spotlightRef} />
        <div className="presentation-orbital" />

        <section className="presentation-panel" ref={panelRef}>
          <div className="presentation-panel-content">
            <div className="presentation-top-row">
              <div className="presentation-brand">
                <div className="presentation-logo-wrap" aria-hidden="true">
                  <div className="presentation-energy-ring" />
                  <div className="presentation-energy-ring presentation-ring-two" />
                  <div className="presentation-logo">
                    <img src="/apple-touch-icon.png" alt="" />
                  </div>
                </div>
                <div className="presentation-brand-text">
                  <span>Sistema de TV Corporativa</span>
                  <strong>Play Wave</strong>
                </div>
              </div>

              <div className="presentation-status-group">
                <div className="presentation-live-pill">
                  <span />
                  Transmissão ativa
                </div>
                <div className="presentation-status-pill">
                  <span className="presentation-status-dot" />
                  <strong>{syncText}</strong>
                </div>
              </div>
            </div>

            <div className="presentation-hero">
              <div>
                <div className="presentation-kicker">Controle centralizado</div>

                <h1 className="presentation-headline">
                  Sua rede de TVs
                  <span className="presentation-gradient">ganha vida.</span>
                </h1>

                <p className="presentation-subtitle">
                  Campanhas entram no ar, players recebem atualizações e cada tela passa
                  a trabalhar como uma vitrine viva para sua comunicação.
                </p>

                <div className="presentation-typing-line">{typingText}</div>

                <div className="presentation-actions">
                  <button className="presentation-btn" type="button" onClick={handleStart}>
                    Iniciar apresentação
                  </button>
                  <button
                    className="presentation-btn presentation-secondary"
                    type="button"
                    onClick={handleFullscreen}
                  >
                    Tela cheia
                  </button>
                </div>

                <div className="presentation-metrics">
                  <div className="presentation-metric">
                    <strong>{counts.tvs}+</strong>
                    <span>TVs online</span>
                  </div>
                  <div className="presentation-metric">
                    <strong>{counts.views}</strong>
                    <span>Exibições hoje</span>
                  </div>
                  <div className="presentation-metric">
                    <strong>{counts.sync}%</strong>
                    <span>Sincronização</span>
                  </div>
                </div>
              </div>

              <div className="presentation-right-zone">
                <div className="presentation-hologram">
                  <div className="presentation-screen-orbit" />
                </div>

                <div className="presentation-device-preview">
                  <div className="presentation-device-screen">
                    <div className="presentation-play-badge">Player ao vivo</div>
                    <div className="presentation-wave-bars" aria-hidden="true">
                      {[32, 74, 48, 88, 42, 68, 92, 36, 62, 84, 46, 70].map((height) => (
                        <span key={height} style={{ height: `${height}%` }} />
                      ))}
                    </div>
                  </div>
                </div>

                <div className="presentation-cards">
                  <FeatureCard number="01" title="Campanhas no ar" text="Programações visuais entrando em execução com impacto." />
                  <FeatureCard number="02" title="Mídias em movimento" text="Vídeos, imagens e links com sensação de transmissão real." />
                  <FeatureCard number="03" title="Players conectados" text="TVs pareadas, status ativo e atualização remota constante." />
                  <FeatureCard number="04" title="Operação monitorada" text="Exibições, alertas e relatórios preparados para escala." />
                </div>
              </div>
            </div>
          </div>

          <div className="presentation-loader" aria-hidden="true">
            <span />
          </div>
        </section>

        <div className={`presentation-toast ${toast ? "presentation-show" : ""}`}>
          {toast}
        </div>
      </main>
    </>
  );
}

function FeatureCard({ number, title, text }) {
  return (
    <article className="presentation-card">
      <small>{number}</small>
      <h3>{title}</h3>
      <p>{text}</p>
    </article>
  );
}

const presentationStyles = `
:root {
  --presentation-bg-1: #020711;
  --presentation-bg-2: #061b38;
  --presentation-bg-3: #0b3f76;
  --presentation-blue: #00a8ff;
  --presentation-cyan: #55ddff;
  --presentation-electric: #6dfcff;
  --presentation-green: #37ffb1;
  --presentation-text: #f5fbff;
  --presentation-muted: #b8d8ee;
  --presentation-glass-border: rgba(124, 219, 255, 0.3);
  --presentation-danger: #ff4d8d;
}

.presentation-stage,
.presentation-stage * {
  box-sizing: border-box;
}

.presentation-stage {
  position: relative;
  width: 100vw;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 40px;
  isolation: isolate;
  perspective: 1200px;
  overflow: hidden;
  font-family: Inter, Arial, Helvetica, sans-serif;
  color: var(--presentation-text);
  background:
    radial-gradient(circle at 16% 16%, rgba(0, 168, 255, 0.36), transparent 30%),
    radial-gradient(circle at 86% 78%, rgba(85, 221, 255, 0.24), transparent 34%),
    radial-gradient(circle at 52% 52%, rgba(0, 168, 255, 0.14), transparent 48%),
    linear-gradient(135deg, var(--presentation-bg-1), var(--presentation-bg-2) 56%, var(--presentation-bg-3));
}

.presentation-stage::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(rgba(255, 255, 255, 0.035) 50%, rgba(0, 0, 0, 0.12) 50%),
    linear-gradient(90deg, rgba(255, 0, 90, 0.035), rgba(0, 255, 255, 0.025), rgba(0, 80, 255, 0.035));
  background-size: 100% 4px, 6px 100%;
  mix-blend-mode: screen;
  opacity: 0.55;
  z-index: 50;
}

.presentation-cinema-flash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.95), transparent 52%);
  opacity: 0;
  z-index: 20;
  animation: presentationCinematicFlash 1.4s ease-out 0.25s both;
}

.presentation-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 1px, transparent 1px);
  background-size: 84px 84px;
  mask-image: radial-gradient(circle at center, black, transparent 82%);
  animation: presentationGridMove 12s linear infinite;
  z-index: -8;
}

.presentation-grid::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(115deg, transparent, rgba(85, 221, 255, 0.18), transparent);
  transform: translateX(-120%);
  animation: presentationGridSweep 5.2s ease-in-out infinite;
}

.presentation-aurora {
  position: absolute;
  width: 58vw;
  height: 58vw;
  border-radius: 999px;
  filter: blur(54px);
  opacity: 0.36;
  z-index: -7;
}

.presentation-one {
  top: -24%;
  left: -18%;
  background: var(--presentation-blue);
  animation: presentationFloatOne 6s ease-in-out infinite alternate;
}

.presentation-two {
  right: -18%;
  bottom: -24%;
  background: var(--presentation-cyan);
  animation: presentationFloatTwo 7s ease-in-out infinite alternate;
}

.presentation-three {
  width: 36vw;
  height: 36vw;
  left: 38%;
  top: 30%;
  background: #334dff;
  opacity: 0.18;
  animation: presentationFloatThree 8s ease-in-out infinite alternate;
}

.presentation-energy-beam {
  position: absolute;
  width: 180vw;
  height: 190px;
  left: -40vw;
  top: 50%;
  transform: translateY(-50%) rotate(-9deg);
  background: linear-gradient(90deg, transparent, rgba(85, 221, 255, 0.08), rgba(255, 255, 255, 0.18), rgba(0, 168, 255, 0.08), transparent);
  filter: blur(10px);
  opacity: 0.75;
  z-index: -6;
  animation: presentationBeamPulse 4.2s ease-in-out infinite;
}

.presentation-spotlight {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at var(--x, 50%) var(--y, 50%), rgba(255, 255, 255, 0.14), transparent 22%);
  z-index: -5;
}

.presentation-orbital {
  position: absolute;
  width: 680px;
  height: 680px;
  border-radius: 50%;
  border: 1px solid rgba(85, 221, 255, 0.13);
  z-index: -4;
  animation: presentationSpin 22s linear infinite;
}

.presentation-orbital::before,
.presentation-orbital::after {
  content: "";
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--presentation-cyan);
  box-shadow: 0 0 26px rgba(85, 221, 255, 0.9);
}

.presentation-orbital::before {
  top: 38px;
  left: 118px;
}

.presentation-orbital::after {
  right: 80px;
  bottom: 84px;
  background: var(--presentation-blue);
}

.presentation-panel {
  position: relative;
  width: min(1140px, 94vw);
  min-height: 635px;
  padding: 50px;
  border: 1px solid var(--presentation-glass-border);
  border-radius: 42px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.13), rgba(255, 255, 255, 0.04)),
    linear-gradient(180deg, rgba(0, 168, 255, 0.06), rgba(0, 0, 0, 0.08));
  box-shadow:
    0 35px 110px rgba(0, 0, 0, 0.52),
    0 0 80px rgba(0, 168, 255, 0.14),
    inset 0 0 44px rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  overflow: hidden;
  transform-style: preserve-3d;
  animation: presentationPanelIn 1.25s cubic-bezier(.15,.95,.22,1) both;
}

.presentation-panel::before {
  content: "";
  position: absolute;
  inset: -2px;
  background: linear-gradient(110deg, transparent 0%, rgba(255, 255, 255, 0.24) 34%, transparent 68%);
  transform: translateX(-100%);
  animation: presentationShine 4.2s ease-in-out infinite;
  pointer-events: none;
}

.presentation-panel::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background:
    radial-gradient(circle at 18% 20%, rgba(85, 221, 255, 0.15), transparent 24%),
    radial-gradient(circle at 78% 72%, rgba(0, 168, 255, 0.12), transparent 26%);
  opacity: 0.9;
}

.presentation-panel-content {
  position: relative;
  z-index: 2;
}

.presentation-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 46px;
}

.presentation-brand {
  display: flex;
  align-items: center;
  gap: 18px;
}

.presentation-logo-wrap {
  position: relative;
  width: 104px;
  height: 104px;
  display: grid;
  place-items: center;
}

.presentation-energy-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(85, 221, 255, 0.25);
  animation: presentationRingSpin 5s linear infinite;
}

.presentation-energy-ring::before {
  content: "";
  position: absolute;
  width: 11px;
  height: 11px;
  right: 9px;
  top: 20px;
  border-radius: 50%;
  background: var(--presentation-electric);
  box-shadow: 0 0 24px var(--presentation-electric);
}

.presentation-ring-two {
  inset: 8px;
  animation-duration: 3.6s;
  animation-direction: reverse;
  opacity: 0.75;
}

.presentation-logo {
  position: relative;
  width: 82px;
  height: 82px;
  border-radius: 26px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(0, 168, 255, 0.38), rgba(85, 221, 255, 0.14));
  border: 1px solid rgba(125, 225, 255, 0.58);
  box-shadow: 0 0 42px rgba(0, 168, 255, 0.32);
  animation: presentationLogoPulse 2.2s ease-in-out infinite;
}

.presentation-logo img {
  width: 58px;
  height: 58px;
  object-fit: contain;
  filter: drop-shadow(0 0 14px rgba(85, 221, 255, 1));
}

.presentation-brand-text span {
  display: block;
  color: var(--presentation-muted);
  font-size: 14px;
  letter-spacing: 0.3em;
  text-transform: uppercase;
}

.presentation-brand-text strong {
  display: block;
  margin-top: 4px;
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1;
  letter-spacing: -0.06em;
  text-shadow: 0 0 20px rgba(85, 221, 255, 0.18);
}

.presentation-status-group {
  display: grid;
  gap: 10px;
  justify-items: end;
}

.presentation-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 17px;
  border: 1px solid rgba(125, 225, 255, 0.34);
  border-radius: 999px;
  color: #dff7ff;
  background: rgba(0, 0, 0, 0.22);
  font-size: 14px;
  white-space: nowrap;
}

.presentation-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--presentation-green);
  box-shadow: 0 0 18px rgba(55, 255, 177, 0.9);
  animation: presentationBlink 1.1s ease-in-out infinite;
}

.presentation-live-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 77, 141, 0.32);
  color: #ffdce9;
  background: rgba(255, 77, 141, 0.1);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.presentation-live-pill span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--presentation-danger);
  box-shadow: 0 0 16px var(--presentation-danger);
  animation: presentationLivePulse 0.9s ease-in-out infinite;
}

.presentation-hero {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 42px;
  align-items: center;
}

.presentation-kicker {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 16px;
  padding: 9px 13px;
  border-radius: 999px;
  border: 1px solid rgba(125, 225, 255, 0.28);
  background: rgba(255, 255, 255, 0.065);
  color: #e8fbff;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.presentation-kicker::before {
  content: "";
  width: 34px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--presentation-blue), var(--presentation-cyan));
  box-shadow: 0 0 18px rgba(85, 221, 255, 0.9);
}

.presentation-headline {
  font-size: clamp(45px, 6vw, 82px);
  line-height: 0.92;
  letter-spacing: -0.085em;
  max-width: 650px;
}

.presentation-gradient {
  display: block;
  background: linear-gradient(90deg, #ffffff, var(--presentation-cyan), var(--presentation-blue), #ffffff);
  background-size: 260% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0 22px rgba(0, 168, 255, 0.22));
  animation: presentationGradientFlow 3.6s ease-in-out infinite;
}

.presentation-subtitle {
  margin-top: 24px;
  max-width: 590px;
  color: var(--presentation-muted);
  font-size: clamp(17px, 2vw, 22px);
  line-height: 1.55;
}

.presentation-typing-line {
  min-height: 30px;
  margin-top: 16px;
  color: #e9fbff;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: 0.03em;
}

.presentation-typing-line::after {
  content: "";
  display: inline-block;
  width: 9px;
  height: 20px;
  margin-left: 5px;
  transform: translateY(4px);
  background: var(--presentation-cyan);
  animation: presentationCursorBlink 0.75s infinite;
}

.presentation-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 32px;
}

.presentation-btn {
  position: relative;
  border: 0;
  cursor: pointer;
  padding: 16px 24px;
  border-radius: 999px;
  font-weight: 900;
  font-size: 15px;
  color: #fff;
  background: linear-gradient(135deg, var(--presentation-blue), #55ddff);
  box-shadow: 0 16px 44px rgba(0, 168, 255, 0.32);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  overflow: hidden;
}

.presentation-btn::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.36), transparent);
  transform: translateX(-110%);
  transition: transform 0.55s ease;
}

.presentation-btn:hover {
  transform: translateY(-4px) scale(1.03);
  box-shadow: 0 22px 62px rgba(0, 168, 255, 0.46);
}

.presentation-btn:hover::before {
  transform: translateX(110%);
}

.presentation-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: #dff7ff;
  border: 1px solid rgba(125, 225, 255, 0.32);
  box-shadow: none;
}

.presentation-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  max-width: 610px;
  margin-top: 28px;
}

.presentation-metric {
  padding: 14px;
  border-radius: 20px;
  border: 1px solid rgba(125, 225, 255, 0.2);
  background: rgba(255, 255, 255, 0.06);
}

.presentation-metric strong {
  display: block;
  font-size: 29px;
  line-height: 1;
  color: #fff;
  text-shadow: 0 0 16px rgba(85, 221, 255, 0.18);
}

.presentation-metric span {
  display: block;
  margin-top: 6px;
  color: var(--presentation-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.presentation-right-zone {
  position: relative;
  min-height: 430px;
  display: grid;
  align-items: center;
}

.presentation-hologram {
  position: absolute;
  inset: 12px 0 auto auto;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0.78;
}

.presentation-screen-orbit {
  position: absolute;
  top: -12px;
  right: 40px;
  width: 310px;
  height: 310px;
  border-radius: 50%;
  border: 1px dashed rgba(85, 221, 255, 0.26);
  animation: presentationSpinReverse 18s linear infinite;
}

.presentation-screen-orbit::before,
.presentation-screen-orbit::after {
  content: "";
  position: absolute;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--presentation-cyan);
  box-shadow: 0 0 20px var(--presentation-cyan);
}

.presentation-screen-orbit::before {
  left: 30px;
  top: 52px;
}

.presentation-screen-orbit::after {
  right: 45px;
  bottom: 25px;
  background: var(--presentation-green);
  box-shadow: 0 0 20px var(--presentation-green);
}

.presentation-device-preview {
  position: relative;
  width: min(430px, 100%);
  margin-left: auto;
  padding: 17px;
  border: 1px solid rgba(125, 225, 255, 0.28);
  border-radius: 30px;
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.04));
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.34), 0 0 60px rgba(0, 168, 255, 0.12);
  transform: rotateY(-10deg) rotateX(4deg);
  animation: presentationDeviceFloat 4.5s ease-in-out infinite;
}

.presentation-device-screen {
  position: relative;
  height: 238px;
  border-radius: 22px;
  overflow: hidden;
  background:
    radial-gradient(circle at 30% 20%, rgba(85, 221, 255, 0.4), transparent 26%),
    linear-gradient(135deg, #031027, #0b4f8a);
  border: 1px solid rgba(125, 225, 255, 0.28);
}

.presentation-device-screen::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    linear-gradient(110deg, transparent, rgba(255,255,255,0.22), transparent),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.055) 0 1px, transparent 1px 7px);
  transform: translateX(-100%);
  animation: presentationScreenSweep 3s ease-in-out infinite;
}

.presentation-play-badge {
  position: absolute;
  left: 26px;
  top: 24px;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 9px 12px;
  border-radius: 999px;
  background: rgba(0,0,0,0.28);
  border: 1px solid rgba(255,255,255,0.18);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.presentation-play-badge::before {
  content: "";
  width: 0;
  height: 0;
  border-top: 6px solid transparent;
  border-bottom: 6px solid transparent;
  border-left: 9px solid var(--presentation-cyan);
}

.presentation-wave-bars {
  position: absolute;
  left: 26px;
  right: 26px;
  bottom: 24px;
  height: 72px;
  display: flex;
  align-items: end;
  gap: 7px;
}

.presentation-wave-bars span {
  flex: 1;
  min-width: 6px;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--presentation-cyan), var(--presentation-blue));
  box-shadow: 0 0 16px rgba(85, 221, 255, 0.25);
  animation: presentationBarDance 1.15s ease-in-out infinite;
}

.presentation-wave-bars span:nth-child(2n) { animation-delay: 0.14s; }
.presentation-wave-bars span:nth-child(3n) { animation-delay: 0.26s; }
.presentation-wave-bars span:nth-child(4n) { animation-delay: 0.38s; }

.presentation-cards {
  position: relative;
  display: grid;
  gap: 14px;
  z-index: 2;
  margin-top: 275px;
}

.presentation-card {
  position: relative;
  min-height: 86px;
  padding: 18px 20px;
  border: 1px solid rgba(125, 225, 255, 0.25);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.075);
  overflow: hidden;
  transform: translateX(42px) scale(0.96);
  opacity: 0;
  animation: presentationCardIn 0.8s cubic-bezier(.2,.9,.2,1) forwards;
}

.presentation-card:nth-child(1) { animation-delay: 0.75s; }
.presentation-card:nth-child(2) { animation-delay: 0.95s; }
.presentation-card:nth-child(3) { animation-delay: 1.15s; }
.presentation-card:nth-child(4) { animation-delay: 1.35s; }

.presentation-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 15% 20%, rgba(85, 221, 255, 0.2), transparent 38%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.presentation-card:hover {
  border-color: rgba(85, 221, 255, 0.52);
}

.presentation-card:hover::before {
  opacity: 1;
}

.presentation-card small {
  position: absolute;
  left: 18px;
  top: 20px;
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 14px;
  color: #fff;
  background: rgba(0, 168, 255, 0.86);
  box-shadow: 0 0 22px rgba(0, 168, 255, 0.35);
}

.presentation-card h3,
.presentation-card p {
  position: relative;
  padding-left: 55px;
}

.presentation-card h3 {
  font-size: 20px;
  margin-bottom: 5px;
}

.presentation-card p {
  color: var(--presentation-muted);
  line-height: 1.42;
  font-size: 14px;
}

.presentation-loader {
  position: absolute;
  left: 50px;
  right: 50px;
  bottom: 36px;
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.09);
  overflow: hidden;
  z-index: 3;
}

.presentation-loader span {
  display: block;
  width: 38%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, transparent, var(--presentation-cyan), var(--presentation-blue), var(--presentation-cyan));
  box-shadow: 0 0 18px rgba(85, 221, 255, 0.6);
  animation: presentationLoading 1.6s ease-in-out infinite;
}

.presentation-particle {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(125, 225, 255, 0.72);
  box-shadow: 0 0 18px rgba(85, 221, 255, 0.9);
  pointer-events: none;
  z-index: -1;
  animation: presentationParticleFloat linear infinite;
}

.presentation-spark {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  pointer-events: none;
  background: var(--presentation-cyan);
  box-shadow: 0 0 20px var(--presentation-cyan);
  animation: presentationSparkBurst 700ms ease-out forwards;
  z-index: 80;
}

.presentation-toast {
  position: fixed;
  left: 50%;
  bottom: 28px;
  transform: translateX(-50%) translateY(18px);
  padding: 14px 18px;
  border-radius: 16px;
  border: 1px solid rgba(125, 225, 255, 0.32);
  color: #eafaff;
  background: rgba(5, 18, 38, 0.82);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.38);
  opacity: 0;
  pointer-events: none;
  transition: 0.35s ease;
  backdrop-filter: blur(12px);
  z-index: 90;
}

.presentation-show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

@keyframes presentationCinematicFlash {
  0% { opacity: 0; transform: scale(0.8); }
  18% { opacity: 0.72; transform: scale(1); }
  100% { opacity: 0; transform: scale(1.28); }
}

@keyframes presentationGridMove {
  from { transform: translateY(0); }
  to { transform: translateY(84px); }
}

@keyframes presentationGridSweep {
  0%, 42% { transform: translateX(-120%); }
  72%, 100% { transform: translateX(120%); }
}

@keyframes presentationFloatOne {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(135px, 88px) scale(1.08); }
}

@keyframes presentationFloatTwo {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(-125px, -76px) scale(1.1); }
}

@keyframes presentationFloatThree {
  from { transform: translate(-40px, 20px) scale(1); }
  to { transform: translate(50px, -30px) scale(1.22); }
}

@keyframes presentationBeamPulse {
  0%, 100% { opacity: 0.32; transform: translateY(-50%) rotate(-9deg) scaleX(0.95); }
  50% { opacity: 0.9; transform: translateY(-50%) rotate(-9deg) scaleX(1.05); }
}

@keyframes presentationSpin {
  to { transform: rotate(360deg); }
}

@keyframes presentationSpinReverse {
  to { transform: rotate(-360deg); }
}

@keyframes presentationPanelIn {
  from { opacity: 0; transform: translateY(36px) rotateX(10deg) scale(0.94); filter: blur(9px); }
  to { opacity: 1; transform: translateY(0) rotateX(0) scale(1); filter: blur(0); }
}

@keyframes presentationShine {
  0%, 45% { transform: translateX(-120%); }
  70%, 100% { transform: translateX(120%); }
}

@keyframes presentationRingSpin {
  to { transform: rotate(360deg); }
}

@keyframes presentationLogoPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 34px rgba(0, 168, 255, 0.28); }
  50% { transform: scale(1.075); box-shadow: 0 0 60px rgba(0, 168, 255, 0.44); }
}

@keyframes presentationBlink {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.45; transform: scale(0.72); }
}

@keyframes presentationLivePulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.55); opacity: 0.55; }
}

@keyframes presentationGradientFlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

@keyframes presentationCursorBlink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}

@keyframes presentationCardIn {
  to { opacity: 1; transform: translateX(0) scale(1); }
}

@keyframes presentationDeviceFloat {
  0%, 100% { transform: rotateY(-10deg) rotateX(4deg) translateY(0); }
  50% { transform: rotateY(-6deg) rotateX(2deg) translateY(-16px); }
}

@keyframes presentationScreenSweep {
  0%, 42% { transform: translateX(-110%); }
  70%, 100% { transform: translateX(110%); }
}

@keyframes presentationBarDance {
  0%, 100% { height: 24%; }
  35% { height: 92%; }
  65% { height: 46%; }
}

@keyframes presentationLoading {
  0% { transform: translateX(-105%); }
  100% { transform: translateX(282%); }
}

@keyframes presentationParticleFloat {
  from { transform: translate3d(0, 110vh, 0) scale(0.7); opacity: 0; }
  12% { opacity: 1; }
  88% { opacity: 1; }
  to { transform: translate3d(var(--drift), -12vh, 0) scale(1.35); opacity: 0; }
}

@keyframes presentationSparkBurst {
  from { transform: translate(0, 0) scale(1); opacity: 1; }
  to { transform: translate(var(--tx), var(--ty)) scale(0); opacity: 0; }
}

@media (max-width: 980px) {
  .presentation-stage {
    min-height: 100vh;
    height: auto;
    padding: 24px;
    overflow: auto;
  }

  .presentation-orbital,
  .presentation-screen-orbit {
    display: none;
  }

  .presentation-panel {
    padding: 28px;
    min-height: auto;
  }

  .presentation-top-row,
  .presentation-hero {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: flex-start;
  }

  .presentation-status-group {
    justify-items: start;
  }

  .presentation-status-pill {
    white-space: normal;
  }

  .presentation-right-zone {
    width: 100%;
    min-height: auto;
  }

  .presentation-hologram {
    display: none;
  }

  .presentation-device-preview {
    margin: 20px 0 0;
    width: 100%;
    transform: none;
  }

  .presentation-cards {
    margin-top: 18px;
  }

  .presentation-metrics {
    grid-template-columns: 1fr;
  }

  .presentation-loader {
    position: relative;
    left: auto;
    right: auto;
    bottom: auto;
    margin-top: 32px;
  }
}
`;

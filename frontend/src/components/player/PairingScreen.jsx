import React, { useEffect, useState } from "react";
import { Wifi, WifiOff } from "lucide-react";

const STATUS_CONFIG = {
  connected: {
    icon: Wifi,
    color: "text-emerald-400",
    label: "Backend conectado",
  },
  no_api: { icon: WifiOff, color: "text-amber-400", label: "API não configurada" },
  error: {
    icon: WifiOff,
    color: "text-red-400",
    label: "Sem conexão ao backend",
  },
  connecting: { icon: null, color: "text-blue-400", label: "Conectando..." },
};

export default function PairingScreen({ pairingCode, apiStatus }) {
  const [dots, setDots] = useState(0);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const d = setInterval(() => setDots((p) => (p + 1) % 4), 600);
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => {
      clearInterval(d);
      clearInterval(t);
    };
  }, []);

  const statusConf = STATUS_CONFIG[apiStatus] || STATUS_CONFIG.connecting;
  const StatusIcon = statusConf.icon;

  return (
    <div className="fixed inset-0 bg-[#07090f] flex text-white overflow-hidden">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />
      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-indigo-600/8 rounded-full blur-[100px] pointer-events-none" />

      {/* Clock — top right */}
      <div className="absolute top-6 right-8 text-right">
        <p className="text-3xl font-light font-mono tracking-widest tabular-nums">
          {time.toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
        <p className="text-xs text-white/30 mt-0.5 tracking-wider uppercase">
          {time.toLocaleDateString("pt-BR", {
            weekday: "long",
            day: "2-digit",
            month: "long",
          })}
        </p>
      </div>

      {/* Logo — top left */}
      <div className="absolute top-6 left-8 flex items-center gap-3">
        <div className="w-9 h-9 flex items-center justify-center">
          <img
            src="/apple-touch-icon.png"
            alt=""
            className="h-full w-full object-contain drop-shadow-[0_0_14px_rgba(14,165,233,0.55)]"
          />
        </div>
        <span className="text-sm font-semibold tracking-wide text-white/70">
          PlayWave
        </span>
      </div>

      {/* Center content */}
      <div className="flex-1 flex flex-col items-center justify-center px-8">
        <div className="flex flex-col items-center gap-8 max-w-md w-full">
          {/* Pairing code card */}
          <div className="w-full bg-white/[0.04] border border-white/[0.08] rounded-3xl p-10 backdrop-blur-sm text-center shadow-2xl">
            <p className="text-xs font-semibold tracking-[0.2em] uppercase text-white/40 mb-6">
              Código de Pareamento
            </p>
            <p className="text-6xl font-bold tracking-[0.4em] font-mono text-white leading-none">
              {pairingCode}
            </p>
            <div className="mt-8 pt-6 border-t border-white/[0.06]">
              <p className="text-sm text-white/30 leading-relaxed">
                Acesse o painel em{" "}
                <span className="text-white/60 font-medium">
                  Dispositivos → Adicionar
                </span>
                <br />e digite este código para vincular esta tela
              </p>
            </div>
          </div>

          {/* Steps */}
          <div className="flex items-center gap-6 text-xs text-white/25">
            {["Abra o painel", "Vá em Dispositivos", "Informe o código"].map(
              (step, i) => (
                <React.Fragment key={i}>
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-7 h-7 rounded-full border border-white/10 flex items-center justify-center text-white/40 font-bold text-xs">
                      {i + 1}
                    </div>
                    <span>{step}</span>
                  </div>
                  {i < 2 && (
                    <div className="h-px w-8 bg-white/10 flex-shrink-0" />
                  )}
                </React.Fragment>
              ),
            )}
          </div>

          {/* Status */}
          <div className="flex items-center gap-2">
            {StatusIcon ? (
              <StatusIcon className={`w-3.5 h-3.5 ${statusConf.color}`} />
            ) : (
              <span className="flex gap-0.5">
                {Array.from({ length: 3 }).map((_, i) => (
                  <span
                    key={i}
                    className={`w-1.5 h-1.5 rounded-full bg-blue-400 ${dots > i ? "opacity-100" : "opacity-20"} transition-opacity`}
                  />
                ))}
              </span>
            )}
            <span className={`text-xs ${statusConf.color}`}>
              {statusConf.label}
            </span>
            <span className="text-white/15 mx-1">·</span>
            <span className="text-xs text-white/25">
              Aguardando{"."[".".repeat(dots).length - 1] ?? ""}
              {".".repeat(dots)}
            </span>
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="absolute bottom-0 left-0 right-0 border-t border-white/[0.05] px-8 py-4 flex items-center justify-between">
        <span className="text-xs text-white/20">PlayWave Player v3.0</span>
        <span className="text-xs text-white/20">Digital Signage Platform</span>
      </div>
    </div>
  );
}

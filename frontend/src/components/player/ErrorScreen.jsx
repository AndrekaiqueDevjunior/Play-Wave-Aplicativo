import React from "react";
import { WifiOff, RefreshCw } from "lucide-react";

export default function ErrorScreen({
  message = "Erro ao carregar conteúdo",
  onRetry,
}) {
  return (
    <div className="fixed inset-0 bg-[#07090f] flex flex-col items-center justify-center text-white gap-6">
      <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
        <WifiOff className="w-8 h-8 text-red-400" />
      </div>
      <div className="text-center">
        <p className="text-white/70 font-medium">{message}</p>
        <p className="text-white/30 text-sm mt-1">
          Verifique a conexão e tente novamente
        </p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-sm text-white/60 hover:text-white/80 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Tentar novamente
        </button>
      )}
    </div>
  );
}

import React from "react";

export default function LoadingScreen({ message = "Carregando conteúdo..." }) {
  return (
    <div className="fixed inset-0 bg-[#07090f] flex flex-col items-center justify-center text-white">
      <div className="relative w-16 h-16 mb-6">
        <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
        <div className="absolute inset-0 rounded-full border-2 border-t-blue-500 animate-spin" />
        <div className="absolute inset-2 rounded-full border border-blue-400/10" />
      </div>
      <p className="text-sm text-white/40 tracking-wide">{message}</p>
    </div>
  );
}

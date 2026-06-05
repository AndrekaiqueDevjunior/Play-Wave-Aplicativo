import React from "react";
import { useAuth } from "@/lib/AuthContext";

// Sessão expirada — o redirect para /login já ocorre diretamente no AuthContext.
// Este componente exibe um aviso não-bloqueante na tela de login.
export default function SessionExpiredModal() {
  const { sessionExpired, dismissSessionExpired } = useAuth();

  if (!sessionExpired) return null;

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-amber-50 border border-amber-300 text-amber-800 rounded-xl px-4 py-3 shadow-lg flex items-center gap-3 text-sm animate-in fade-in slide-in-from-top-2 max-w-sm w-full mx-4">
      <span>⏱</span>
      <span className="flex-1">Sessão expirada. Faça login novamente.</span>
      <button onClick={dismissSessionExpired} className="text-amber-600 hover:text-amber-900 font-bold text-lg leading-none">×</button>
    </div>
  );
}

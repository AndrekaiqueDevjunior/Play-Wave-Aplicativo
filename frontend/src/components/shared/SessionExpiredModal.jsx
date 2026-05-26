import React from "react";
import { LogIn, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/AuthContext";

export default function SessionExpiredModal() {
  const { sessionExpired, dismissSessionExpired } = useAuth();

  if (!sessionExpired) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full mx-4 text-center animate-in fade-in zoom-in-95 duration-200">
        <div className="flex justify-center mb-4">
          <div className="bg-amber-100 rounded-full p-4">
            <Clock className="h-8 w-8 text-amber-600" />
          </div>
        </div>

        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Sessão expirada
        </h2>
        <p className="text-gray-500 text-sm mb-6">
          Sua sessão foi encerrada por inatividade ou expiração do token. Faça login novamente para continuar.
        </p>

        <Button onClick={dismissSessionExpired} className="w-full gap-2">
          <LogIn className="h-4 w-4" />
          Fazer login
        </Button>
      </div>
    </div>
  );
}

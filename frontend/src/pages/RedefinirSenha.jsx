import React, { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, KeyRound } from "lucide-react";
import { confirmarResetSenha } from "@/api/usuarios";
import { useAuth } from "@/lib/AuthContext";

export default function RedefinirSenha() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";
  const { setSession } = useAuth();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password.length < 6) {
      setError("A senha deve ter pelo menos 6 caracteres.");
      return;
    }
    if (password !== confirmPassword) {
      setError("As senhas não coincidem.");
      return;
    }
    if (!token) {
      setError("Link de redefinição inválido.");
      return;
    }

    setSubmitting(true);
    try {
      const result = await confirmarResetSenha(token, password);
      if (setSession) {
        setSession(result);
      }
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err?.message || "Não foi possível redefinir a senha. O link pode ter expirado.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-[#f8fafc] px-6 py-12">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-lg px-8 py-10">
        <div className="mb-6 flex flex-col items-center text-center">
          <img src="/apple-touch-icon.png" alt="" className="h-12 w-12 object-contain" />
          <h1 className="mt-3 text-2xl font-bold text-[#020817]">Redefinir senha</h1>
          <p className="mt-2 text-sm text-slate-500">Escolha uma nova senha de acesso.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="password">Nova senha</Label>
            <Input
              id="password"
              type="password"
              autoComplete="new-password"
              placeholder="Mínimo de 6 caracteres"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
            />
          </div>
          <div>
            <Label htmlFor="confirmPassword">Confirme a senha</Label>
            <Input
              id="confirmPassword"
              type="password"
              autoComplete="new-password"
              placeholder="Repita a senha"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={submitting}
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Salvando...
              </>
            ) : (
              <>
                <KeyRound className="w-4 h-4 mr-2" />
                Redefinir senha
              </>
            )}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          <Link to="/login" className="text-blue-600 font-medium">Voltar para o login</Link>
        </p>
      </div>
    </main>
  );
}

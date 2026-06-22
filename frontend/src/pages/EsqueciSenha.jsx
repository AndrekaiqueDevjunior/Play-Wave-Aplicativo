import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Mail } from "lucide-react";
import { solicitarResetSenha } from "@/api/usuarios";

export default function EsqueciSenha() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await solicitarResetSenha(email.trim().toLowerCase());
      setSent(true);
    } catch (err) {
      setError(err?.message || "Não foi possível processar a solicitação.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen w-full flex items-center justify-center bg-[#f8fafc] px-6 py-12">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-lg px-8 py-10">
        <div className="mb-6 flex flex-col items-center text-center">
          <img src="/apple-touch-icon.png" alt="" className="h-12 w-12 object-contain" />
          <h1 className="mt-3 text-2xl font-bold text-[#020817]">Recuperar senha</h1>
          <p className="mt-2 text-sm text-slate-500">
            Informe seu e-mail e enviaremos um link para redefinir sua senha.
          </p>
        </div>

        {sent ? (
          <p className="text-sm text-center text-slate-600">
            Se o e-mail existir em nossa base, você receberá as instruções em breve.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitting}
              />
            </div>

            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full" disabled={submitting || !email}>
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4 mr-2" />
                  Enviar link de recuperação
                </>
              )}
            </Button>
          </form>
        )}

        <p className="mt-6 text-center text-sm text-slate-500">
          <Link to="/login" className="text-blue-600 font-medium">Voltar para o login</Link>
        </p>
      </div>
    </main>
  );
}

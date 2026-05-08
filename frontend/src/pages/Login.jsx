import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Eye, EyeOff, Loader2, Monitor, Wifi, BarChart3, Radio, ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useAuth } from "@/lib/AuthContext";

// ─── Validação ───────────────────────────────────────────────────────────────

const schema = z.object({
  email: z
    .string()
    .min(1, "E-mail é obrigatório")
    .email("Formato de e-mail inválido"),
  password: z
    .string()
    .min(1, "Senha é obrigatória")
    .min(6, "Senha deve ter pelo menos 6 caracteres"),
  remember: z.boolean().default(false),
});

// ─── Rate limiting ───────────────────────────────────────────────────────────

const MAX_ATTEMPTS    = 5;
const LOCKOUT_SECONDS = 30;

// ─── Componente ──────────────────────────────────────────────────────────────

export default function Login() {
  const navigate                  = useNavigate();
  const { login, isAuthenticated, isLoadingAuth } = useAuth();

  const [showPassword, setShowPassword] = useState(false);
  const [serverError,  setServerError]  = useState("");
  const [attempts,     setAttempts]     = useState(0);
  const [lockoutUntil, setLockoutUntil] = useState(null);
  const [countdown,    setCountdown]    = useState(0);
  const timerRef = useRef(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", remember: false },
  });

  const remember = watch("remember");
  const isLocked = lockoutUntil != null && Date.now() < lockoutUntil;

  // Redireciona se já autenticado
  useEffect(() => {
    if (!isLoadingAuth && isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, isLoadingAuth, navigate]);

  // Countdown do lockout
  useEffect(() => {
    if (!lockoutUntil) return;

    const tick = () => {
      const remaining = Math.ceil((lockoutUntil - Date.now()) / 1000);
      if (remaining <= 0) {
        clearInterval(timerRef.current);
        setLockoutUntil(null);
        setAttempts(0);
        setCountdown(0);
      } else {
        setCountdown(remaining);
      }
    };

    tick();
    timerRef.current = setInterval(tick, 1000);
    return () => clearInterval(timerRef.current);
  }, [lockoutUntil]);

  // Submissão do formulário
  const onSubmit = useCallback(
    async ({ email, password, remember }) => {
      if (isLocked) return;
      setServerError("");

      try {
        await login(email.trim().toLowerCase(), password, remember);
        navigate("/dashboard", { replace: true });
      } catch (err) {
        const next = attempts + 1;
        setAttempts(next);

        if (next >= MAX_ATTEMPTS) {
          setLockoutUntil(Date.now() + LOCKOUT_SECONDS * 1000);
          setServerError(
            `Número máximo de tentativas atingido. Aguarde ${LOCKOUT_SECONDS} segundos.`
          );
        } else {
          setServerError(err.message ?? "Erro ao fazer login.");
        }
      }
    },
    [login, navigate, attempts, isLocked]
  );

  // Tela de carregamento da sessão inicial
  if (isLoadingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[hsl(var(--background))]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Painel esquerdo: Brand ─────────────────────────────────────────── */}
      <div className="hidden lg:flex lg:w-[45%] bg-[hsl(var(--sidebar-background))] flex-col justify-between p-12 relative overflow-hidden">
        {/* Círculo decorativo */}
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-primary/10 pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-64 h-64 rounded-full bg-primary/5 pointer-events-none" />

        <div className="relative">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-14">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg">
              <Monitor className="w-5 h-5 text-white" />
            </div>
            <span className="text-white text-xl font-bold tracking-tight">Play Wave</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Digital Signage<br />& Rádio Indoor
          </h1>
          <p className="text-[hsl(var(--sidebar-foreground))] text-base leading-relaxed max-w-sm">
            Gerencie campanhas, dispositivos e conteúdo audiovisual em um único painel centralizado.
          </p>
        </div>

        {/* Grid de features */}
        <div className="relative grid grid-cols-2 gap-3">
          {[
            { icon: Monitor,    label: "Dispositivos", desc: "TVs e painéis" },
            { icon: BarChart3,  label: "Relatórios",   desc: "Em tempo real" },
            { icon: Wifi,       label: "Monitoramento",desc: "Status ao vivo" },
            { icon: Radio,      label: "Rádio Indoor", desc: "Áudio ambiente" },
          ].map(({ icon: Icon, label, desc }) => (
            <div
              key={label}
              className="bg-[hsl(var(--sidebar-accent))] rounded-xl p-4 border border-white/5"
            >
              <Icon className="w-5 h-5 text-primary mb-2" />
              <p className="text-white text-sm font-semibold">{label}</p>
              <p className="text-[hsl(var(--sidebar-foreground))] text-xs mt-0.5">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ── Painel direito: Formulário ─────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-6 bg-[hsl(var(--background))]">
        <div className="w-full max-w-[360px]">

          {/* Logo mobile */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Monitor className="w-4 h-4 text-white" />
            </div>
            <span className="text-foreground text-lg font-bold">Play Wave</span>
          </div>

          {/* Cabeçalho */}
          <h2 className="text-2xl font-bold text-foreground mb-1">
            Bem-vindo de volta
          </h2>
          <p className="text-muted-foreground text-sm mb-8">
            Acesse sua conta para gerenciar o sistema
          </p>

          {/* ── Formulário ─────────────────────────────────────────────────── */}
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">

            {/* E-mail */}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">
                E-mail
              </Label>
              <Input
                id="email"
                type="email"
                inputMode="email"
                placeholder="seu@email.com"
                autoComplete="email"
                autoFocus
                disabled={isSubmitting || isLocked}
                aria-invalid={!!errors.email}
                aria-describedby={errors.email ? "email-error" : undefined}
                className={errors.email ? "border-destructive focus-visible:ring-destructive" : ""}
                {...register("email")}
              />
              {errors.email && (
                <p id="email-error" role="alert" className="text-xs text-destructive">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Senha */}
            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-sm font-medium">
                Senha
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  disabled={isSubmitting || isLocked}
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? "password-error" : undefined}
                  className={`pr-10 ${errors.password ? "border-destructive focus-visible:ring-destructive" : ""}`}
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  disabled={isSubmitting || isLocked}
                  tabIndex={-1}
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
                >
                  {showPassword
                    ? <EyeOff className="w-4 h-4" />
                    : <Eye     className="w-4 h-4" />
                  }
                </button>
              </div>
              {errors.password && (
                <p id="password-error" role="alert" className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Lembrar acesso */}
            <div className="flex items-center gap-2.5">
              <Checkbox
                id="remember"
                checked={remember}
                onCheckedChange={(checked) => setValue("remember", !!checked)}
                disabled={isSubmitting || isLocked}
              />
              <label
                htmlFor="remember"
                className="text-sm text-muted-foreground cursor-pointer select-none"
              >
                Lembrar acesso neste dispositivo
              </label>
            </div>

            {/* Erro do servidor */}
            {serverError && (
              <div
                role="alert"
                className="rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 flex gap-3"
              >
                <ShieldCheck className="w-4 h-4 text-destructive shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-destructive leading-snug">{serverError}</p>
                  {!isLocked && attempts > 0 && attempts < MAX_ATTEMPTS && (
                    <p className="text-xs text-destructive/70 mt-1">
                      {MAX_ATTEMPTS - attempts} tentativa{MAX_ATTEMPTS - attempts !== 1 ? "s" : ""} restante{MAX_ATTEMPTS - attempts !== 1 ? "s" : ""}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Lockout ativo */}
            {isLocked && (
              <div
                role="status"
                aria-live="polite"
                className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3"
              >
                <p className="text-sm font-semibold text-amber-800">
                  Acesso temporariamente bloqueado
                </p>
                <p className="text-xs text-amber-700 mt-1">
                  Muitas tentativas incorretas. Aguarde{" "}
                  <span className="font-bold tabular-nums">{countdown}s</span> para tentar novamente.
                </p>
              </div>
            )}

            {/* Botão de envio */}
            <Button
              type="submit"
              size="lg"
              className="w-full font-semibold"
              disabled={isSubmitting || isLocked}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Verificando...
                </>
              ) : isLocked ? (
                `Aguarde ${countdown}s`
              ) : (
                "Entrar"
              )}
            </Button>
          </form>

          {/* Rodapé */}
          <p className="text-center text-xs text-muted-foreground mt-10 leading-relaxed">
            Play Wave Digital Signage &copy; {new Date().getFullYear()}
            <br />
            <span className="text-muted-foreground/60">
              Acesso monitorado e protegido
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

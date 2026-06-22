import React, { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Eye,
  EyeOff,
  Loader2,
  Monitor,
  Wifi,
  BarChart3,
  Radio,
  ShieldCheck,
  Calendar,
  Shield,
  Cloud,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useAuth } from "@/lib/AuthContext";

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

const MAX_ATTEMPTS = 5;
const LOCKOUT_SECONDS = 30;

export default function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated, isLoadingAuth } = useAuth();

  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState("");
  const [attempts, setAttempts] = useState(0);
  const [lockoutUntil, setLockoutUntil] = useState(null);
  const [countdown, setCountdown] = useState(0);
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

  useEffect(() => {
    if (!isLoadingAuth && isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, isLoadingAuth, navigate]);

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

  if (isLoadingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f8fafc]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <main className="relative isolate min-h-screen w-full grid grid-cols-1 lg:grid-cols-2 bg-[#f8fafc] overflow-hidden">
      <ParticlesAndSparks />
      <section className="relative z-10 hidden min-h-screen overflow-hidden bg-[#020817] px-8 py-8 text-white md:px-14 md:py-10 lg:block">
        <div className="absolute inset-0 opacity-40 bg-[linear-gradient(rgba(59,130,246,0.16)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.16)_1px,transparent_1px)] bg-[size:48px_48px]" />
        <div className="absolute top-0 right-[-140px] w-[520px] h-full bg-blue-600/35 blur-[120px]" />
        <div className="absolute bottom-[-180px] left-[-120px] w-[420px] h-[420px] bg-blue-700/20 rounded-full blur-[120px]" />
        <div className="absolute top-[-90px] right-[-180px] w-[720px] h-[720px] border border-blue-500/20 rounded-full" />
        <div className="absolute top-[20px] right-[-120px] w-[560px] h-[560px] border border-blue-500/20 rounded-full" />
        <div className="absolute top-[130px] right-[-70px] w-[420px] h-[420px] border border-blue-400/20 rounded-full" />

        <div className="relative z-10 mx-auto flex min-h-[calc(100vh-80px)] max-w-[900px] flex-col justify-center">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center">
              <img
                src="/apple-touch-icon.png"
                alt=""
                className="h-full w-full object-contain drop-shadow-[0_0_18px_rgba(14,165,233,0.55)]"
              />
            </div>
            <span className="text-xl font-bold tracking-tight">Play Wave</span>
          </div>

          <div className="mt-10 inline-flex w-fit items-center gap-2 rounded-full border border-blue-500/40 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
            <Monitor className="w-4 h-4" />
            Plataforma de Mídia Inteligente
          </div>

          <div className="mt-5">
            <h1 className="text-[46px] md:text-[58px] xl:text-[66px] leading-[0.95] font-extrabold tracking-tight">
              Digital Signage
              <br />
              & Rádio Indoor
            </h1>
            <p className="mt-6 max-w-[560px] text-[17px] leading-7 text-slate-200">
              Gerencie campanhas, dispositivos e conteúdo audiovisual em um único
              painel centralizado.
            </p>
          </div>

          <div className="mt-7 grid max-w-[780px] grid-cols-2 gap-4 xl:grid-cols-4">
            <FeatureSmall icon={Monitor} title="Dispositivos" subtitle="TVs e painéis" />
            <FeatureSmall icon={BarChart3} title="Relatórios" subtitle="Em tempo real" />
            <FeatureSmall icon={Wifi} title="Monitoramento" subtitle="Status ao vivo" />
            <FeatureSmall icon={Radio} title="Rádio Indoor" subtitle="Áudio ambiente" />
          </div>

          <div className="mt-5 max-w-[880px] rounded-[22px] border border-blue-300/20 bg-[#061225]/80 p-4 shadow-[0_25px_80px_rgba(0,0,0,0.35)] backdrop-blur-xl md:p-5">
            <div className="mb-4 flex items-center justify-between gap-4">
              <h2 className="text-lg font-bold">Visão geral da rede</h2>
              <div className="flex items-center gap-2 text-sm text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                Todos os sistemas operando
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <MetricCard
                title="Dispositivos online"
                value="32"
                suffix="de 45"
                status="70% online"
                type="line"
              />
              <MetricCard
                title="Campanhas ativas"
                value="14"
                suffix="Transmissões"
                type="line"
              />
              <MetricCard
                title="Rádio Indoor"
                value="8"
                suffix="Zonas ativas"
                type="bar"
              />
            </div>

            <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-[1.4fr_1fr]">
              <div className="rounded-2xl border border-blue-300/15 bg-[#071a33]/80 p-4">
                <h3 className="mb-4 text-sm font-semibold">Atividades recentes</h3>
                <div className="space-y-3 text-sm">
                  <ActivityItem icon="✓" text="Campanha Verão 2026 foi publicada" time="Há 5 min" color="blue" />
                  <ActivityItem icon="♪" text="Playlist Rádio Indoor atualizada" time="Há 15 min" color="blue" />
                  <ActivityItem icon="↗" text="Novo dispositivo conectado: Loja Centro" time="Há 1 h" color="blue" />
                  <ActivityItem icon="!" text="Alerta: Dispositivo offline detectado" time="Há 2 h" color="yellow" />
                  <ActivityItem icon="□" text="Relatório semanal gerado" time="Há 3 h" color="slate" />
                </div>
              </div>

              <div className="rounded-2xl border border-blue-300/15 bg-[#071a33]/80 p-4">
                <h3 className="mb-4 text-sm font-semibold">Status da rede</h3>
                <div className="grid grid-cols-[1fr_120px] items-center gap-4">
                  <div className="space-y-4 text-sm">
                    <StatusLine color="bg-emerald-400" label="Online" value="32" />
                    <StatusLine color="bg-yellow-400" label="Inativos" value="5" />
                    <StatusLine color="bg-red-400" label="Offline" value="8" />
                  </div>
                  <div className="relative flex h-[112px] w-[112px] items-center justify-center rounded-full bg-[conic-gradient(#10b981_0_50%,#2563eb_50%_78%,#facc15_78%_88%,#ef4444_88%_100%)]">
                    <div className="flex h-[74px] w-[74px] items-center justify-center rounded-full bg-[#071a33]">
                      <span className="text-2xl font-bold">70%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 grid max-w-[880px] grid-cols-2 gap-3 xl:grid-cols-4">
            <FeatureCard icon={Monitor} title="Controle centralizado" text="Gerencie tudo em um só lugar" />
            <FeatureCard icon={Calendar} title="Agendamento inteligente" text="Programe conteúdos com facilidade" />
            <FeatureCard icon={Shield} title="Segurança avançada" text="Seus dados protegidos 24/7" />
            <FeatureCard icon={Cloud} title="100% na nuvem" text="Acesse de qualquer lugar do mundo" />
          </div>
        </div>
      </section>

      {/* LADO DIREITO - LOGIN EXEMPLO 06 */}
      <section className="relative z-10 min-h-screen bg-[#f8fafc] flex items-center justify-center px-6 py-12 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(37,99,235,0.06),transparent_55%)]" />
        <div className="absolute top-8 right-10 w-[260px] h-[260px] opacity-70 bg-[radial-gradient(circle,#2563eb_1.5px,transparent_1.8px)] [background-size:18px_18px]" />
        <div className="absolute bottom-8 right-12 w-[260px] h-[260px] opacity-40 bg-[radial-gradient(circle,#2563eb_1.5px,transparent_1.8px)] [background-size:18px_18px]" />
        <div className="absolute inset-y-0 right-0 w-[45%] opacity-25 pointer-events-none">
          <div className="absolute inset-0 neon-diagonal-lines" />
        </div>
        <div className="absolute left-1/2 top-1/2 w-[620px] h-[620px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/10 blur-[120px] neon-breathe" />

        <div className="relative z-10 w-full max-w-[760px]">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center">
              <img
                src="/apple-touch-icon.png"
                alt=""
                className="h-full w-full object-contain drop-shadow-[0_0_18px_rgba(14,165,233,0.45)]"
              />
            </div>
            <span className="text-xl font-bold tracking-tight text-[#020817]">
              Play Wave
            </span>
          </div>

          <div className="relative flex items-center justify-center">
            <div className="absolute left-[40px] md:left-[80px] top-1/2 -translate-y-1/2 w-[160px] md:w-[210px] h-[520px] rounded-[28px] bg-gradient-to-b from-sky-400 via-blue-600 to-blue-800 shadow-[0_30px_80px_rgba(37,99,235,0.35)] neon-panel-glow overflow-hidden">
              <div className="absolute inset-0 opacity-25 rounded-[28px] bg-[radial-gradient(circle,rgba(255,255,255,0.35)_1px,transparent_1.5px)] [background-size:18px_18px]" />
              <div className="absolute inset-x-0 top-[45%] h-[2px] bg-cyan-200/90 shadow-[0_0_18px_rgba(125,211,252,0.95)] neon-scanline" />
              <PanelParticles />
            </div>

            <div className="absolute left-[10px] md:left-[35px] top-[70px] z-20 w-[135px] h-[125px] rounded-[22px] bg-white shadow-[0_25px_70px_rgba(15,23,42,0.18)] border border-slate-100 flex items-center justify-center floating-card">
              <div className="absolute inset-[-12px] rounded-[28px] border border-cyan-300/40 neon-orbit" />
              <div className="relative w-[72px] h-[82px]">
                <svg viewBox="0 0 90 100" fill="none" className="w-full h-full">
                  <path
                    d="M45 4L80 18V43C80 67 65 86 45 96C25 86 10 67 10 43V18L45 4Z"
                    fill="url(#shieldGradient)"
                  />
                  <path
                    d="M30 50L41 61L63 36"
                    stroke="white"
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <defs>
                    <linearGradient id="shieldGradient" x1="10" y1="4" x2="80" y2="96">
                      <stop stopColor="#38bdf8" />
                      <stop offset="0.55" stopColor="#2563eb" />
                      <stop offset="1" stopColor="#1d4ed8" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>

            <div className="card-soft-sparks relative z-10 w-full max-w-[520px] ml-[90px] md:ml-[150px] bg-white rounded-[30px] border border-slate-200 shadow-[0_35px_100px_rgba(15,23,42,0.18)] px-8 md:px-12 py-10 md:py-14 overflow-hidden">
              <div className="absolute inset-x-8 top-0 h-[1px] bg-gradient-to-r from-transparent via-cyan-300 to-transparent opacity-80" />
              <div className="mb-5 flex flex-col items-center">
                <img
                  src="/apple-touch-icon.png"
                  alt=""
                  className="h-12 w-12 object-contain drop-shadow-[0_0_22px_rgba(14,165,233,0.45)]"
                />
                <span className="mt-2 text-xl font-extrabold tracking-tight text-[#020817]">
                  PlayWave
                </span>
              </div>
              <h2 className="text-[34px] md:text-[38px] leading-tight font-extrabold tracking-tight text-[#020817]">
                Bem-vindo de volta
              </h2>

              <p className="mt-3 text-[17px] text-slate-500">
                Acesse sua conta para gerenciar o sistema
              </p>

              <form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-9 space-y-7">
                <div>
                  <Label htmlFor="email" className="block mb-3 text-[16px] font-bold text-[#020817]">
                    E-mail
                  </Label>

                  <div className="relative neon-input-wrap">
                    <span className="absolute left-5 top-1/2 -translate-y-1/2 text-blue-600">
                      <EmailIcon className="w-6 h-6" />
                    </span>
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
                      className={`w-full h-[62px] rounded-xl border-slate-300 bg-white pl-14 pr-5 text-[17px] text-slate-700 placeholder:text-slate-400 shadow-none transition focus-visible:ring-4 focus-visible:ring-blue-600/10 ${
                        errors.email ? "border-destructive focus-visible:ring-destructive/20" : "focus-visible:border-blue-600"
                      }`}
                      {...register("email")}
                    />
                  </div>

                  {errors.email && (
                    <p id="email-error" role="alert" className="mt-2 text-xs text-destructive">
                      {errors.email.message}
                    </p>
                  )}
                </div>

                <div>
                  <Label htmlFor="password" className="block mb-3 text-[16px] font-bold text-[#020817]">
                    Senha
                  </Label>

                  <div className="relative neon-input-wrap">
                    <span className="absolute left-5 top-1/2 -translate-y-1/2 text-blue-600">
                      <LockIcon className="w-6 h-6" />
                    </span>
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    disabled={isSubmitting || isLocked}
                    aria-invalid={!!errors.password}
                    aria-describedby={errors.password ? "password-error" : undefined}
                    className={`w-full h-[62px] rounded-xl border-slate-300 bg-white pl-14 pr-14 text-[17px] text-slate-700 placeholder:text-slate-500 shadow-none transition focus-visible:ring-4 focus-visible:ring-blue-600/10 ${
                      errors.password ? "border-destructive focus-visible:ring-destructive/20" : "focus-visible:border-blue-600"
                    }`}
                    {...register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    disabled={isSubmitting || isLocked}
                    tabIndex={-1}
                    aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                    className="absolute right-5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50"
                  >
                    {showPassword ? (
                      <EyeOff className="w-6 h-6" />
                    ) : (
                      <Eye className="w-6 h-6" />
                    )}
                  </button>
                </div>
                {errors.password && (
                  <p id="password-error" role="alert" className="mt-2 text-xs text-destructive">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <div className="flex items-center justify-between gap-3 text-[16px]">
                <label className="flex items-center gap-3 text-slate-500 cursor-pointer">
                  <Checkbox
                    id="remember"
                    checked={remember}
                    onCheckedChange={(checked) => setValue("remember", !!checked)}
                    disabled={isSubmitting || isLocked}
                    className="w-5 h-5 rounded border-slate-300 bg-white shadow-sm"
                  />
                  Lembrar acesso neste dispositivo
                </label>
                <Link to="/esqueci-senha" className="text-blue-600 font-medium whitespace-nowrap">
                  Esqueci minha senha
                </Link>
              </div>

              {serverError && (
                <div
                  role="alert"
                  className="flex gap-3 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3"
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

              {isLocked && (
                <div
                  role="status"
                  aria-live="polite"
                  className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3"
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

              <Button
                type="submit"
                size="lg"
                className="button-sparks relative w-full h-[64px] rounded-xl bg-[#075bff] hover:bg-blue-700 text-white text-[21px] font-bold shadow-[0_18px_35px_rgba(37,99,235,0.35)] transition overflow-hidden neon-button"
                disabled={isSubmitting || isLocked}
              >
                <span className="relative z-10 flex items-center justify-center">
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
                </span>
                <span className="absolute inset-0 neon-button-sweep" />
              </Button>

                <div className="flex items-center justify-center gap-3 pt-2 text-[16px] text-slate-500">
                  <ShieldSmallIcon className="w-6 h-6 text-blue-600 neon-icon-pulse" />
                  <span>Seus dados estão protegidos</span>
                </div>
              </form>
            </div>
          </div>

          <div className="mt-14 text-center text-[16px] leading-7 text-slate-500">
            <p>Play Wave Digital Signage &copy; {new Date().getFullYear()}</p>
            <p>Acesso monitorado e protegido</p>
          </div>
        </div>
      </section>
    </main>
  );
}

function FeatureSmall({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-blue-500/20 bg-blue-600/15 text-blue-400 shadow-[0_0_35px_rgba(37,99,235,0.25)]">
        <Icon className="w-7 h-7" />
      </div>
      <div>
        <p className="text-sm font-bold">{title}</p>
        <p className="text-sm text-slate-300">{subtitle}</p>
      </div>
    </div>
  );
}

function ParticlesAndSparks() {
  const particles = [
    { left: "8%", top: "12%", size: 5, delay: "0s", duration: "7s" },
    { left: "16%", top: "24%", size: 3, delay: "1.2s", duration: "8s" },
    { left: "27%", top: "15%", size: 6, delay: "2s", duration: "9s" },
    { left: "38%", top: "30%", size: 4, delay: "0.8s", duration: "7.5s" },
    { left: "53%", top: "18%", size: 5, delay: "1.8s", duration: "8.5s" },
    { left: "69%", top: "22%", size: 4, delay: "2.5s", duration: "9s" },
    { left: "82%", top: "30%", size: 6, delay: "1s", duration: "7s" },
    { left: "10%", top: "58%", size: 4, delay: "2.2s", duration: "8s" },
    { left: "22%", top: "70%", size: 6, delay: "0.5s", duration: "9.5s" },
    { left: "35%", top: "64%", size: 3, delay: "1.5s", duration: "7.5s" },
    { left: "50%", top: "78%", size: 5, delay: "2.8s", duration: "8.5s" },
    { left: "72%", top: "68%", size: 4, delay: "0.9s", duration: "8s" },
    { left: "88%", top: "76%", size: 5, delay: "1.7s", duration: "9s" },
    { left: "6%", top: "34%", size: 4, delay: "3.1s", duration: "8.4s" },
    { left: "14%", top: "42%", size: 5, delay: "2.7s", duration: "9.2s" },
    { left: "24%", top: "38%", size: 3, delay: "3.4s", duration: "7.8s" },
    { left: "42%", top: "12%", size: 4, delay: "3s", duration: "8.8s" },
    { left: "58%", top: "36%", size: 6, delay: "3.6s", duration: "9.4s" },
    { left: "63%", top: "48%", size: 3, delay: "4.1s", duration: "7.6s" },
    { left: "74%", top: "42%", size: 5, delay: "3.3s", duration: "8.6s" },
    { left: "91%", top: "40%", size: 4, delay: "3.9s", duration: "9.1s" },
    { left: "7%", top: "82%", size: 3, delay: "4.2s", duration: "8.2s" },
    { left: "18%", top: "86%", size: 4, delay: "3.8s", duration: "9.6s" },
    { left: "30%", top: "82%", size: 5, delay: "4.6s", duration: "8.9s" },
    { left: "43%", top: "92%", size: 3, delay: "3.5s", duration: "7.9s" },
    { left: "58%", top: "90%", size: 4, delay: "4.4s", duration: "9.7s" },
    { left: "82%", top: "88%", size: 6, delay: "4.8s", duration: "8.7s" },
    { left: "94%", top: "84%", size: 3, delay: "5.1s", duration: "9.3s" },
  ];

  const sparks = [
    { left: "18%", top: "18%", delay: "0s" },
    { left: "31%", top: "42%", delay: "1.4s" },
    { left: "66%", top: "14%", delay: "0.8s" },
    { left: "76%", top: "48%", delay: "2.1s" },
    { left: "44%", top: "70%", delay: "1.1s" },
    { left: "86%", top: "62%", delay: "2.6s" },
    { left: "12%", top: "46%", delay: "3.2s" },
    { left: "24%", top: "82%", delay: "3.7s" },
    { left: "52%", top: "32%", delay: "3.4s" },
    { left: "61%", top: "84%", delay: "4s" },
    { left: "92%", top: "34%", delay: "4.5s" },
    { left: "78%", top: "82%", delay: "5s" },
  ];

  return (
    <div className="absolute inset-0 z-20 pointer-events-none overflow-hidden">
      <div className="absolute left-[4%] top-[10%] w-[420px] h-[420px] rounded-full bg-cyan-300/10 blur-[90px] particle-fog" />
      <div className="absolute right-[8%] bottom-[10%] w-[380px] h-[380px] rounded-full bg-blue-500/10 blur-[100px] particle-fog particle-fog-delay" />

      {particles.map((particle, index) => (
        <span
          key={`particle-${index}`}
          className="absolute rounded-full particle-dot"
          style={{
            left: particle.left,
            top: particle.top,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            animationDelay: particle.delay,
            animationDuration: particle.duration,
          }}
        />
      ))}

      {sparks.map((spark, index) => (
        <span
          key={`spark-${index}`}
          className="absolute particle-spark"
          style={{
            left: spark.left,
            top: spark.top,
            animationDelay: spark.delay,
          }}
        />
      ))}

    </div>
  );
}

function PanelParticles() {
  const particles = [
    { left: "18%", top: "9%", size: 4, delay: "0s", duration: "4.8s" },
    { left: "52%", top: "13%", size: 3, delay: "1.1s", duration: "5.4s" },
    { left: "78%", top: "18%", size: 5, delay: "0.6s", duration: "5.1s" },
    { left: "30%", top: "28%", size: 3, delay: "1.8s", duration: "4.6s" },
    { left: "66%", top: "34%", size: 4, delay: "2.2s", duration: "5.8s" },
    { left: "20%", top: "45%", size: 5, delay: "0.9s", duration: "5.2s" },
    { left: "48%", top: "52%", size: 3, delay: "2.8s", duration: "4.9s" },
    { left: "82%", top: "58%", size: 4, delay: "1.5s", duration: "5.6s" },
    { left: "34%", top: "68%", size: 4, delay: "3.1s", duration: "5s" },
    { left: "70%", top: "76%", size: 5, delay: "2.5s", duration: "5.9s" },
    { left: "16%", top: "84%", size: 3, delay: "3.7s", duration: "4.7s" },
    { left: "56%", top: "90%", size: 4, delay: "1.9s", duration: "5.3s" },
  ];

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {particles.map((particle, index) => (
        <span
          key={index}
          className="absolute rounded-full panel-particle"
          style={{
            left: particle.left,
            top: particle.top,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            animationDelay: particle.delay,
            animationDuration: particle.duration,
          }}
        />
      ))}
    </div>
  );
}

function MetricCard({ title, value, suffix, status, type }) {
  return (
    <div className="min-h-[130px] overflow-hidden rounded-2xl border border-blue-300/15 bg-[#071a33]/80 p-4">
      <p className="text-sm font-semibold">{title}</p>
      <div className="mt-4 flex items-end justify-between gap-3">
        <div>
          <div className="flex items-end gap-2">
            <strong className="text-4xl leading-none">{value}</strong>
            <span className="mb-1 text-sm text-slate-300">{suffix}</span>
          </div>
          {status && (
            <div className="mt-4 flex items-center gap-2 text-sm text-slate-300">
              <span className="text-emerald-400">↑</span>
              {status}
            </div>
          )}
        </div>
        {type === "bar" ? <MiniBars /> : <MiniLine />}
      </div>
    </div>
  );
}

function MiniLine() {
  return (
    <svg width="150" height="62" viewBox="0 0 170 62" fill="none" className="max-w-[45%]">
      <path
        d="M2 50 C16 45, 24 55, 36 46 C48 37, 58 25, 72 38 C84 49, 94 26, 108 34 C120 43, 126 22, 140 20 C152 18, 156 8, 168 4"
        stroke="#0b6cff"
        strokeWidth="3"
        fill="none"
      />
      <path
        d="M2 50 C16 45, 24 55, 36 46 C48 37, 58 25, 72 38 C84 49, 94 26, 108 34 C120 43, 126 22, 140 20 C152 18, 156 8, 168 4 L168 62 L2 62 Z"
        fill="url(#lineGradient)"
      />
      <defs>
        <linearGradient id="lineGradient" x1="85" y1="4" x2="85" y2="62">
          <stop stopColor="#0b6cff" stopOpacity="0.35" />
          <stop offset="1" stopColor="#0b6cff" stopOpacity="0" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function MiniBars() {
  const bars = [8, 12, 18, 30, 46, 34, 58, 42, 68, 50];

  return (
    <div className="flex h-[66px] items-end gap-2">
      {bars.map((height, index) => (
        <div
          key={index}
          className="w-2.5 rounded-t bg-blue-500 shadow-[0_0_16px_rgba(37,99,235,0.65)]"
          style={{ height }}
        />
      ))}
    </div>
  );
}

function ActivityItem({ icon, text, time, color }) {
  const colorClass =
    color === "blue"
      ? "bg-blue-600 text-white"
      : color === "yellow"
        ? "bg-yellow-400 text-slate-950"
        : "bg-slate-600 text-white";

  return (
    <div className="flex items-center justify-between gap-4 text-slate-200">
      <div className="flex min-w-0 items-center gap-2">
        <span
          className={`flex h-5 w-5 items-center justify-center rounded-md text-[11px] font-bold ${colorClass}`}
        >
          {icon}
        </span>
        <span className="truncate">{text}</span>
      </div>
      <span className="whitespace-nowrap text-slate-300">{time}</span>
    </div>
  );
}

function StatusLine({ color, label, value }) {
  return (
    <div className="grid grid-cols-[12px_1fr_30px] items-center gap-3">
      <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, text }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-blue-300/20 bg-blue-600/10 p-5">
      <div className="absolute top-0 left-6 h-2 w-8 -translate-y-1 rotate-45 bg-[#020817]" />
      <div className="mb-3 text-blue-400">
        <Icon className="w-10 h-10" />
      </div>
      <h3 className="text-sm font-bold">{title}</h3>
      <p className="mt-1 text-sm leading-5 text-slate-300">{text}</p>
    </div>
  );
}

function EmailIcon({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <path
        d="M4 6.5h16v11H4v-11Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M4.5 7L12 13L19.5 7"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LockIcon({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <rect
        x="5"
        y="10"
        width="14"
        height="10"
        rx="2"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path
        d="M8 10V7a4 4 0 0 1 8 0v3"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M12 14v2"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ShieldSmallIcon({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none">
      <path
        d="M12 3L20 7V12C20 17 16.5 20 12 21C7.5 20 4 17 4 12V7L12 3Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path
        d="M9 12L11 14L15 10"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * App.jsx — Roteador principal do SignControl
 *
 * Estrutura de módulos:
 *  - /                   → Dashboard
 *  - /dispositivos/*     → Gestão de telas/players
 *  - /midias/*           → Biblioteca de arquivos
 *  - /campanhas/*        → Campanhas e playlists
 *  - /agenda             → Calendário de campanhas
 *  - /monitoramento      → Status em tempo real
 *  - /relatorios         → Relatórios de exibição
 *  - /localizacoes       → Grupos e locais
 *  - /audio/*            → Rádio Indoor
 *  - /configuracoes/*    → Empresa e usuários
 *  - /planos             → Planos de assinatura
 *  - /player             → Player de tela (sem layout)
 *  - /dev/quickstart     → Documentação de integração
 */

import { Toaster } from "@/components/ui/toaster";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClientInstance } from "@/lib/query-client";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import PageNotFound from "./lib/PageNotFound";
import { AuthProvider, useAuth } from "@/lib/AuthContext";
import UserNotRegisteredError from "@/components/UserNotRegisteredError";

// Layout
import AppLayout from "@/components/layout/AppLayout";

// ── Módulo: Dashboard ─────────────────────────────────────────────────────────
import Dashboard from "@/pages/Dashboard";

// ── Módulo: Dispositivos ──────────────────────────────────────────────────────
import Dispositivos from "@/pages/Dispositivos";
import NovoDispositivo from "@/pages/DispositivoNovo";
import DetalhesDispositivo from "@/pages/DispositivoDetalhe";

// ── Módulo: Mídias ────────────────────────────────────────────────────────────
import BibliotecaMidias from "@/pages/BibliotecaMidias";
import UploadMidia from "@/pages/MidiaUpload";

// ── Módulo: Campanhas ─────────────────────────────────────────────────────────
import Campanhas from "@/pages/Campanhas";
import NovaCampanha from "@/pages/Campanhas";
import PreviewCampanha from "@/pages/CampanhaPreview";
import EditorPlaylist from "@/pages/EditorPlaylist";

// ── Módulo: Agenda ────────────────────────────────────────────────────────────
import Agenda from "@/pages/Agenda";

// ── Módulo: Monitoramento ─────────────────────────────────────────────────────
import Monitoramento from "@/pages/Monitoramento";

// ── Módulo: Relatórios ────────────────────────────────────────────────────────
import Relatorios from "@/pages/Relatorios";

// ── Módulo: Localizações ──────────────────────────────────────────────────────
import Localizacoes from "@/pages/Localizacoes";

// ── Módulo: Rádio Indoor (Áudio) ──────────────────────────────────────────────
import FaixasAudio from "@/pages/FaixasAudio";
import PlaylistsSonoras from "@/pages/PlaylistsSonoras";

// ── Módulo: Configurações ─────────────────────────────────────────────────────
import ConfiguracaoEmpresa from "@/pages/ConfigEmpresa";
import ConfiguracaoUsuarios from "@/pages/ConfigUsuario";
import Planos from "@/pages/Planos";

// ── Módulo: Player (sem layout de admin) ─────────────────────────────────────
import Player from "@/pages/Player.jsx";

// ── Módulo: Dev / Integração ──────────────────────────────────────────────────
import Quickstart from "@/pages/Quickstart";

const AppAutenticado = () => {
  const { isLoadingAuth, isLoadingPublicSettings, authError, navigateToLogin } =
    useAuth();

  if (isLoadingPublicSettings || isLoadingAuth) {
    return (
      <div className="fixed inset-0 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-slate-200 border-t-slate-800 rounded-full animate-spin" />
      </div>
    );
  }

  if (authError) {
    if (authError.type === "user_not_registered")
      return <UserNotRegisteredError />;
    if (authError.type === "auth_required") {
      navigateToLogin();
      return null;
    }
  }

  return (
    <Routes>
      {/* Player de tela — sem barra lateral */}
      <Route path="/player" element={<Player />} />

      {/* Admin — com layout */}
      <Route element={<AppLayout />}>
        {/* Dashboard */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />

        {/* Dispositivos */}
        <Route path="/dispositivos" element={<Dispositivos />} />
        <Route path="/dispositivos/novo" element={<NovoDispositivo />} />
        <Route path="/dispositivos/:id" element={<DetalhesDispositivo />} />

        {/* Mídias */}
        <Route path="/midias" element={<BibliotecaMidias />} />
        <Route path="/midias/upload" element={<UploadMidia />} />

        {/* Campanhas */}
        <Route path="/campanhas" element={<Campanhas />} />
        <Route path="/campanhas/nova" element={<NovaCampanha />} />
        <Route path="/campanhas/:id/preview" element={<PreviewCampanha />} />
        <Route path="/campanhas/:id/playlist" element={<EditorPlaylist />} />

        {/* Agenda */}
        <Route path="/agenda" element={<Agenda />} />

        {/* Monitoramento */}
        <Route path="/monitoramento" element={<Monitoramento />} />

        {/* Relatórios */}
        <Route path="/relatorios" element={<Relatorios />} />

        {/* Localizações */}
        <Route path="/localizacoes" element={<Localizacoes />} />

        {/* Rádio Indoor */}
        <Route path="/audio/faixas" element={<FaixasAudio />} />
        <Route path="/audio/playlists" element={<PlaylistsSonoras />} />

        {/* Configurações */}
        <Route
          path="/configuracoes/empresa"
          element={<ConfiguracaoEmpresa />}
        />
        <Route
          path="/configuracoes/usuarios"
          element={<ConfiguracaoUsuarios />}
        />
        <Route path="/planos" element={<Planos />} />

        {/* Dev */}
        <Route path="/dev/quickstart" element={<Quickstart />} />

        {/* Rotas legadas — redireciona para novas */}
        <Route path="/devices" element={<Dispositivos />} />
        <Route path="/devices/new" element={<NovoDispositivo />} />
        <Route path="/devices/:id" element={<DetalhesDispositivo />} />
        <Route path="/media" element={<BibliotecaMidias />} />
        <Route path="/media/upload" element={<UploadMidia />} />
        <Route path="/campaigns" element={<Campanhas />} />
        <Route path="/campaigns/new" element={<NovaCampanha />} />
        <Route path="/campaigns/:id/preview" element={<PreviewCampanha />} />
        <Route path="/campaigns/:id/playlist" element={<EditorPlaylist />} />
        <Route path="/schedule" element={<Agenda />} />
        <Route path="/monitoring" element={<Monitoramento />} />
        <Route path="/reports" element={<Relatorios />} />
        <Route path="/locations" element={<Localizacoes />} />
        <Route path="/audio/tracks" element={<FaixasAudio />} />
        <Route path="/settings/company" element={<ConfiguracaoEmpresa />} />
        <Route path="/settings/users" element={<ConfiguracaoUsuarios />} />
        <Route path="/billing/plans" element={<Planos />} />
        <Route path="/quickstart" element={<Quickstart />} />
      </Route>

      <Route path="*" element={<PageNotFound />} />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClientInstance}>
        <Router>
          <AppAutenticado />
        </Router>
        <Toaster />
      </QueryClientProvider>
    </AuthProvider>
  );
}

export default App;

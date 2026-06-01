import { Toaster } from "@/components/ui/toaster";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClientInstance } from "@/lib/query-client";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import PageNotFound from "./lib/PageNotFound";
import { AuthProvider } from "@/lib/AuthContext";
import ProtectedRoute from "@/components/shared/ProtectedRoute";
import SessionExpiredModal from "@/components/shared/SessionExpiredModal";
import ErrorBoundary from "@/components/shared/ErrorBoundary";

// Layout
import AppLayout from "@/components/layout/AppLayout";

// Dashboard
import Dashboard from "@/pages/Dashboard";

// Dispositivos
import Dispositivos from "@/pages/Dispositivos";
import NovoDispositivo from "@/pages/DispositivoNovo";
import DetalhesDispositivo from "@/pages/DispositivoDetalhe";

// Mídias
import BibliotecaMidias from "@/pages/BibliotecaMidias";
import UploadMidia from "@/pages/MidiaUpload";

// Campanhas
import Campanhas from "@/pages/Campanhas";
import PreviewCampanha from "@/pages/CampanhaPreview";
import EditorPlaylist from "@/pages/EditorPlaylist";

// Agenda
import Agenda from "@/pages/agenda";

// Monitoramento
import Monitoramento from "@/pages/Monitoramento";

// Relatórios
import Relatorios from "@/pages/Relatorios";

// Localizações
import Localizacoes from "@/pages/Localizacoes";

// Rádio Indoor
import FaixasAudio from "@/pages/FaixasAudio";
import PlaylistsSonoras from "@/pages/PlaylistsSonoras";
import PlaylistDetalhe from "@/pages/PlaylistDetalhe";

// Configurações
import ConfiguracaoEmpresa from "@/pages/ConfigEmpresa";
import ConfiguracaoUsuarios from "@/pages/ConfigUsuario";
import Planos from "@/pages/Planos";

// Player
import Player from "@/pages/Player.jsx";

// Dev
import Quickstart from "@/pages/Quickstart";
import Apresentacao from "@/pages/Apresentacao";

// Login
import Login from "@/pages/Login";

function isNativePlayerShell() {
  if (typeof window === "undefined") return false;
  const platform = window.Capacitor?.getPlatform?.();
  return Boolean(platform && platform !== "web");
}

function App() {
  const nativePlayerShell = isNativePlayerShell();

  return (
    // Router envolve tudo — AuthProvider pode usar useNavigate() com segurança
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <QueryClientProvider client={queryClientInstance}>
          <ErrorBoundary>
            <Routes>
            {/* Pública */}
            <Route path="/login" element={<Login />} />

            {/* Player de TV — autenticação de device, sem layout admin */}
            {nativePlayerShell && <Route path="/" element={<Player />} />}
            <Route path="/player" element={<Player />} />
            <Route path="/apresentacao" element={<Apresentacao />} />

            {/* Rotas protegidas — com layout */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="dashboard" element={<Dashboard />} />

              {/* Dispositivos */}
              <Route path="dispositivos" element={<Dispositivos />} />
              <Route path="dispositivos/novo" element={<NovoDispositivo />} />
              <Route path="dispositivos/:id" element={<DetalhesDispositivo />} />

              {/* Mídias */}
              <Route path="midias" element={<BibliotecaMidias />} />
              <Route path="midias/upload" element={<UploadMidia />} />

              {/* Campanhas */}
              <Route path="campanhas" element={<Campanhas />} />
              <Route path="campanhas/nova" element={<Campanhas />} />
              <Route path="campanhas/:id/preview" element={<PreviewCampanha />} />
              <Route path="campanhas/:id/playlist" element={<EditorPlaylist />} />

              {/* Agenda */}
              <Route path="agenda" element={<Agenda />} />

              {/* Monitoramento */}
              <Route path="monitoramento" element={<Monitoramento />} />

              {/* Relatórios */}
              <Route path="relatorios" element={<Relatorios />} />

              {/* Localizações */}
              <Route path="localizacoes" element={<Localizacoes />} />

              {/* Rádio Indoor */}
              <Route path="radio/faixas" element={<FaixasAudio />} />
              <Route path="radio/playlists" element={<PlaylistsSonoras />} />
              <Route path="radio/playlists/:id" element={<PlaylistDetalhe />} />

              {/* Configurações — apenas admin */}
              <Route
                path="configuracoes/empresa"
                element={
                  <ProtectedRoute allowedRoles={["admin"]}>
                    <ConfiguracaoEmpresa />
                  </ProtectedRoute>
                }
              />
              <Route
                path="configuracoes/usuarios"
                element={
                  <ProtectedRoute allowedRoles={["admin"]}>
                    <ConfiguracaoUsuarios />
                  </ProtectedRoute>
                }
              />
              <Route
                path="planos"
                element={
                  <ProtectedRoute allowedRoles={["admin"]}>
                    <Planos />
                  </ProtectedRoute>
                }
              />

              {/* Dev */}
              <Route path="dev/quickstart" element={<Quickstart />} />

              {/* Aliases legados */}
              <Route path="devices" element={<Dispositivos />} />
              <Route path="devices/new" element={<NovoDispositivo />} />
              <Route path="devices/:id" element={<DetalhesDispositivo />} />
              <Route path="media" element={<BibliotecaMidias />} />
              <Route path="media/upload" element={<UploadMidia />} />
              <Route path="campaigns" element={<Campanhas />} />
              <Route path="campaigns/new" element={<Campanhas />} />
              <Route path="campaigns/:id/preview" element={<PreviewCampanha />} />
              <Route path="campaigns/:id/playlist" element={<EditorPlaylist />} />
              <Route path="schedule" element={<Agenda />} />
              <Route path="monitoring" element={<Monitoramento />} />
              <Route path="reports" element={<Relatorios />} />
              <Route path="locations" element={<Localizacoes />} />
              <Route path="audio/tracks" element={<FaixasAudio />} />
              <Route path="settings/company" element={<ConfiguracaoEmpresa />} />
              <Route path="settings/users" element={<ConfiguracaoUsuarios />} />
              <Route
                path="billing/plans"
                element={
                  <ProtectedRoute allowedRoles={["admin"]}>
                    <Planos />
                  </ProtectedRoute>
                }
              />
              <Route path="quickstart" element={<Quickstart />} />
            </Route>

            <Route path="*" element={<PageNotFound />} />
          </Routes>
          </ErrorBoundary>

          <Toaster />
          <SessionExpiredModal />
        </QueryClientProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;

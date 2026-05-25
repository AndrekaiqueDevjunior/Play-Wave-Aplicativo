import React, { createContext, useState, useContext, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

// ─── Utilitários de JWT ──────────────────────────────────────────────────────

function decodeJwtPayload(token) {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
}

function isTokenExpired(token) {
  const payload = decodeJwtPayload(token);
  if (!payload?.exp) return true;
  // 30 segundos de margem antes da expiração real
  return payload.exp * 1000 < Date.now() + 30_000;
}

// ─── Abstração de storage ────────────────────────────────────────────────────
// sessionStorage = limpa ao fechar o browser (padrão)
// localStorage   = persiste entre sessões ("Lembrar acesso")

const TOKEN_KEY = "pw_access_token";
const USER_KEY  = "pw_user";

function getStoredToken() {
  return sessionStorage.getItem(TOKEN_KEY) ?? localStorage.getItem(TOKEN_KEY) ?? null;
}

function getStoredUser() {
  const raw = sessionStorage.getItem(USER_KEY) ?? localStorage.getItem(USER_KEY);
  try { return raw ? JSON.parse(raw) : null; } catch { return null; }
}

function storeSession(token, user, remember) {
  const primary   = remember ? localStorage  : sessionStorage;
  const secondary = remember ? sessionStorage : localStorage;
  primary.setItem(TOKEN_KEY, token);
  primary.setItem(USER_KEY, JSON.stringify(user));
  secondary.removeItem(TOKEN_KEY);
  secondary.removeItem(USER_KEY);
}

function clearSession() {
  [localStorage, sessionStorage].forEach((s) => {
    s.removeItem(TOKEN_KEY);
    s.removeItem(USER_KEY);
  });
}

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const navigate = useNavigate();

  const [user, setUser]                     = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth]   = useState(true);

  // Verifica sessão ao carregar o app
  const checkAuth = useCallback(async () => {
    const token = getStoredToken();

    if (!token || isTokenExpired(token)) {
      clearSession();
      setUser(null);
      setIsAuthenticated(false);
      setIsLoadingAuth(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        // Token inválido no servidor
        clearSession();
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch {
      // Sem conexão com o backend — usa cache local para não expulsar o usuário
      const cached = getStoredUser();
      if (cached && !isTokenExpired(token)) {
        setUser(cached);
        setIsAuthenticated(true);
      } else {
        clearSession();
        setUser(null);
        setIsAuthenticated(false);
      }
    } finally {
      setIsLoadingAuth(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Login — lança exceção com mensagem traduzida se falhar
  const login = useCallback(async (email, password, remember = false) => {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const status = res.status;

      if (status === 401) throw new Error("E-mail ou senha incorretos.");
      if (status === 403) throw new Error("Conta inativa. Contate o administrador.");
      if (status === 422) throw new Error("Dados inválidos. Verifique e-mail e senha.");
      if (status >= 500) throw new Error("Erro no servidor. Tente novamente em instantes.");
      throw new Error(body.detail || "Erro ao fazer login.");
    }

    const data = await res.json();
    storeSession(data.access_token, data.user, remember);
    setUser(data.user);
    setIsAuthenticated(true);
    return data.user;
  }, []);

  // Logout — notifica o backend e limpa sessão local
  const logout = useCallback(async () => {
    const token = getStoredToken();
    if (token) {
      // Fire-and-forget — não bloqueia o logout local se o backend falhar
      fetch(`${API_URL}/api/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
    clearSession();
    setUser(null);
    setIsAuthenticated(false);
    navigate("/login", { replace: true });
  }, [navigate]);

  // Retorna o token atual para usar em chamadas autenticadas
  const getToken = useCallback(() => getStoredToken(), []);

  // Verifica role exato
  const hasRole = useCallback((role) => user?.role === role, [user]);

  // Verifica permissão por módulo
  const hasPermission = useCallback((permission) => {
    if (!user) return false;
    if (user.role === "admin") return true;
    if (user.role === "operator") {
      return ["campaigns", "media", "playlists", "devices", "reports"].includes(permission);
    }
    if (user.role === "viewer") return true;
    return false;
  }, [user]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoadingAuth,
        login,
        logout,
        getToken,
        hasRole,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  return ctx;
}

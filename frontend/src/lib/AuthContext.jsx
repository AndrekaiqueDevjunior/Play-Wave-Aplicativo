import React, { createContext, useState, useContext, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";

let API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
if (typeof window !== "undefined" && window.__ELECTRON__?.backendUrl) {
  API_URL = window.__ELECTRON__.backendUrl.replace(/\/$/, "");
}

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

const INACTIVITY_MS = 30 * 60 * 1000; // 30 minutos

// ─── Context ─────────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const navigate = useNavigate();

  const [user, setUser]                     = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth]   = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);
  const inactivityTimer = useRef(null);

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

  // Timer de inatividade + listener do evento pw:session-expired
  useEffect(() => {
    const handleExpired = () => setSessionExpired(true);
    window.addEventListener("pw:session-expired", handleExpired);

    const resetTimer = () => {
      clearTimeout(inactivityTimer.current);
      // Só conta inatividade quando autenticado
      if (sessionStorage.getItem("pw_access_token") || localStorage.getItem("pw_access_token")) {
        inactivityTimer.current = setTimeout(() => {
          clearSession();
          setSessionExpired(true);
        }, INACTIVITY_MS);
      }
    };

    const EVENTS = ["mousemove", "keydown", "mousedown", "touchstart", "scroll"];
    EVENTS.forEach((e) => window.addEventListener(e, resetTimer, { passive: true }));
    resetTimer();

    return () => {
      window.removeEventListener("pw:session-expired", handleExpired);
      EVENTS.forEach((e) => window.removeEventListener(e, resetTimer));
      clearTimeout(inactivityTimer.current);
    };
  }, []);

  // Login — chama o backend e armazena o JWT real
  const login = useCallback(async (email, password, remember = false) => {
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      let detail = "Erro ao fazer login";
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch { /* ignore */ }
      throw new Error(detail);
    }

    const data = await res.json();
    const token = data.access_token;
    const userData = data.user ?? { email };

    storeSession(token, userData, remember);
    setUser(userData);
    setIsAuthenticated(true);
    return userData;
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

  const dismissSessionExpired = useCallback(() => {
    setSessionExpired(false);
    setUser(null);
    setIsAuthenticated(false);
    navigate("/login", { replace: true });
  }, [navigate]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoadingAuth,
        sessionExpired,
        dismissSessionExpired,
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

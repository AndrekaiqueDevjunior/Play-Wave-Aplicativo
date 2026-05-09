import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Monitor,
  Image,
  Megaphone,
  Calendar,
  Activity,
  BarChart3,
  MapPin,
  Settings,
  CreditCard,
  X,
  Radio,
  ListMusic,
  Zap,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/AuthContext";

/**
 * Estrutura modular do menu lateral — agrupado por domínio de negócio.
 * Cada grupo tem label, ícone e subitens.
 */
const MENU_GRUPOS = [
  {
    label: "Início",
    items: [{ label: "Dashboard", icon: LayoutDashboard, path: "/dashboard" }],
  },
  {
    label: "Exibição",
    items: [
      { label: "Dispositivos", icon: Monitor, path: "/dispositivos" },
      { label: "Mídias", icon: Image, path: "/midias" },
      { label: "Campanhas", icon: Megaphone, path: "/campanhas" },
      { label: "Agenda", icon: Calendar, path: "/agenda" },
    ],
  },
  {
    label: "Operação",
    items: [
      { label: "Monitoramento", icon: Activity, path: "/monitoramento" },
      { label: "Relatórios", icon: BarChart3, path: "/relatorios" },
      { label: "Localizações", icon: MapPin, path: "/localizacoes" },
    ],
  },
  {
    label: "Rádio Indoor",
    items: [
      { label: "Faixas de Áudio", icon: Radio, path: "/audio/faixas" },
      { label: "Playlists Sonoras", icon: ListMusic, path: "/audio/playlists" },
    ],
  },
];

const MENU_CONFIG = [
  { label: "Configurações", icon: Settings, path: "/configuracoes/empresa" },
  { label: "Planos", icon: CreditCard, path: "/planos" },
];

const MENU_DEV = [
  { label: "Quickstart API", icon: Zap, path: "/dev/quickstart" },
];

function NavItem({ item, onClose }) {
  const location = useLocation();
  const isActive =
    location.pathname === item.path ||
    location.pathname.startsWith(item.path + "/");
  return (
    <Link
      to={item.path}
      onClick={onClose}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
        isActive
          ? "bg-sidebar-primary text-sidebar-primary-foreground"
          : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent",
      )}
    >
      <item.icon className="w-[18px] h-[18px] flex-shrink-0" />
      {item.label}
    </Link>
  );
}

function NavGroup({ grupo, onClose }) {
  const location = useLocation();
  const hasActive = grupo.items.some(
    (i) =>
      location.pathname === i.path ||
      location.pathname.startsWith(i.path + "/"),
  );
  const [open, setOpen] = useState(hasActive || true);

  return (
    <div className="mb-1">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40 hover:text-sidebar-foreground/60 transition-colors"
      >
        {grupo.label}
        {open ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
      </button>
      {open && (
        <div className="space-y-0.5">
          {grupo.items.map((item) => (
            <NavItem key={item.path} item={item} onClose={onClose} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function Sidebar({ open, onClose }) {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const configItems = MENU_CONFIG.filter((item) => {
    if (item.path === "/planos") return isAdmin;
    if (item.path === "/configuracoes/empresa") return isAdmin;
    return true;
  });

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full w-64 bg-sidebar text-sidebar-foreground flex flex-col transition-transform duration-300 ease-in-out",
          "lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 h-16 border-b border-sidebar-border flex-shrink-0">
          <Link to="/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg overflow-hidden">
              <img
                src="/playwave-icon-512.png"
                alt=""
                className="h-full w-full object-cover"
              />
            </div>
            <span className="text-lg font-bold tracking-tight">
              SignControl
            </span>
          </Link>
          <button
            onClick={onClose}
            className="lg:hidden text-sidebar-foreground/60 hover:text-sidebar-foreground"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navegação principal — com scroll */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-2">
          {MENU_GRUPOS.map((grupo) => (
            <NavGroup key={grupo.label} grupo={grupo} onClose={onClose} />
          ))}
        </nav>

        {/* Dev */}
        <div className="px-3 pb-2 border-t border-sidebar-border pt-3 space-y-0.5">
          <p className="px-3 mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
            Dev
          </p>
          {MENU_DEV.map((item) => (
            <NavItem key={item.path} item={item} onClose={onClose} />
          ))}
        </div>

        {/* Configurações e Planos */}
        <div className="px-3 pb-4 border-t border-sidebar-border pt-3 space-y-0.5">
          {configItems.map((item) => (
            <NavItem key={item.path} item={item} onClose={onClose} />
          ))}
        </div>
      </aside>
    </>
  );
}

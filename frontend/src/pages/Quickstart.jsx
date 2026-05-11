/**
 * pages/Quickstart.jsx
 * Documentação interativa do contrato FastAPI para o PlayWave.
 * Atualizada com todos os endpoints e entidades.
 */
import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Copy,
  CheckCheck,
  Terminal,
  Server,
  Radio,
  FileVideo,
  MapPin,
  BarChart2,
  Shield,
  Zap,
} from "lucide-react";

function CopyBlock({ code, lang = "bash" }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="relative group">
      <pre className="bg-slate-950 text-slate-200 rounded-xl p-4 text-xs overflow-x-auto leading-relaxed font-mono">
        <code>{code}</code>
      </pre>
      <button
        onClick={copy}
        className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors opacity-0 group-hover:opacity-100"
      >
        {copied ? (
          <CheckCheck className="w-3.5 h-3.5 text-emerald-400" />
        ) : (
          <Copy className="w-3.5 h-3.5" />
        )}
      </button>
    </div>
  );
}

function Method({ m }) {
  const colors = {
    GET: "bg-blue-100 text-blue-700",
    POST: "bg-emerald-100 text-emerald-700",
    PATCH: "bg-amber-100 text-amber-700",
    DELETE: "bg-red-100 text-red-700",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold font-mono ${colors[m] || "bg-slate-100 text-slate-700"}`}
    >
      {m}
    </span>
  );
}

function AuthBadge({ type }) {
  if (type === "device")
    return (
      <Badge className="bg-violet-100 text-violet-700 border-violet-200 text-xs">
        X-Device-Token
      </Badge>
    );
  if (type === "admin")
    return (
      <Badge className="bg-blue-100 text-blue-700 border-blue-200 text-xs">
        Admin JWT
      </Badge>
    );
  if (type === "super")
    return (
      <Badge className="bg-orange-100 text-orange-700 border-orange-200 text-xs">
        Superadmin
      </Badge>
    );
  return (
    <Badge className="bg-slate-100 text-slate-600 border-slate-200 text-xs">
      Público
    </Badge>
  );
}

const ENDPOINTS = {
  devices: [
    {
      method: "POST",
      path: "/devices/pair-request",
      auth: "public",
      desc: "TV registra código de pareamento",
    },
    {
      method: "GET",
      path: "/devices/by-code/{code}/status",
      auth: "public",
      desc: "TV faz polling do status do pareamento",
    },
    {
      method: "POST",
      path: "/devices/{id}/pair-confirm",
      auth: "admin",
      desc: "Admin confirma pareamento e cria device",
    },
    {
      method: "GET",
      path: "/devices",
      auth: "admin",
      desc: "Lista todos os dispositivos do tenant",
    },
    {
      method: "GET",
      path: "/devices/{id}",
      auth: "admin",
      desc: "Detalhe de um dispositivo",
    },
    {
      method: "PATCH",
      path: "/devices/{id}",
      auth: "admin",
      desc: "Atualiza dados do dispositivo",
    },
    {
      method: "DELETE",
      path: "/devices/{id}",
      auth: "admin",
      desc: "Remove dispositivo",
    },
    {
      method: "GET",
      path: "/devices/{id}/playlist",
      auth: "device",
      desc: "TV busca playlist visual ativa",
    },
    {
      method: "POST",
      path: "/devices/{id}/heartbeat",
      auth: "device",
      desc: "TV envia sinal de vida a cada 30s",
    },
    {
      method: "GET",
      path: "/devices/{id}/metrics",
      auth: "admin",
      desc: "Métricas em tempo real",
    },
    {
      method: "POST",
      path: "/devices/{id}/command",
      auth: "admin",
      desc: "Envia comando remoto (restart, sync...)",
    },
    {
      method: "POST",
      path: "/devices/{id}/block",
      auth: "admin",
      desc: "Bloqueia dispositivo",
    },
    {
      method: "POST",
      path: "/devices/{id}/unblock",
      auth: "admin",
      desc: "Desbloqueia dispositivo",
    },
    {
      method: "POST",
      path: "/devices/{id}/revoke-token",
      auth: "admin",
      desc: "Revoga token — força re-pareamento",
    },
  ],
  campaigns: [
    {
      method: "GET",
      path: "/campaigns",
      auth: "admin",
      desc: "Lista campanhas do tenant",
    },
    {
      method: "GET",
      path: "/campaigns/{id}",
      auth: "admin",
      desc: "Detalhe de campanha",
    },
    {
      method: "POST",
      path: "/campaigns",
      auth: "admin",
      desc: "Cria nova campanha",
    },
    {
      method: "PATCH",
      path: "/campaigns/{id}",
      auth: "admin",
      desc: "Atualiza campanha",
    },
    {
      method: "DELETE",
      path: "/campaigns/{id}",
      auth: "admin",
      desc: "Remove campanha",
    },
    {
      method: "POST",
      path: "/campaigns/{id}/publish",
      auth: "admin",
      desc: "Publica campanha nos players",
    },
    {
      method: "POST",
      path: "/campaigns/{id}/pause",
      auth: "admin",
      desc: "Pausa campanha",
    },
    {
      method: "POST",
      path: "/campaigns/{id}/resume",
      auth: "admin",
      desc: "Retoma campanha pausada",
    },
    {
      method: "GET",
      path: "/campaigns/{id}/stats",
      auth: "admin",
      desc: "Estatísticas de exibição",
    },
  ],
  media: [
    {
      method: "GET",
      path: "/media",
      auth: "admin",
      desc: "Lista biblioteca de mídias",
    },
    {
      method: "GET",
      path: "/media/{id}",
      auth: "admin",
      desc: "Detalhe de mídia",
    },
    {
      method: "POST",
      path: "/media/upload",
      auth: "admin",
      desc: "Upload de arquivo (multipart/form-data)",
    },
    {
      method: "POST",
      path: "/media",
      auth: "admin",
      desc: "Cadastra URL externa",
    },
    {
      method: "PATCH",
      path: "/media/{id}",
      auth: "admin",
      desc: "Atualiza metadados",
    },
    {
      method: "DELETE",
      path: "/media/{id}",
      auth: "admin",
      desc: "Remove mídia",
    },
  ],
  audio: [
    {
      method: "GET",
      path: "/audio/tracks",
      auth: "admin",
      desc: "Lista faixas de áudio",
    },
    {
      method: "POST",
      path: "/audio/tracks/upload",
      auth: "admin",
      desc: "Upload de faixa MP3 (multipart)",
    },
    {
      method: "PATCH",
      path: "/audio/tracks/{id}",
      auth: "admin",
      desc: "Atualiza faixa",
    },
    {
      method: "DELETE",
      path: "/audio/tracks/{id}",
      auth: "admin",
      desc: "Remove faixa",
    },
    {
      method: "GET",
      path: "/audio/playlists",
      auth: "admin",
      desc: "Lista playlists sonoras",
    },
    {
      method: "GET",
      path: "/audio/playlists/{id}",
      auth: "admin",
      desc: "Detalhe de playlist",
    },
    {
      method: "POST",
      path: "/audio/playlists",
      auth: "admin",
      desc: "Cria playlist sonora",
    },
    {
      method: "PATCH",
      path: "/audio/playlists/{id}",
      auth: "admin",
      desc: "Atualiza playlist",
    },
    {
      method: "DELETE",
      path: "/audio/playlists/{id}",
      auth: "admin",
      desc: "Remove playlist",
    },
    {
      method: "GET",
      path: "/audio/devices/{id}/playlist",
      auth: "device",
      desc: "TV busca playlist de áudio",
    },
  ],
  reports: [
    {
      method: "GET",
      path: "/reports/playback",
      auth: "admin",
      desc: "Lista logs de exibição (filtros: device, campaign, datas)",
    },
    {
      method: "GET",
      path: "/reports/summary",
      auth: "admin",
      desc: "Resumo geral (views, top campaign, views/dia)",
    },
    {
      method: "GET",
      path: "/reports/device/{id}",
      auth: "admin",
      desc: "Relatório por dispositivo",
    },
    {
      method: "GET",
      path: "/reports/campaign/{id}",
      auth: "admin",
      desc: "Relatório por campanha",
    },
    {
      method: "POST",
      path: "/reports/playback",
      auth: "device",
      desc: "TV registra exibição de mídia",
    },
    {
      method: "GET",
      path: "/reports/export/csv",
      auth: "admin",
      desc: "Download CSV com filtros",
    },
    {
      method: "GET",
      path: "/events",
      auth: "admin",
      desc: "Lista eventos de auditoria dos devices",
    },
  ],
  locations: [
    {
      method: "GET",
      path: "/locations",
      auth: "admin",
      desc: "Lista localizações do tenant",
    },
    {
      method: "GET",
      path: "/locations/{id}",
      auth: "admin",
      desc: "Detalhe de localização",
    },
    {
      method: "POST",
      path: "/locations",
      auth: "admin",
      desc: "Cria localização",
    },
    {
      method: "PATCH",
      path: "/locations/{id}",
      auth: "admin",
      desc: "Atualiza localização",
    },
    {
      method: "DELETE",
      path: "/locations/{id}",
      auth: "admin",
      desc: "Remove localização",
    },
    {
      method: "GET",
      path: "/locations/{id}/devices",
      auth: "admin",
      desc: "Dispositivos da localização",
    },
  ],
  tenants: [
    {
      method: "GET",
      path: "/tenants",
      auth: "super",
      desc: "Lista todos os tenants",
    },
    {
      method: "GET",
      path: "/tenants/{id}",
      auth: "admin",
      desc: "Detalhe do tenant",
    },
    {
      method: "POST",
      path: "/tenants",
      auth: "super",
      desc: "Cria novo tenant",
    },
    {
      method: "PATCH",
      path: "/tenants/{id}",
      auth: "super",
      desc: "Atualiza tenant (plano, status...)",
    },
    {
      method: "DELETE",
      path: "/tenants/{id}",
      auth: "super",
      desc: "Remove tenant",
    },
    {
      method: "GET",
      path: "/tenants/{id}/stats",
      auth: "admin",
      desc: "Estatísticas do tenant",
    },
    {
      method: "GET",
      path: "/health",
      auth: "public",
      desc: "Health check do backend",
    },
  ],
};

const INSTALL = `# 1. Clonar / criar o projeto FastAPI
pip install fastapi uvicorn sqlalchemy asyncpg alembic python-jose passlib python-multipart

# 2. Configurar variável no .env do frontend
echo "VITE_API_URL=http://localhost:8000" >> .env

# 3. Iniciar o backend
uvicorn main:app --reload --port 8000`;

const FASTAPI_MAIN = `# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import devices, campaigns, media, audio, reports, locations, tenants

app = FastAPI(title="PlayWave API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # produção: especifique o domínio do frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(devices.router,    prefix="/devices",    tags=["Devices"])
app.include_router(campaigns.router,  prefix="/campaigns",  tags=["Campaigns"])
app.include_router(media.router,      prefix="/media",      tags=["Media"])
app.include_router(audio.router,      prefix="/audio",      tags=["Audio"])
app.include_router(reports.router,    prefix="/reports",    tags=["Reports"])
app.include_router(locations.router,  prefix="/locations",  tags=["Locations"])
app.include_router(tenants.router,    prefix="/tenants",    tags=["Tenants"])

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}`;

const FASTAPI_DEVICES = `# routers/devices.py (trechos principais)
from fastapi import APIRouter, Header, HTTPException, Depends
from datetime import datetime, timedelta
import secrets, hashlib

router = APIRouter()

# TV solicita código de pareamento
@router.post("/pair-request")
async def pair_request(body: PairRequestSchema):
    code = generate_pairing_code()   # ex: "TV-A3F9"
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    record = await DevicePairingCode.create(
        code=code, expires_at=expires_at, status="waiting",
        os=body.os, player_version=body.player_version,
        screen_resolution=body.screen_resolution
    )
    return record

# TV faz polling até ser pareada
@router.get("/by-code/{code}/status")
async def pairing_status(code: str):
    record = await DevicePairingCode.get(code=code)
    if not record:
        raise HTTPException(404)
    if record.status == "paired":
        return {"status": "paired", "device_token": record.device.device_token}
    if datetime.utcnow() > record.expires_at:
        await record.update(status="expired")
        return {"status": "expired"}
    return {"status": "waiting"}

# Admin confirma pareamento
@router.post("/{device_id}/pair-confirm")
async def pair_confirm(device_id: str, body: PairConfirmSchema):
    token = secrets.token_hex(32)
    device = await Device.update(device_id,
        name=body.name, device_token=token, status="offline",
        paired_at=datetime.utcnow(), device_type=body.device_type)
    return device

# TV heartbeat
@router.post("/{device_id}/heartbeat")
async def heartbeat(device_id: str, body: HeartbeatSchema,
                    x_device_token: str = Header(None)):
    device = await validate_device_token(device_id, x_device_token)
    await device.update(last_seen_at=datetime.utcnow(),
                        status="online", ip_address=body.ip_address)
    return {"ok": True, "is_blocked": device.is_blocked,
            "has_update": device.config_version != body.config_version}`;

const PLAYER_ENV = `# .env (frontend)
VITE_API_URL=https://api.meudominio.com

# A partir desse momento o Player.jsx e todos os módulos
# em /api/* usam automaticamente o FastAPI como backend.
# Base44 continua como fallback se VITE_API_URL não estiver definido.`;

const MODULES = [
  {
    id: "devices",
    label: "Dispositivos",
    icon: Terminal,
    color: "text-blue-500",
  },
  { id: "campaigns", label: "Campanhas", icon: Zap, color: "text-emerald-500" },
  { id: "media", label: "Mídias", icon: FileVideo, color: "text-violet-500" },
  { id: "audio", label: "Áudio", icon: Radio, color: "text-amber-500" },
  {
    id: "reports",
    label: "Relatórios",
    icon: BarChart2,
    color: "text-rose-500",
  },
  {
    id: "locations",
    label: "Localizações",
    icon: MapPin,
    color: "text-teal-500",
  },
  { id: "tenants", label: "Tenants", icon: Shield, color: "text-orange-500" },
];

export default function Quickstart() {
  const [activeModule, setActiveModule] = useState("devices");
  const endpoints = ENDPOINTS[activeModule] || [];

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold">Integração FastAPI</h2>
        <p className="text-sm text-muted-foreground">
          Contrato completo de endpoints e como conectar o backend
        </p>
      </div>

      <Tabs defaultValue="endpoints">
        <TabsList>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="code">Código FastAPI</TabsTrigger>
        </TabsList>

        {/* ── ENDPOINTS ── */}
        <TabsContent value="endpoints" className="space-y-4 mt-4">
          {/* Legenda de autenticação */}
          <div className="flex flex-wrap gap-3 text-xs items-center">
            <span className="text-muted-foreground font-medium">
              Autenticação:
            </span>
            <AuthBadge type="public" />{" "}
            <span className="text-muted-foreground">Sem token</span>
            <AuthBadge type="device" />{" "}
            <span className="text-muted-foreground">Header X-Device-Token</span>
            <AuthBadge type="admin" />{" "}
            <span className="text-muted-foreground">Bearer JWT (admin)</span>
            <AuthBadge type="super" />{" "}
            <span className="text-muted-foreground">Superadmin</span>
          </div>

          {/* Selector de módulo */}
          <div className="flex flex-wrap gap-2">
            {MODULES.map((m) => {
              const Icon = m.icon;
              return (
                <button
                  key={m.id}
                  onClick={() => setActiveModule(m.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                    activeModule === m.id
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-card border-border hover:bg-accent"
                  }`}
                >
                  <Icon
                    className={`w-3.5 h-3.5 ${activeModule === m.id ? "" : m.color}`}
                  />
                  {m.label}
                </button>
              );
            })}
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {endpoints.map((ep, i) => (
                  <div key={i} className="flex items-center gap-4 px-4 py-3">
                    <Method m={ep.method} />
                    <code className="text-xs font-mono text-foreground flex-1">
                      {ep.path}
                    </code>
                    <AuthBadge type={ep.auth} />
                    <span className="text-xs text-muted-foreground hidden md:block min-w-0">
                      {ep.desc}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── SETUP ── */}
        <TabsContent value="setup" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                Instalação
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CopyBlock code={INSTALL} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Server className="w-4 h-4" />
                Variável de Ambiente
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CopyBlock code={PLAYER_ENV} />
              <p className="text-xs text-muted-foreground mt-3">
                Quando{" "}
                <code className="bg-muted px-1 rounded">VITE_API_URL</code> está
                definido, o frontend usa automaticamente o FastAPI para todos os
                módulos. Sem ele, o app continua funcionando via Base44 (modo
                MVP).
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Arquitetura de Fallback</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  {
                    label: "VITE_API_URL definido",
                    desc: "Todas as chamadas vão ao FastAPI",
                    badge: "Produção",
                    color: "bg-emerald-100 text-emerald-700",
                  },
                  {
                    label: "VITE_API_URL ausente",
                    desc: "Base44 SDK é usado como banco de dados",
                    badge: "MVP / Dev",
                    color: "bg-blue-100 text-blue-700",
                  },
                ].map((item, i) => (
                  <div key={i} className="border rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-foreground text-xs">
                        {item.label}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-medium ${item.color}`}
                      >
                        {item.badge}
                      </span>
                    </div>
                    <p className="text-xs">{item.desc}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── CÓDIGO FASTAPI ── */}
        <TabsContent value="code" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Server className="w-4 h-4" />
                main.py — App Principal
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CopyBlock code={FASTAPI_MAIN} lang="python" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Terminal className="w-4 h-4" />
                routers/devices.py — Trechos Chave
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CopyBlock code={FASTAPI_DEVICES} lang="python" />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

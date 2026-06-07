# 🏗️ Arquitetura PlayWave — Electron + Backend

## Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    PLAYWAVE ECOSYSTEM                        │
└─────────────────────────────────────────────────────────────┘

                    DESENVOLVIMENTO LOCAL
                    
    ┌──────────────────────────────────────────────────────┐
    │                    WINDOWS (Dev)                      │
    │                                                       │
    │  ┌──────────────┐      ┌──────────────┐             │
    │  │  Electron    │      │  Dev Server  │             │
    │  │   App        │◄────►│   (Vite)     │             │
    │  │              │      │ :5173/:3000  │             │
    │  └──────────────┘      └──────────────┘             │
    │        │                      │                      │
    │        │                      │                      │
    │        │  VITE_PLAYER_URL     │                      │
    │        │  http://localhost    │  VITE_API_URL        │
    │        │  :3000/player        │  http://localhost    │
    │        │                      │  :8000               │
    │        ▼                      ▼                      │
    │  ┌──────────────────────────────────────┐           │
    │  │       React SPA                      │           │
    │  │  - Login page                        │           │
    │  │  - Dashboard                         │           │
    │  │  - Dispositivos                      │           │
    │  │  - Campanhas                         │           │
    │  │  - Mídia                             │           │
    │  │  - Mock data (lib/mockData.js)       │           │
    │  └──────────────────────────────────────┘           │
    │        │                                             │
    │        │  API Calls                                 │
    │        │  Authorization: Bearer JWT                 │
    │        │                                             │
    │        ▼                                             │
    │  ┌────────────────────────────────────┐            │
    │  │   Docker Network (bridge)          │            │
    │  │                                    │            │
    │  │  ┌──────────────────────────────┐ │            │
    │  │  │  Backend FastAPI :8000       │ │            │
    │  │  │  - /api/auth/login           │ │            │
    │  │  │  - /api/devices              │ │            │
    │  │  │  - /api/campaigns            │ │            │
    │  │  │  - /api/media                │ │            │
    │  │  │  - /health                   │ │            │
    │  │  └──────────────────────────────┘ │            │
    │  │           │                        │            │
    │  │           ▼                        │            │
    │  │  ┌──────────────────────────────┐ │            │
    │  │  │   PostgreSQL :5432           │ │            │
    │  │  │   - Users                    │ │            │
    │  │  │   - Devices                  │ │            │
    │  │  │   - Campaigns                │ │            │
    │  │  │   - Media files              │ │            │
    │  │  │   - Logs                     │ │            │
    │  │  └──────────────────────────────┘ │            │
    │  │                                    │            │
    │  │  ┌──────────────────────────────┐ │            │
    │  │  │   Redis :6379 (Cache)        │ │            │
    │  │  │   - Session cache            │ │            │
    │  │  │   - Token storage            │ │            │
    │  │  └──────────────────────────────┘ │            │
    │  │                                    │            │
    │  │  ┌──────────────────────────────┐ │            │
    │  │  │   RabbitMQ :5672 (Queue)     │ │            │
    │  │  │   - Celery tasks             │ │            │
    │  │  │   - Async processing         │ │            │
    │  │  └──────────────────────────────┘ │            │
    │  │                                    │            │
    │  │  ┌──────────────────────────────┐ │            │
    │  │  │   Nginx :80 (Load Balancer)  │ │            │
    │  │  │   - Proxy /api → backend     │ │            │
    │  │  │   - Proxy /ws → websocket    │ │            │
    │  │  │   - CORS handling            │ │            │
    │  │  └──────────────────────────────┘ │            │
    │  └────────────────────────────────────┘            │
    │                                                     │
    └─────────────────────────────────────────────────────┘


                    AMBIENTE DE PRODUÇÃO

    ┌──────────────────────────────────────────────────┐
    │               Usuários Finais                     │
    │  ┌─────────────────────────────────────────────┐│
    │  │  Desktop (Electron)                         ││
    │  │  - Windows: .exe installer                  ││
    │  │  - Auto-update via GitHub releases          ││
    │  │  - Fullscreen Kiosk mode                    ││
    │  └─────────────────────────────────────────────┘│
    │  ┌─────────────────────────────────────────────┐│
    │  │  Mobile (APK Capacitor)                     ││
    │  │  - Android 9+ (HTTPS + cleartext)           ││
    │  │  - iOS (capacitor:// scheme)                ││
    │  └─────────────────────────────────────────────┘│
    │  ┌─────────────────────────────────────────────┐│
    │  │  Web (PWA)                                  ││
    │  │  - https://playwave.com.br                  ││
    │  │  - Responsive design                        ││
    │  └─────────────────────────────────────────────┘│
    └──────────────────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
    ┌──────────────────────────────────────────────────┐
    │           CloudFlare / AWS / GCP                 │
    │  ┌──────────────────────────────────────────────┐│
    │  │  API Gateway / Load Balancer                 ││
    │  │  - Rate limiting                             ││
    │  │  - DDoS protection                           ││
    │  │  - SSL/TLS termination                       ││
    │  └──────────────────────────────────────────────┘│
    │                    │                             │
    │                    ▼                             │
    │  ┌──────────────────────────────────────────────┐│
    │  │  https://api.playwave.com.br :443            ││
    │  │  - Backend FastAPI (scaled)                  ││
    │  │  - Kubernetes / Docker Swarm                 ││
    │  │  - Multiple replicas                         ││
    │  └──────────────────────────────────────────────┘│
    │                    │                             │
    │        ┌───────────┼───────────┐                │
    │        ▼           ▼           ▼                │
    │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │
    │  │PostgreSQL│ │  Redis   │ │RabbitMQ  │       │
    │  │ (AWS RDS)│ │(Elasticache)(Managed)│       │
    │  └──────────┘ └──────────┘ └──────────┘       │
    │                                                │
    │  ┌──────────────────────────────────────────┐ │
    │  │  S3 / Blob Storage (Mídia)               │ │
    │  │  - Imagens (JPG, PNG, WebP)              │ │
    │  │  - Vídeos (MP4, 1920x1080)               │ │
    │  │  - CDN com cache (CloudFront)            │ │
    │  └──────────────────────────────────────────┘ │
    │                                                │
    │  ┌──────────────────────────────────────────┐ │
    │  │  Monitoring & Logging                    │ │
    │  │  - Sentry (error tracking)               │ │
    │  │  - Datadog (APM)                         │ │
    │  │  - ELK Stack (logs)                      │ │
    │  └──────────────────────────────────────────┘ │
    └──────────────────────────────────────────────────┘
```

---

## Fluxo de Requisição: Login

```
User (Electron/Web)
    │
    │ 1. Enter: admin@playwave.com / password
    │
    ▼
React Login Component
    │
    │ 2. validateForm() + preventDefault
    │
    ▼
AuthContext.login()
    │
    │ 3. fetch('http://localhost:8000/api/auth/login', {
    │     method: 'POST',
    │     body: JSON.stringify({email, password})
    │   })
    │
    ▼
Browser Preflight (OPTIONS)
    │
    │ 4. Nginx recebe OPTIONS
    │    Nginx check ALLOWED_ORIGINS
    │    Se OK: response headers com Access-Control-Allow-*
    │
    ▼
Browser POST
    │
    │ 5. POST /api/auth/login
    │    - Headers: Content-Type: application/json
    │    - Body: {email, password}
    │
    ▼
Nginx Proxy
    │
    │ 6. location /api {
    │      proxy_pass http://backend:8000;
    │    }
    │
    ▼
FastAPI Backend (:8000)
    │
    │ 7. @router.post("/api/auth/login")
    │    def login(credentials: UserLogin, db: Session):
    │      user = db.query(User).filter(...).first()
    │      if verify_password(pwd, user.password_hash):
    │        token = create_access_token({"sub": user.id})
    │        return Token(access_token, user)
    │
    ▼
PostgreSQL Query
    │
    │ 8. SELECT * FROM users WHERE email = 'admin@playwave.com'
    │
    ▼
Response: 200 OK + JWT
    │
    │ 9. {
    │      "access_token": "eyJhbGc...",
    │      "token_type": "bearer",
    │      "user": {id, name, email, role, ...}
    │    }
    │
    ▼
Browser localStorageset()
    │
    │ 10. localStorage.setItem('pw_access_token', token)
    │     localStorage.setItem('pw_user', userObj)
    │
    ▼
React Router
    │
    │ 11. navigate('/dashboard', {replace: true})
    │
    ▼
Dashboard Component
    │
    │ 12. useEffect(() => {
    │       fetch('/api/devices', {
    │         headers: {'Authorization': 'Bearer ' + token}
    │       })
    │     })
    │
    ▼
✓ Autenticado!
```

---

## Componentes & Responsabilidades

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.jsx           ← Form com validação zod
│   │   ├── Dashboard.jsx       ← Gráficos + resumo
│   │   ├── Dispositivos.jsx    ← List + detalhes
│   │   ├── Campanhas.jsx       ← CRUD campanhas
│   │   ├── BibliotecaMidias.jsx ← Upload + preview
│   │   └── ...
│   ├── lib/
│   │   ├── AuthContext.jsx     ← JWT + session
│   │   ├── mockData.js         ← 6 devices, campanhas, etc
│   │   └── hooks/
│   │       └── useAuth.ts      ← login/logout
│   ├── api/
│   │   ├── http.js             ← fetch wrapper
│   │   ├── dispositivos.js     ← GET /devices
│   │   ├── campanhas.js        ← CRUD /campaigns
│   │   ├── midias.js           ← POST /media/upload
│   │   └── ...
│   ├── components/
│   │   ├── ui/                 ← shadcn/ui
│   │   └── ...
│   └── styles/
│       └── globals.css         ← Tailwind
├── electron/
│   ├── main.js                 ← Electron entry
│   ├── preload.js              ← IPC bridge
│   └── dist-electron/          ← Build output
├── .env.example                ← Template
├── .env.local                  ← Dev (NÃO commitar)
├── .env.production             ← Prod (build-time)
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### Backend (FastAPI + SQLAlchemy)
```
backend/
├── api/
│   ├── v1/
│   │   ├── auth.py             ← /api/auth/login
│   │   ├── dispositivos.py     ← /api/devices
│   │   ├── campanhas.py        ← /api/campaigns
│   │   ├── midias.py           ← /api/media
│   │   └── ...
│   └── routes.py               ← Router aggregator
├── core/
│   ├── config.py               ← Env vars
│   ├── database.py             ← SQLAlchemy session
│   ├── security.py             ← JWT, password hash
│   ├── models.py               ← User, Device, Campaign
│   ├── schemas.py              ← Pydantic request/response
│   ├── auth.py                 ← verify_password, etc
│   └── dependencies.py         ← Depends(get_db), Depends(get_current_user)
├── migrations/                 ← Alembic migrations
├── main.py                     ← FastAPI app + startup
├── init_db.py                  ← Seed admin user
├── .env                        ← (NÃO commitar secrets)
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

---

## Fluxo de Dados: Mock → API Real

### Fase 1: Desenvolvimento (Mock)
```javascript
// frontend/src/pages/Dispositivos.jsx
import { mockDevices } from "@/lib/mockData";

export function Dispositivos() {
  const devices = mockDevices;  // ← Mock data
  return <DeviceList data={devices} />;
}
```

### Fase 2: Transição (Fallback)
```javascript
import { mockDevices } from "@/lib/mockData";
import { apiFetch } from "@/api/http";

export function Dispositivos() {
  const [devices, setDevices] = useState(mockDevices);
  
  useEffect(() => {
    apiFetch("/api/devices")
      .then(data => setDevices(data))
      .catch(err => {
        console.warn("API failed, usando mock:", err);
        setDevices(mockDevices);
      });
  }, []);
  
  return <DeviceList data={devices} />;
}
```

### Fase 3: Produção (API Real)
```javascript
import { apiFetch } from "@/api/http";

export function Dispositivos() {
  const [devices, setDevices] = useState([]);
  
  useEffect(() => {
    apiFetch("/api/devices")
      .then(setDevices)
      .catch(err => toast.error(err.message));
  }, []);
  
  return <DeviceList data={devices} />;
}
```

---

## Segurança: JWT + CORS + HTTPS

```
         Client (Electron/Web)
                  │
                  │ 1. login(email, pwd)
                  ▼
          Backend /api/auth/login
                  │
                  │ 2. Verify email/pwd vs bcrypt hash
                  ▼
         IF valid: create_access_token()
                  │
                  │ 3. JWT = header.payload.signature
                  │          (exp: +30min)
                  ▼
          RETURN { access_token, user }
                  │
                  │ 4. Client stores in localStorage
                  ▼
         SEND Authorization: Bearer JWT
                  │
                  │ 5. Backend middleware:
                  │    - Verify signature (SECRET_KEY)
                  │    - Check expiration
                  │    - Extract user_id from payload
                  ▼
              IF valid: Proceed with request
              IF expired: Clear client cache + redirect /login
              IF invalid: 401 Unauthorized
```

### CORS Configuration (docker-compose.yml Nginx)
```nginx
# Permitido fazer requisições para
ALLOWED_ORIGINS=
  http://localhost:5173,      # Dev Vite
  http://localhost:3000,      # Dev Electron
  https://playwave.com.br,    # Prod Web
  https://www.playwave.com.br,# Prod Web (WWW)
  capacitor://localhost       # APK Capacitor
```

---

## Escalabilidade em Produção

```
                    ┌─────────────┐
                    │   Usuários  │
                    └──────┬──────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │      CloudFlare / AWS Shield     │
        │    (DDoS protection, WAF)        │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │   Application Load Balancer      │
        │  (SSL/TLS termination)           │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    ┌────────┐    ┌────────┐    ┌────────┐
    │Backend │    │Backend │    │Backend │
    │Replica │    │Replica │    │Replica │
    │   1    │    │   2    │    │   N    │
    └────────┘    └────────┘    └────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │    AWS RDS PostgreSQL       │
        │  (Primary + Replicas)       │
        └─────────────────────────────┘

        ┌──────────────────────────────┐
        │  Cache Layer                 │
        │  - Redis (session)           │
        │  - Memcached (query cache)   │
        │  - CloudFront (CDN)          │
        └──────────────────────────────┘

        ┌──────────────────────────────┐
        │  Storage                     │
        │  - S3 (media files)          │
        │  - CloudFront (distribution) │
        └──────────────────────────────┘
```

---

## Diagrama de Estado: Autenticação

```
┌──────────────┐
│  Logged Out  │  ← Inicial
└──────┬───────┘
       │ user entra credenciais válidas
       ▼
┌──────────────┐
│  Logging In  │  ← Loading...
└──────┬───────┘
       │ backend retorna token
       ├─ Sucesso? 
       │  ▼
       │ ┌──────────────┐
       │ │ Logged In    │  ← Armazenar JWT
       │ └──────┬───────┘
       │        │
       │        │ Inatividade 30min?
       │        ▼
       │ ┌──────────────┐
       │ │ Session      │  ← Expirou
       │ │ Expired      │
       │ └──────┬───────┘
       │        │ redirect /login
       │        ▼
       │     Logged Out
       │
       └─ Erro (401/403)?
          ▼
       ┌──────────────┐
       │ Auth Error   │  ← Email/pwd incorretos
       └──────┬───────┘
              │ user tenta novamente
              └─► Logged Out
```

---

## Performance Targets

| Métrica | Target | Dev | Prod |
|---------|--------|-----|------|
| **Page Load** | < 3s | Sub-segundo | 1-2s |
| **API Response** | < 200ms | < 100ms | < 200ms (latência) |
| **Login** | < 500ms | 50-100ms | 200-300ms |
| **Device List** | < 1s | < 100ms | < 500ms |
| **Memory** | < 500MB | 150-200MB | 300-400MB |
| **CPU** | < 30% | Low | Average |

---

## Integrações Futuras

```
┌──────────────────────────────────────────┐
│  PlayWave Core                           │
│  ├── Sentry (Error Tracking)             │
│  ├── Datadog (APM + Monitoring)          │
│  ├── LogRocket (Session Replay)          │
│  ├── GitHub Actions (CI/CD)              │
│  ├── Stripe (Pagamento)                  │
│  └── SendGrid (Email)                    │
└──────────────────────────────────────────┘
```

---

**Última atualização**: 2026-06-04  
**Version**: 1.0  
**Owner**: PlayWave Team


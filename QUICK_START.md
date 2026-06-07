# 🚀 PlayWave Electron + Backend — Quick Start

## ✅ Status Atual

| Componente | Status | URL |
|-----------|--------|-----|
| **Backend FastAPI** | ✅ Rodando | http://localhost:8000 |
| **Banco de Dados** | ✅ Saudável | PostgreSQL 5432 |
| **Admin Credentials** | ✅ Configurado | admin@playwave.com |
| **CORS** | ✅ Ativado | http://localhost:3000 |
| **.env Backend** | ✅ Atualizado | URL_HOST, ENVIRONMENT |
| **.env Frontend** | ✅ Atualizado | VITE_API_URL, VITE_PLAYER_URL |

---

## 🎯 Iniciar Tudo em 3 Passos

### ✅ Passo 1: Backend (já está rodando)
```bash
# Docker containers estão UP
docker ps

# Esperado: 5 containers
# - playwave-backend
# - playwave-postgres  
# - playwave-redis
# - playwave-rabbitmq
# - playwave-nginx
```

### ✅ Passo 2: Frontend Dev Server
```bash
cd "c:\Users\Kaik\Documents\VScode\PlayWave\Play-Wave-Aplicativo\frontend"

npm run dev
# Abre em http://localhost:5173
# Login: admin@playwave.com
```

### ✅ Passo 3: Electron App
```bash
# Terminal 1: Servidor Player (porta 3000)
npm run preview -- --port 3000

# Terminal 2: Electron (novo terminal)
cd electron
npm run electron:dev
```

---

## 📱 Teste de Login

### Web (http://localhost:5173)
```
Email: admin@playwave.com
Senha: &2p0Kw45A&lLNX4bM%gpH*cy
```

**Esperado**: Dashboard com 6 dispositivos, campanhas, alertas

### Electron (Standalone)
Mesmas credenciais, conecta direto via http://localhost:3000/player

---

## 🔧 Arquivos Atualizados

### Backend (.env)
```bash
# Novo
URL_HOST=http://localhost:8000
ENVIRONMENT=development

# Existing
DATABASE_URL=postgresql://playwave:Z7xK9mP2qR8nV4wY@localhost:5432/playwave
SECRET_KEY=J8mN3pQ5rT7vW2xZ9kL4sD6fG1hB8cE
ADMIN_INITIAL_EMAIL=admin@playwave.com
ADMIN_INITIAL_PASSWORD=&2p0Kw45A&lLNX4bM%gpH*cy
```

### Frontend (.env.local)
```bash
# Novo
VITE_PLAYER_URL=http://localhost:3000/player

# Existing
VITE_API_URL=http://localhost:8000
```

---

## 📚 Documentação Criada

1. **ELECTRON_SETUP.md** ← Leia primeiro
   - Configuração passo-a-passo
   - Troubleshooting "backend não conectado"
   - CORS e proxies

2. **MOCK_DATA_FEATURES.md**
   - 6 Dispositivos (status, OS, IP)
   - 6 Campanhas (active, draft, ended)
   - 7 Arquivos de mídia
   - 6 Localizações
   - 3 Alertas com severidade

3. **ELECTRON_TESTING.md**
   - Testes unitários
   - Diagnóstico de CORS/conexão
   - Debug console
   - Checklist visual

---

## 💡 Dados Mock Disponíveis

Localização: `frontend/src/lib/mockData.js`

```javascript
import {
  mockDevices,       // 6 TVs, Totens, Web Players
  mockCampaigns,     // Campanha Abril, Promoção, etc
  mockMedia,         // 7 arquivos (IMG, VIDEO)
  mockLocations,     // Recepção, Lojas, Restaurante
  mockAlerts,        // 3 alertas com severidade
  mockViewsPerDay,   // Gráfico 7 dias
  formatFileSize     // Helper (2.4 MB)
} from "@/lib/mockData";
```

**Exemplo de uso:**
```jsx
export default function Dashboard() {
  const alertas = mockAlerts;
  const devicesOnline = mockDevices
    .filter(d => d.status === 'online')
    .length;

  return (
    <div>
      <AlertList data={alertas} />
      <DeviceCount count={devicesOnline} />
    </div>
  );
}
```

---

## 🐛 Se o Electron Mostrar "Backend não conectado"

### Verificação Rápida (1 min)
```bash
# Terminal 1: Testar health
curl http://localhost:8000/health

# Terminal 2: Testar login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"admin@playwave.com",
    "password":"&2p0Kw45A&lLNX4bM%gpH*cy"
  }'
```

### Checklist Interno
- [ ] Backend rodando em porta 8000? → `docker ps`
- [ ] VITE_API_URL configurado? → `cat frontend/.env.local`
- [ ] VITE_PLAYER_URL apontando para 3000? → `cat frontend/.env.local`
- [ ] Variáveis carregadas no Electron? → `Ctrl+Shift+I` → console

### Solução Comum
```bash
# Limpar cache Vite
rm -rf frontend/node_modules/.vite
npm run dev
```

---

## 📊 Estrutura de Produção

```
PRODUÇÃO
├─ Backend
│  └─ https://api.playwave.com.br  (FastAPI)
├─ Frontend Web
│  └─ https://playwave.com.br      (React + Vite)
├─ APK Capacitor
│  └─ capacitor://localhost        (HTTPS obrigatório)
└─ Configuração
   └─ .env.production              (embutido no build)
```

---

## 🎯 Próximas Tarefas

1. **Implementar Features com Mock Data**
   - [ ] Página de Dispositivos
   - [ ] Página de Campanhas
   - [ ] Dashboard com gráficos
   - [ ] Página de Mídia

2. **Migrar para API Real**
   - [ ] Substituir mockDevices por fetch
   - [ ] Implementar useQuery / useFetch
   - [ ] Tratamento de erros

3. **Electron em Produção**
   - [ ] Build .exe para Windows
   - [ ] Auto-update
   - [ ] Instalador NSIS

---

## 🔐 Credenciais de Teste

| Usuário | Email | Senha | Acesso |
|---------|-------|-------|--------|
| Admin | admin@playwave.com | &2p0Kw45A&lLNX4bM%gpH*cy | Full |
| Operator | operador@playwave.com | Troque@456! | Limitado |

---

## 📞 Troubleshooting

### "ECONNREFUSED localhost:8000"
- Backend parou
- Solução: `docker-compose up -d`

### "CORS error"
- VITE_PLAYER_URL não está em ALLOWED_ORIGINS
- Solução: Atualizar `.env` backend e reiniciar Docker

### "Token inválido"
- Token expirou ou corrupto
- Solução: Limpar localStorage + fazer login novamente
  ```javascript
  localStorage.removeItem('pw_access_token');
  location.reload();
  ```

### Electron não carrega
- VITE_PLAYER_URL vazio
- Solução: Certificar que `.env.local` tem a variável
  ```bash
  grep VITE_PLAYER_URL frontend/.env.local
  ```

---

## 📖 Referências

- **Vite Env**: https://vitejs.dev/guide/env-and-mode.html
- **Electron**: https://www.electronjs.org/docs
- **React Hook Form**: https://react-hook-form.com/
- **Tailwind CSS**: https://tailwindcss.com/

---

**Última atualização**: 2026-06-04  
**Status**: ✅ Pronto para começar  
**Próximo passo**: Rodar `npm run dev` + `npm run electron:dev`


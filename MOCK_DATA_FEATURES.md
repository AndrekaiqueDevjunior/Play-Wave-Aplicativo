# Mock Data & Features

Localização: **`frontend/src/lib/mockData.js`**

---

## 📱 Mock Devices (6 Dispositivos)

### 1. TV Recepção Principal
```javascript
{
  id: "1",
  name: "TV Recepção Principal",
  status: "online",
  location: "Recepção",
  group: "Matriz",
  os: "Android TV",
  player_version: "2.4.1",
  ip_address: "192.168.1.101",
  current_campaign: "Campanha Abril",
  storage_used: 2400 MB,
}
```

### 2. TV Sala de Espera
- Status: **online**
- Campanha: Institucional
- OS: Android TV 2.4.1

### 3. Totem Loja 01
- Status: **offline** (último acesso: 08:15)
- OS: **Windows**
- Storage: 5200 MB

### 4. TV Restaurante
- Status: **online**
- Campanha: Cardápio Digital
- Parceiro integrado

### 5. TV Academia
- Status: **error** (inativo há 12h)
- OS: Web Player 2.2.0
- Alert: "offline há 12 horas"

### 6. Painel Externo
- Status: **syncing**
- Localização: Fachada Loja 02
- Filial

---

## 📺 Mock Campaigns (6 Campanhas)

### Status: Active
1. **Campanha Abril**
   - Duração: 01/04 - 30/04
   - Devices: 1, 6
   - Média: 3 (Banner, Slide, Vídeo)
   - Total views: 12.450

2. **Campanha Institucional**
   - Duração: 15/03 - 15/06 (longa duração)
   - Device: 2 (Recepção)
   - Mídia: 1 (Vídeo 60s)
   - Total views: 8.200

3. **Promoção Especial**
   - Duração: 20/04 - 28/04 (fim de semana)
   - Device: 3 (Loja Centro)
   - Horário: 08:00 - 22:00
   - Dias: seg-sab
   - Total views: 3.100

4. **Cardápio Digital**
   - Duração: 01/04 - 31/05
   - Device: 4 (Restaurante)
   - Mídia: 2 (Cardápio Almoço + Jantar)
   - Total views: 5.800

### Status: Draft
5. **Campanha Maio**
   - Agendada: 01/05 - 31/05
   - Nenhum device atribuído ainda
   - Sem views (rascunho)

### Status: Ended
6. **Black Friday 2025**
   - Duração: 20/11 - 30/11 (encerrada)
   - Devices: 1, 3
   - Total views: **45.000** (maior campanha)

---

## 🎬 Mock Media (7 Arquivos)

| ID | Nome | Tipo | Duração | Tamanho | Status |
|----|------|------|---------|---------|--------|
| 1 | Banner Promoção Abril.jpg | image | 10s | 2.4 MB | ✓ available |
| 2 | Vídeo Institucional.mp4 | video | 30s | 15 MB | ✓ available |
| 3 | Slide Produtos.png | image | 8s | 1.8 MB | ✓ available |
| 4 | Apresentação Empresa.mp4 | video | 60s | 35 MB | ✓ available |
| 5 | Oferta Relâmpago.webp | image | 6s | 950 KB | ✓ available |
| 6 | Cardápio Almoço.jpg | image | 12s | 3.2 MB | ✓ available |
| 7 | Cardápio Jantar.jpg | image | 12s | 2.8 MB | ⏳ processing |

### Características
- Todas em 1920x1080 (Full HD)
- Vídeos: MP4 H.264
- Imagens: JPG, PNG, WebP
- URL: Unsplash (publicamente acessível)

---

## 📍 Mock Locations (6 Localizações)

| Localização | Endereço | Devices | Descrição |
|-------------|----------|---------|-----------|
| Recepção | Av. Paulista, 1000 | 1 | Matriz principal |
| Sala de Espera | Av. Paulista, 1000 | 1 | Escritório |
| Loja Centro | Rua Augusta, 500 | 1 | Filial |
| Restaurante | Rua Oscar Freire, 200 | 1 | Parceiro |
| Academia FitMax | Av. Brasil, 3000 | 1 | Parceiro |
| Fachada Loja 02 | Shopping Iguatemi | 1 | Painel externo |

---

## 📊 Mock Analytics

### Views por Dia (7 dias)
```
21/04: 1.820 views
22/04: 2.150 views
23/04: 1.950 views
24/04: 2.400 views ⬆️ (pico)
25/04: 2.100 views
26/04: 2.650 views ⬆️ (pico 2)
27/04: 1.890 views
```

Total: **16.140 views** em 7 dias

---

## 🚨 Mock Alerts (3 Alertas)

### Severity: HIGH 🔴
**ID 1: Dispositivo Offline**
- Mensagem: "TV Academia está offline há 12 horas"
- Device: 5
- Tempo: 10 min atrás

### Severity: MEDIUM 🟡
**ID 2: Campanha Encerrando**
- Mensagem: 'Campanha "Promoção Especial" encerra amanhã'
- Tempo: 30 min atrás

### Severity: LOW 🟢
**ID 3: Mídia Processando**
- Mensagem: 'Mídia "Cardápio Jantar.jpg" ainda processando'
- Tempo: 1h atrás
- File: ID 7 (status: processing)

---

## 🎯 Casos de Uso Cobertos

### Dashboard
- [ ] Exibir alertas (3 severidades)
- [ ] Gráfico de views por dia
- [ ] Resumo de devices online/offline
- [ ] Campanhas ativas

### Dispositivos
- [ ] Listar 6 devices com status
- [ ] Filtrar por status (online, offline, error, syncing)
- [ ] Filtrar por grupo (Matriz, Filiais, Parceiros)
- [ ] Ver IP e versão do player

### Campanhas
- [ ] Listar campanhas com status
- [ ] Filtrar por status (active, draft, ended)
- [ ] Horários de exibição (all_day ou range)
- [ ] Visualizar devices atribuídos

### Mídia
- [ ] Listar arquivos com thumbnails
- [ ] Filtrar por tipo (image, video)
- [ ] Status de processamento (available, processing)
- [ ] Tamanho em MB/GB

### Analytics
- [ ] Gráfico de views por dia
- [ ] Total views por campanha
- [ ] Device com mais views
- [ ] Período de 7 dias

---

## 🔄 Usando Mock Data em Componentes

### Importar
```javascript
import {
  mockDevices,
  mockCampaigns,
  mockMedia,
  mockLocations,
  mockAlerts,
  mockViewsPerDay,
  formatFileSize
} from "@/lib/mockData";
```

### Exemplo de Uso
```javascript
export default function Dashboard() {
  const alerts = mockAlerts;
  const devices = mockDevices.filter(d => d.status === 'online').length;

  return (
    <div>
      <AlertList alerts={alerts} />
      <DeviceCount online={devices} />
    </div>
  );
}
```

---

## 📝 Estrutura de Dados

### Device Schema
```typescript
{
  id: string;
  name: string;
  pairing_code: string;
  location: string;
  group: "Matriz" | "Filiais" | "Parceiros";
  status: "online" | "offline" | "error" | "syncing";
  last_connection: ISO8601;
  current_campaign: string;
  ip_address: string;
  player_version: string;
  os: string;
  storage_used: number; // MB
  is_active: boolean;
}
```

### Campaign Schema
```typescript
{
  id: string;
  name: string;
  description: string;
  status: "active" | "draft" | "ended";
  start_date: YYYY-MM-DD;
  end_date: YYYY-MM-DD;
  device_ids: string[];
  media_ids: string[];
  total_views: number;
  schedule_all_day: boolean;
  schedule_start_time?: string; // HH:MM
  schedule_end_time?: string;   // HH:MM
  schedule_days?: string[];
}
```

### Media Schema
```typescript
{
  id: string;
  name: string;
  file_url: string;
  thumbnail_url: string;
  type: "image" | "video" | "audio";
  duration: number; // segundos
  file_size: number; // bytes
  resolution: string; // 1920x1080
  status: "available" | "processing" | "failed";
  tags: string[];
  created_date: YYYY-MM-DD;
}
```

---

## 💡 Features Mockáveis

### Dashboard
- ✅ Alertas (3 tipos com severidade)
- ✅ Gráfico de views (7 dias)
- ✅ Card de devices online/offline
- ✅ Campanhas ativas
- ✅ Próximas campanhas

### Dispositivos
- ✅ List view com 6 dispositivos
- ✅ Status indicators (online/offline/error/syncing)
- ✅ Grupos (Matriz/Filiais/Parceiros)
- ✅ Detalhes: IP, versão, armazenamento
- ✅ Atividade (último acesso)

### Campanhas
- ✅ List com status badges
- ✅ Agendamento (all-day vs horário)
- ✅ Dias da semana
- ✅ Associação com devices
- ✅ Timeline visual (início/fim)

### Mídia
- ✅ Grid ou list de arquivos
- ✅ Thumbnails
- ✅ Resolução (1920x1080)
- ✅ Tipo de arquivo
- ✅ Status de processamento
- ✅ Tags

### Localizações
- ✅ Mapa com 6 locais
- ✅ Contagem de devices por local
- ✅ Endereço completo
- ✅ Descrição

---

## 🎨 Tailwind Classes Para Status

```javascript
// status colors
const statusColors = {
  online: "bg-green-100 text-green-800", // ✅
  offline: "bg-red-100 text-red-800",     // ❌
  error: "bg-red-100 text-red-800",       // ⚠️
  syncing: "bg-blue-100 text-blue-800",   // 🔄
};

const campaignStatus = {
  active: "bg-green-100 text-green-800",
  draft: "bg-yellow-100 text-yellow-800",
  ended: "bg-gray-100 text-gray-800",
};

const mediaStatus = {
  available: "bg-green-100 text-green-800",
  processing: "bg-yellow-100 text-yellow-800",
  failed: "bg-red-100 text-red-800",
};
```

---

## 🚀 Próximas Etapas

1. **Converter Mock para Llamadas Real**
   - Remover import de mockData
   - Usar hooks de API (useFetch, useQuery)

2. **Manter Mock Mode**
   - Flag de desenvolvimento
   - Fallback se API falhar

3. **Integração com Backend**
   - Usar mesmas estruturas de dados
   - Validar com Pydantic schemas


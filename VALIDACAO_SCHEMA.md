# Validação de Consistência: Backend vs Frontend

Relatório de inconsistências entre JSON schemas, Models do backend e uso no frontend.

---

## Inconsistências Encontradas

### 1. Device - Campo `os`

**JSON Schema** (`entidade/device.json`):
```json
"os": {
  "type": "string",
  "enum": ["Android TV", "Windows", "Web Player", "iOS", "Linux"]
}
```

**Backend Model** (`backend/models.py`):
```python
os = Column(String(50), nullable=True)
```
- ❌ **Problema**: Backend não tem enum, apenas String(50)

**Frontend** (`DeviceFormModal.jsx`):
```javascript
const DEVICE_TYPES = [...] // OK
<SelectItem value="Web Player">Web Player</SelectItem>
<SelectItem value="Android TV">Android TV</SelectItem>
<SelectItem value="Windows">Windows</SelectItem>
<SelectItem value="iOS">iOS</SelectItem>
<SelectItem value="Linux">Linux</SelectItem>
```
- ✅ **OK**: Frontend usa os mesmos valores do JSON schema

**Recomendação**: Adicionar enum no backend model:
```python
class DeviceOS(str, enum.Enum):
    ANDROID_TV = "Android TV"
    WINDOWS = "Windows"
    WEB_PLAYER = "Web Player"
    IOS = "iOS"
    LINUX = "Linux"

os = Column(SQLEnum(DeviceOS), nullable=True)
```

---

### 2. Tenant - Campo `document`

**JSON Schema** (`entidade/Tenant.json`):
```json
{
  "name": "Tenant",
  "properties": {
    "name": { "type": "string" },
    "plan": { ... },
    "is_active": { ... },
    "max_devices": { ... },
    "contact_email": { ... },
    "notes": { ... }
  }
}
```
- ❌ **Problema**: Não tem campo `document`

**Backend Model** (`backend/models.py`):
```python
class Tenant(Base):
    ...
    document = Column(String(50), nullable=True)  # CNPJ, CPF, etc.
```
- ❌ **Problema**: Tem campo `document` que não existe no JSON schema

**Recomendação**: 
- Opção A: Remover `document` do backend se não for necessário
- Opção B: Adicionar `document` ao JSON schema:
```json
"document": {
  "type": "string",
  "description": "CNPJ, CPF, etc."
}
```

---

## Entidades Verificadas (Consistentes)

### Campaign
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes
- ✅ Frontend: Usa base44.entities.Campaign

### Media
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes
- ✅ Frontend: Usa base44.entities.Media

### Location
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes
- ✅ Frontend: Usa base44.entities.Location

### AudioTrack
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes
- ✅ Frontend: Usa base44.entities.AudioTrack

### AudioPlaylist
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes
- ✅ Frontend: Usa base44.entities.AudioPlaylist

### DevicePairingCode
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes

### DeviceSession
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes

### DeviceEvent
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes

### PlaybackLog
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes

### ViewReport
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes

### UserLog
- ✅ JSON schema: Todos os campos presentes
- ✅ Backend model: Todos os campos consistentes

---

## Resumo

| Entidade | Status | Problema |
|----------|--------|----------|
| Tenant | ⚠️ Inconsistente | Campo `document` no backend não existe no JSON schema |
| Device | ⚠️ Inconsistente | Campo `os` no backend não tem enum |
| Campaign | ✅ Consistente | - |
| Media | ✅ Consistente | - |
| Location | ✅ Consistente | - |
| AudioTrack | ✅ Consistente | - |
| AudioPlaylist | ✅ Consistente | - |
| DevicePairingCode | ✅ Consistente | - |
| DeviceSession | ✅ Consistente | - |
| DeviceEvent | ✅ Consistente | - |
| PlaybackLog | ✅ Consistente | - |
| ViewReport | ✅ Consistente | - |
| UserLog | ✅ Consistente | - |

---

## Ações Recomendadas

1. **Adicionar enum DeviceOS ao backend model** para validar o campo `os`
2. **Decidir sobre o campo `document` em Tenant**:
   - Se necessário: adicionar ao JSON schema
   - Se não necessário: remover do backend model

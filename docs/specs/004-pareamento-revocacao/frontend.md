# SPEC 004 — Frontend Gerenciador

## Arquivos afetados

- `frontend/src/pages/DispositivoDetalhe.jsx` — modal de confirmacao, botoes, timeline.
- `frontend/src/api/dispositivos.js` — novas funcoes.
- `frontend/src/components/devices/RegenerateCodeDialog.jsx` (novo).
- `frontend/src/components/devices/ForceRepairDialog.jsx` (novo).
- `frontend/src/components/devices/PairingEventTimeline.jsx` (novo).

## API client — `dispositivos.js`

Adicionar:

```javascript
export async function buscarSessoesAtivas(deviceId) {
  const { data } = await http.get(`/devices/${deviceId}/sessions/active`);
  return data;
}

export async function regenerarCodigoPareamento(deviceId, reason) {
  const { data } = await http.post(
    `/devices/${deviceId}/pairing-code/regenerate`,
    reason ? { reason } : {},
  );
  return data;
}

export async function forcarReparamento(deviceId, reason) {
  const { data } = await http.post(
    `/devices/${deviceId}/force-repair`,
    reason ? { reason } : {},
  );
  return data;
}

export async function listarEventosPareamento(deviceId, params = {}) {
  const { data } = await http.get(`/devices/${deviceId}/pairing-events`, { params });
  return data;
}
```

## DispositivoDetalhe.jsx — secao de pareamento

Reorganizar em card com 3 acoes:

```
+---------------------------------------------------------------+
| Pareamento                                                    |
|---------------------------------------------------------------|
| Codigo atual:  TV-X7K2          [Copiar] [Mostrar QR]         |
| Pareado em:    2026-05-10 14:30                               |
| Token version: 2 (regenerado em 2026-05-22 10:00)             |
| Sessoes ativas: 1                                             |
|---------------------------------------------------------------|
| [ Forcar reparamento ]   [ Regenerar codigo ]   [ Bloquear ]  |
+---------------------------------------------------------------+
```

### "Regenerar codigo" → `RegenerateCodeDialog`

Modal:

```
Atencao — Regenerar codigo de pareamento

Esta acao vai:
  • Gerar um novo codigo de pareamento (visivel aos operadores).
  • Revogar TODOS os players atualmente conectados a este dispositivo.
  • Forcar reparamento manual em cada TV.

Sessoes ativas que serao desconectadas: 1
  - 192.168.1.100 (ultima atividade ha 5s)

Motivo (opcional, para auditoria):
  [_____________________________________________]

Tem certeza?

  [Cancelar]   [Sim, regenerar e revogar]
```

Apos confirmar:

- Toast: "Codigo regenerado. 1 player foi desconectado."
- Atualiza UI com novo codigo.
- Invalida query de sessions/events.

### "Forcar reparamento" → `ForceRepairDialog`

Modal:

```
Forcar reparamento (mantem o codigo)

Esta acao vai:
  • Revogar todos os players atualmente conectados.
  • Manter o codigo de pareamento atual: TV-X7K2.
  • Operadores podem reparear com o MESMO codigo.

Use isso quando suspeitar de player clonado/roubado sem
querer reconfigurar todas as TVs autorizadas.

Motivo (opcional, recomendado):
  [_____________________________________________]

  [Cancelar]   [Sim, forcar reparamento]
```

Apos confirmar:

- Toast: "Reparamento forcado. 1 player foi desconectado. Codigo permanece o mesmo."
- Mantem codigo na UI.
- Invalida query de sessions/events.

## PairingEventTimeline.jsx (novo)

Componente que renderiza historico de eventos de pareamento.

```javascript
const EVENT_LABELS = {
  paired: { label: "Pareado", color: "green", icon: "Link" },
  re_paired: { label: "Re-pareado", color: "blue", icon: "Link" },
  code_regenerated: { label: "Codigo regenerado", color: "amber", icon: "RefreshCw" },
  force_repair: { label: "Reparamento forcado", color: "amber", icon: "AlertTriangle" },
  token_revoked: { label: "Token revogado", color: "gray", icon: "ShieldOff" },
  code_expired: { label: "Codigo expirou", color: "gray", icon: "Clock" },
  device_blocked: { label: "Bloqueado", color: "red", icon: "Ban" },
  device_unblocked: { label: "Desbloqueado", color: "green", icon: "ShieldCheck" },
};

export function PairingEventTimeline({ deviceId }) {
  const { data } = useQuery(["pairing-events", deviceId], () =>
    listarEventosPareamento(deviceId, { limit: 20 })
  );

  return (
    <div className="space-y-3">
      {data?.items.map((ev) => (
        <div key={ev.id} className="flex gap-3 p-3 border rounded-lg">
          <Icon name={EVENT_LABELS[ev.event_type]?.icon} className={`text-${EVENT_LABELS[ev.event_type]?.color}-500`} />
          <div className="flex-1">
            <div className="font-medium">{EVENT_LABELS[ev.event_type]?.label}</div>
            <div className="text-sm text-gray-500">
              {ev.requested_by?.name && `por ${ev.requested_by.name} · `}
              {formatRelative(ev.created_at)}
            </div>
            {ev.reason && <div className="text-sm mt-1 italic">"{ev.reason}"</div>}
            {ev.previous_pairing_code && ev.new_pairing_code && (
              <div className="text-xs mt-2 font-mono">
                {ev.previous_pairing_code} → {ev.new_pairing_code}
              </div>
            )}
            {ev.metadata?.revoked_sessions_count > 0 && (
              <div className="text-xs mt-1 text-amber-600">
                {ev.metadata.revoked_sessions_count} sessao(oes) revogada(s)
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
```

## DispositivoDetalhe.jsx — adicionar timeline

Em aba ou secao colapsavel "Historico de pareamento":

```javascript
<Section title="Historico de pareamento">
  <PairingEventTimeline deviceId={device.id} />
</Section>
```

## React Query keys

- `["device", deviceId]` — invalida apos regenerate/force-repair.
- `["device-sessions-active", deviceId]` — invalida apos regenerate/force-repair.
- `["pairing-events", deviceId]` — invalida apos regenerate/force-repair.

## Toasts e feedback

- Sucesso: usar `toast.success` do sistema atual.
- Erro: capturar `error_code` se vier do backend; senao mostrar `detail`.

## Acessibilidade

- Modais com `role="alertdialog"`.
- Botoes destrutivos com `aria-label` claro.
- Foco automatico no campo de motivo em ambos os dialogs.
- Tecla ESC fecha modal sem confirmar.

## Estado de loading

- Botoes desabilitados durante mutation.
- Indicador "Revogando sessoes..." durante chamada.

## Mensagem de impacto pre-acao

Antes de confirmar, sempre mostrar contagem de `sessions_active` chamando `buscarSessoesAtivas` no mount do modal. Se erro ao buscar, mostrar "Nao foi possivel verificar sessoes ativas, prossiga com cautela."

## Casos de uso operacionais

### Caso 1: Operador troca codigo de uma TV trocada de loja

- Trocar codigo gera novo codigo visivel.
- Player antigo expulso.
- Operador anota novo codigo e configura nova TV.

### Caso 2: Suspeita de player clonado

- "Forcar reparamento" sem trocar codigo.
- TVs autorizadas continuam usando mesmo codigo.
- Player suspeito eh expulso e nao consegue reusar token antigo.
- Auditoria registra motivo da acao.

### Caso 3: Bloqueio total

- "Bloquear dispositivo" (botao existente) impede qualquer player de operar mesmo com token valido.
- Erro 403 `DEVICE_BLOCKED` retorna para o player.
- `forceRepair` dispara e mostra "Dispositivo bloqueado".

# SPEC 003 — Frontend Gerenciador

## Arquivos afetados

- `frontend/src/pages/DispositivoDetalhe.jsx` — botoes e historico de comandos.
- `frontend/src/api/dispositivos.js` — sem mudanca obrigatoria.
- `frontend/src/components/devices/CommandHistoryTimeline.jsx` (novo).

## DispositivoDetalhe.jsx — Botoes de comando

Reorganizar a secao de "Acoes" do dispositivo em 3 grupos com tooltips explicativos.

### Grupo 1 — Operacional (seguros)

| Botao | command_type | Tooltip |
|---|---|---|
| Sincronizar | `sync` | Recarrega playlist sem reiniciar player. |
| Atualizar Playlist | `refresh_playlist` | Mesma coisa que sincronizar (alias). |
| Limpar Cache | `clear_cache` | Limpa IndexedDB local e recarrega. |
| Recarregar Player | `reload_player` | Recarrega a pagina do player. |

### Grupo 2 — Reset do App

| Botao | command_type | Tooltip |
|---|---|---|
| Reiniciar App | `restart_app` | Encerra e reabre o processo do player (Electron) ou recreate da Activity (Android). Web puro: nao suportado. |

Exibir confirmacao simples antes de enviar ("Tem certeza?").

### Grupo 3 — Energia (destrutivos)

| Botao | command_type | Tooltip |
|---|---|---|
| Reiniciar Dispositivo | `restart_device` | Reboot fisico do OS. Windows/Linux com permissao adequada. Android exige Device Owner. |
| Desligar Dispositivo | `shutdown_device` | Desliga fisicamente. Windows/Linux com permissao adequada. Android: bloqueia a tela (limitacao do Android stock). |

Estes botoes devem:

- Ter cor de aviso (vermelho/laranja).
- Pedir confirmacao com modal forte: "Voce esta prestes a desligar o dispositivo X. Esta acao requer alguem fisicamente para liga-lo de volta."
- Mostrar plataforma detectada e se eh suportada.

## DispositivoDetalhe.jsx — Historico de comandos

Substituir lista simples de comandos por componente `CommandHistoryTimeline`.

### Colunas/Info por comando

- Tipo (label amigavel).
- Status atual com cor:
  - `pending` cinza claro
  - `sent` azul claro
  - `received` azul
  - `executing` amarelo
  - `completed` / `executed` verde
  - `failed` vermelho
  - `failed` com `platform_unsupported=true` cinza com badge "Nao suportado"
  - `expired` cinza escuro
  - `cancelled` roxo
- Timestamps de transicao:
  - Solicitado em (`requested_at`)
  - Enviado em (`sent_at`)
  - Recebido em (`received_at`)
  - Iniciado em (`started_at`)
  - Finalizado em (`executed_at`)
  - Expira em (`expires_at`) — destaque se proximo do prazo
- Quem solicitou (`requested_by` — exibir nome do usuario).
- Mensagem de erro com `error_code` quando houver.
- Resultado bruto (collapsible — para suporte tecnico ver `result.platform`, `ack_phase`, etc.).
- Acao "Cancelar" para comandos em `pending` ou `sent`.

### Mock visual (ASCII)

```
+---------------------------------------------------------------+
| Reiniciar Dispositivo                          [EXECUTANDO]   |
| Por: admin@playwave.com                                       |
| Solicitado: 10:00:00                                          |
| Enviado:    10:00:03 (3s)                                     |
| Recebido:   10:00:12 (12s)                                    |
| Iniciado:   10:00:13 (13s)                                    |
| Expira em:  10:10:00 (em 9min 47s)                            |
| Plataforma: electron-linux                                    |
| [Ver detalhes] [Cancelar]                                     |
+---------------------------------------------------------------+

+---------------------------------------------------------------+
| Desligar Dispositivo                       [NAO SUPORTADO]    |
| Por: admin@playwave.com                                       |
| Solicitado: 09:50:00                                          |
| Falhou em:  09:50:11                                          |
| Plataforma: web                                               |
| Erro: BROWSER_ENVIRONMENT — shutdown nao suportado no browser |
+---------------------------------------------------------------+
```

## CommandHistoryTimeline.jsx (novo)

Componente reutilizavel. Props:

```
{
  commands: Array<Command>,
  onCancel?: (commandId) => Promise<void>,
}
```

Renderiza cards com info acima. Internamente usa labels/cores de uma tabela helper.

Helper de label (sugerido em `frontend/src/utils/deviceCommands.js`):

```
export const COMMAND_LABELS = {
  sync: "Sincronizar",
  refresh_playlist: "Atualizar Playlist",
  clear_cache: "Limpar Cache",
  reload_player: "Recarregar Player",
  restart_app: "Reiniciar App",
  restart_device: "Reiniciar Dispositivo",
  shutdown_device: "Desligar Dispositivo",
  set_volume: "Ajustar Volume",
  mute: "Silenciar",
  unmute: "Ativar Som",
  take_screenshot: "Capturar Tela",
};

export const STATUS_LABELS = {
  pending: { label: "Aguardando envio", color: "gray-400" },
  sent: { label: "Enviado", color: "blue-300" },
  received: { label: "Recebido", color: "blue-500" },
  executing: { label: "Executando", color: "amber-500" },
  completed: { label: "Concluido", color: "green-500" },
  executed: { label: "Concluido", color: "green-500" },
  failed: { label: "Falhou", color: "red-500" },
  expired: { label: "Expirou", color: "gray-600" },
  cancelled: { label: "Cancelado", color: "purple-500" },
};

export function statusFor(command) {
  if (command.status === "failed" && command.result?.platform_unsupported) {
    return { label: "Nao suportado", color: "gray-500" };
  }
  return STATUS_LABELS[command.status] || { label: command.status, color: "gray-400" };
}
```

## Modal de confirmacao destrutiva

Componente sugerido: `DestructiveCommandConfirmDialog`.

Conteudo:

- Titulo: "Atencao — operacao fisica no dispositivo"
- Texto: "Voce esta prestes a [Desligar/Reiniciar] o dispositivo [Nome]. Esta operacao [desliga/reinicia] fisicamente o dispositivo. Voce ou alguem proximo precisara [liga-lo de volta/aguardar a inicializacao]."
- Linha tecnica: "Plataforma detectada: [electron-linux]. Suporte ao comando: [Sim/Limitado/Nao]."
- Botoes: "Cancelar" / "Confirmar [Desligar/Reiniciar]" (vermelho).

## API client — `dispositivos.js`

Funcoes existentes ja cobrem tudo. Nenhuma nova funcao necessaria.

Opcional: aceitar `expires_in_seconds` em `enviarComando`:

```
export async function enviarComando(deviceId, command, payload = {}, expiresInSeconds = null) {
  return apiClient.post(`/devices/${deviceId}/command`, {
    command_type: command,
    payload,
    ...(expiresInSeconds ? { expires_in_seconds: expiresInSeconds } : {}),
  });
}
```

## Acessibilidade

- Botoes destrutivos com `aria-label` explicito.
- Modal de confirmacao com `role="alertdialog"` e foco automatico no botao "Cancelar".

## Estados de loading/error

- Botao desabilita durante envio.
- Toast de sucesso ao criar comando.
- Toast de erro com mensagem do backend se 4xx/5xx.
- Lista de comandos auto-refresh a cada 5s (React Query `refetchInterval`).

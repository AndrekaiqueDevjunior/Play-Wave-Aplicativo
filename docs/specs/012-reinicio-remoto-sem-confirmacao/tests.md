# SPEC 012 — Tests

Status: aguardando SPEC 011

## Testes manuais obrigatorios

### TM012-01 — Restart remoto com player online

Pre-condicao:

- SPEC 011 validada.
- Player online e pareado.
- Campanha ou playlist ativa.

Passos:

1. No gerenciador, enviar comando de reiniciar player.
2. Verificar que nenhum prompt aparece no player.
3. Verificar que o app reinicia.
4. Verificar que o player volta para a campanha/playlist.
5. Verificar status final do comando.

Resultado esperado:

- Comando finaliza com sucesso.
- Player volta sozinho.

### TM012-02 — Restart sem campanha visual

Pre-condicao:

- Player com radio/campanha sem midia visual, se aplicavel.

Resultado esperado:

- Player reinicia e volta ao estado operacional anterior.

### TM012-03 — Falha de plataforma

Pre-condicao:

- Rodar player em ambiente web sem bridge nativo.

Resultado esperado:

- Comando falha com erro claro `PLATFORM_UNSUPPORTED` ou equivalente.
- Gerenciador mostra falha, nao sucesso falso.

### TM012-04 — Comando duplicado

Passos:

1. Enviar restart.
2. Enviar o mesmo comando ou simular retry.

Resultado esperado:

- Nao entra em loop infinito.
- Status final e previsivel.

## Testes automatizados sugeridos

- Unitario para handler de `restart_app` em `commands.js`.
- Unitario para `commandPoller` confirmar `received` e `started` antes da execucao.
- Unitario para plataforma sem bridge retornar `platform_unsupported`.
- Teste backend para comando expirado.
- Teste backend para ACK de sucesso/falha.

## Evidencias de teste

Preencher apos execucao:

- Ambiente:
- Build/commit:
- Data:
- Resultado:
- Observacoes:


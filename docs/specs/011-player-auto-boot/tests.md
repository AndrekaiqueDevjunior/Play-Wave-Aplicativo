# SPEC 011 — Tests

Status: plano inicial com verificacao sintatica

## Testes manuais obrigatorios

### TM011-01 — Boot com sessao valida

Pre-condicao:

- Player ja pareado.
- Storage local contem sessao valida.
- Backend online.

Passos:

1. Fechar player.
2. Abrir player novamente.
3. Verificar se nao aparece modal de escolha.
4. Verificar se entra no modo player.
5. Verificar se inicia reproducao.
6. Verificar heartbeat/last_seen no backend ou gerenciador.

Resultado esperado:

- Player inicia sem clique humano.
- Log `PLAYER_AUTO_BOOT_SUCCESS`.

### TM011-02 — Boot offline com cache valido

Pre-condicao:

- Player ja sincronizou ao menos uma vez.
- Cache local valido.

Passos:

1. Derrubar rede.
2. Abrir player.
3. Verificar se usa ultima configuracao valida.
4. Restaurar rede.
5. Verificar nova tentativa de sync.

Resultado esperado:

- Player nao fica bloqueado.
- Log `PLAYER_AUTO_BOOT_OFFLINE_CACHE_USED`.
- Ao reconectar, sync ocorre sem reload total.

### TM011-03 — Boot com sessao expirada

Pre-condicao:

- Storage local contem sessao expirada/incompleta.
- `device_id` ou `pairing_code` salvo.

Passos:

1. Abrir player.
2. Verificar chamada de revalidacao.
3. Confirmar restauracao de sessao.

Resultado esperado:

- Modal manual nao aparece antes da tentativa de revalidacao.
- Player inicia se backend aceitar.

### TM011-04 — Boot com pareamento revogado

Pre-condicao:

- Backend rejeita sessao por `pairing_invalidated`.

Passos:

1. Abrir player.
2. Verificar resposta do backend.
3. Verificar limpeza de credenciais antigas.
4. Verificar tela de pareamento.

Resultado esperado:

- Player nao continua operando com sessao antiga.
- Log `PLAYER_AUTO_BOOT_PAIRING_REQUIRED`.

### TM011-05 — Boot sem credencial/cache

Pre-condicao:

- Storage limpo.
- Nenhum pairing code salvo.

Passos:

1. Abrir player.

Resultado esperado:

- Tela de pareamento aparece.
- Nenhum erro silencioso ou tela branca.

## Testes automatizados sugeridos

- Unitario para decisao de boot com sessao valida.
- Unitario para decisao de boot com cache offline valido.
- Unitario para decisao de boot com pareamento revogado.
- Unitario para nao apagar cache valido em erro de rede.
- Integracao do endpoint de heartbeat, se existir suite backend.

## Evidencias de teste

Preencher apos execucao:

- Ambiente: local
- Build/commit: worktree atual
- Data: 2026-06-15
- Resultado: `node --check frontend/electron/main.js` executado com sucesso.
- Observacoes: ainda falta teste E2E abrindo o Electron em modo kiosk/producao.

# Fila de SPECs Criticas — Player, Radio, Windows, Midias e Usuarios

Data: 2026-06-15
Origem: `2026-06-correcoes-player-radio-windows.md`

## Regra principal

As SPECs abaixo devem ser trabalhadas em sequencia. A proxima SPEC so entra em implementacao quando a anterior estiver concluida de ponta a ponta:

- diagnostico do estado atual preenchido;
- arquivos impactados registrados;
- implementacao concluida;
- testes automatizados ou manuais executados;
- criterios de aceite validados;
- riscos e pendencias documentados.

## Fila

| Ordem | SPEC | Pasta | Status |
|---:|---|---|---|
| 1 | SPEC 011 — Player Auto Boot | `docs/specs/011-player-auto-boot/` | concluida — 11/11 testes passando |
| 2 | SPEC 012 — Reinicio Remoto sem Confirmacao | `docs/specs/012-reinicio-remoto-sem-confirmacao/` | concluida — 12/12 testes passando (deploy backend pendente) |
| 3 | SPEC 013 — Spot da Radio sem Sobreposicao | `docs/specs/013-spot-radio-sem-sobreposicao/` | concluida — 29/29 testes unitarios passando (teste manual em hardware pendente) |
| 4 | SPEC 014 — Video Estavel no Player | `docs/specs/014-video-estavel-no-player/` | concluida — 7/7 testes novos + 68/68 relacionados passando (validacao em hardware pendente) |
| 5 | SPEC 015 — Minimizar Windows sem Cortar Conteudo | `docs/specs/015-minimizar-windows-sem-cortar-conteudo/` | concluida — 79/79 testes frontend passando (backend validado por sintaxe; deploy/migration e hardware pendentes) |
| 6 | SPEC 016 — Faixas de Audio Arquivar/Excluir | `docs/specs/016-faixas-audio-arquivar-excluir/` | concluida — 170/173 testes frontend sem regressao; backend validado por sintaxe (deploy/migration pendente) |
| 7 | SPEC 017 — Playlist Sonora Arquivar/Excluir | `docs/specs/017-playlist-sonora-arquivar-excluir/` | concluida — 170/173 testes frontend sem regressao; backend validado por sintaxe (deploy/migration pendente) |
| 8 | SPEC 018 — Midias com Exclusao em Massa | `docs/specs/018-midias-exclusao-em-massa/` | concluida — 170/173 testes frontend sem regressao; backend validado por sintaxe (deploy/migration pendente) |
| 9 | SPEC 019 — Usuarios com Senha/Convite | `docs/specs/019-usuarios-senha-convite/` | concluida — 170/173 testes frontend sem regressao; backend validado por revisao manual (execucao automatizada bloqueada por ambiente sem fastapi e falha intermitente de ferramenta; deploy/migration e SMTP real pendentes) |
| 10 | SPEC 020 — Padrao Arquivamento vs Exclusao | a criar apos SPEC 019 | aguardando |

## Politica de abertura de SPEC

Cada SPEC deve ser criada apenas quando for a proxima da fila, exceto se for necessario antecipar diagnostico de dependencia compartilhada.

Diagnostico antecipado permitido:

- SPEC 011 e SPEC 012 podem compartilhar auditoria de sessao, comandos, storage e heartbeat.
- SPEC 013 e SPEC 014 podem compartilhar auditoria do motor de audio/video do player.
- SPEC 016, SPEC 017, SPEC 018 e SPEC 020 podem compartilhar auditoria de arquivamento/exclusao.

Mesmo quando houver diagnostico compartilhado, a implementacao deve fechar uma SPEC por vez.

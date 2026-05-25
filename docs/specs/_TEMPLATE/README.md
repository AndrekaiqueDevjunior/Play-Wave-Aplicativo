# Template de SPEC

Use esta pasta como ponto de partida para criar uma nova SPEC do PlayWave.

## Como usar

```bash
cp -r docs/specs/_TEMPLATE docs/specs/NNN-nome-curto-da-spec
```

Onde:

- `NNN` eh o proximo numero sequencial (verifique `ls docs/specs/` antes).
- `nome-curto-da-spec` eh um slug em kebab-case que descreve o escopo (ex: `007-upload-multiplo-audio`).

## Quais arquivos preencher

Cada SPEC contem ate 8 arquivos. **Nem todos sao obrigatorios** — remova os que nao se aplicam.

| Arquivo | Quando incluir |
|---|---|
| `requirements.md` | **Sempre.** Objetivo, contexto, escopo, RFs numerados. |
| `design.md` | **Sempre.** Arquitetura, fluxos, decisoes tecnicas. |
| `database.md` | Quando ha migracao ou nova tabela. |
| `api-contract.md` | Quando ha endpoint novo ou alterado. |
| `frontend.md` | Quando ha mudanca de UI admin. |
| `player.md` | Quando ha mudanca no player (web/Electron/Capacitor). |
| `tasks.md` | **Sempre.** Backlog executavel com checkboxes. |
| `tests.md` | **Sempre.** Plano de testes backend/frontend/E2E. |

## Convencoes

### Nomeacao de RFs

Prefixo: `RF{NNN}-{XX}` onde `NNN` eh o numero da spec e `XX` eh sequencial.

Exemplo: SPEC 007 → `RF007-01`, `RF007-02`, etc.

### Status em tasks.md

- `[ ]` pendente
- `[~]` parcial / em andamento
- `[x]` concluido
- `[!]` bloqueado ou aguardando decisao

### Compatibilidade

Toda SPEC que altera contrato com player ou banco deve incluir:

- **Decisoes de compatibilidade** em requirements.md (como dados existentes sao tratados).
- **Compatibilidade** em api-contract.md (como clientes antigos continuam funcionando).
- **Backfill** em database.md (se aplicavel).
- **Compat-period** em tasks.md (rollout em fases quando necessario).

### Referencias a codigo

Usar caminhos relativos a raiz do projeto: `frontend/src/pages/Player.jsx:123`.

### Migrations

Nome de arquivo: `2026XXXX_descricao_curta.py` em `backend/alembic/versions/`.

## Antes de submeter

Checklist de qualidade (de `SPEC DRIVEN DEVELOPMENT/tasks.md`):

- [ ] Requisitos escritos em `requirements.md`.
- [ ] Design tecnico escrito em `design.md`.
- [ ] Tasks quebradas em backend/frontend/player/testes.
- [ ] Migration criada quando houver banco.
- [ ] Compatibilidade com dados existentes avaliada.
- [ ] Endpoint documentado em `api-contract.md`.
- [ ] Frontend sem mock/localStorage para funcionalidade real.
- [ ] Player atualizado quando contrato muda.
- [ ] Cache/invalidacao avaliados.
- [ ] Auditoria avaliada.
- [ ] Testes ou plano manual registrado em `tests.md`.

## Apos a SPEC ser implementada

1. Atualizar `SPEC DRIVEN DEVELOPMENT/tasks.md` referenciando a spec e seu status.
2. Marcar tasks como `[x]` em `tasks.md` da spec conforme finaliza.
3. Manter `tests.md` atualizado com casos descobertos durante implementacao.

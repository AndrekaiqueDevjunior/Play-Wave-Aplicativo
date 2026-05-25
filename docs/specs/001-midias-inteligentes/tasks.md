# SPEC 001 — Tasks

## Fase 0 — Analise

- [x] Mapear arquivos backend relacionados a midia.
- [x] Mapear arquivos frontend relacionados a midia.
- [x] Mapear arquivos do player relacionados a sync/reproducao.
- [x] Mapear endpoints existentes.
- [x] Mapear models e schemas existentes.
- [x] Identificar campos existentes e faltantes.
- [x] Identificar riscos de compatibilidade com campanhas.

## Fase 1 — Banco e Models

- [x] Confirmar migration `media_metadata_versions` no ambiente alvo.
- [x] Adicionar/validar `media.duration_seconds`.
- [x] Adicionar/validar `media.display_duration_seconds`.
- [x] Adicionar/validar `media.starts_at`.
- [x] Adicionar/validar `media.ends_at`.
- [x] Adicionar/validar `media.file_hash`.
- [x] Adicionar/validar `media.file_version`.
- [x] Adicionar/validar `media.is_active`.
- [x] Adicionar/validar `media.extra_metadata`.
- [x] Criar/validar tabela `media_versions`.
- [ ] Planejar backfill para midias antigas.

## Fase 2 — Backend de Upload

- [x] Validar MIME/extensao por tipo.
- [x] Validar tamanho maximo.
- [x] Salvar arquivo em `uploads/media`.
- [x] Calcular SHA-256.
- [x] Detectar duracao de video com `ffprobe`.
- [x] Detectar duracao de audio com `ffprobe`.
- [x] Salvar `duration_seconds`.
- [x] Salvar `display_duration_seconds`.
- [x] Manter compatibilidade com `duration`.
- [x] Registrar metadata extra.
- [x] Criar primeira versao em `media_versions`.

## Fase 3 — Periodo e Status

- [x] Validar `ends_at >= starts_at`.
- [x] Criar helper de disponibilidade calculada.
- [x] Retornar `availability_status` em `MediaResponse`.
- [x] Filtrar midias expiradas/agendadas no payload do player.
- [x] Mostrar status no frontend.

## Fase 4 — Substituicao de Arquivo

- [x] Implementar/validar `POST /media/{id}/replace-file`.
- [x] Garantir que `media_id` nao muda.
- [x] Garantir que campanhas nao perdem vinculo.
- [x] Recalcular hash/duracao/tamanho/mime.
- [x] Incrementar `file_version`.
- [x] Marcar versao anterior como nao atual.
- [x] Criar nova linha em `media_versions`.
- [x] Atualizar `config_version` de campanhas afetadas.
- [x] Invalidar cache Redis dos devices afetados.
- [x] Publicar evento SSE de playlist invalidada.

## Fase 5 — Frontend

- [x] Atualizar cliente `frontend/src/api/midias.js`.
- [x] Atualizar formulario de criacao/edicao.
- [x] Mostrar duracao detectada.
- [x] Mostrar duracao customizada opcional.
- [x] Adicionar campos de inicio/fim.
- [x] Adicionar botao "Substituir arquivo".
- [ ] Mostrar aviso de uso em campanhas.
- [x] Mostrar historico de versoes.
- [ ] Melhorar confirmacao de delete em uso.

## Fase 6 — Player

- [x] Atualizar contrato recebido em `Player.jsx`.
- [x] Receber `file_hash`.
- [x] Receber `file_version`.
- [x] Receber `duration_seconds`.
- [x] Receber `display_duration_seconds`.
- [ ] Respeitar `play_until_end`.
- [x] Invalidar cache local se hash/versao mudar.
- [x] Registrar erro de reproducao.
- [x] Pular midia com erro e seguir playlist.

## Fase 7 — Testes

- [ ] Testar upload de video com duracao real.
- [ ] Testar upload de audio com duracao real.
- [ ] Testar imagem com duracao manual.
- [ ] Testar link com duracao manual.
- [ ] Testar `ends_at < starts_at`.
- [ ] Testar midia agendada.
- [ ] Testar midia expirada.
- [ ] Testar substituicao mantendo `media_id`.
- [ ] Testar campanha mantendo vinculo apos substituicao.
- [ ] Testar player recebendo nova versao.
- [ ] Testar cache invalidado apos substituicao.

## Ordem recomendada

1. Validar migration e models.
2. Validar upload com duracao automatica.
3. Validar periodo/status.
4. Validar substituicao/versionamento.
5. Atualizar frontend.
6. Atualizar player/cache.
7. Executar testes manuais e automatizados.

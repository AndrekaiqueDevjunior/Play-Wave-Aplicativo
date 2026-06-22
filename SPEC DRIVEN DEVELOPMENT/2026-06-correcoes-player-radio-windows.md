# SPEC Driven Development — Correções Críticas PlayWave: Player, Rádio, Windows, Mídias e Usuários

## 1. Contexto

Cliente reportou falhas críticas no uso real do PlayWave em ambiente de loja/TV:

* O app/player não inicializa automaticamente sem intervenção humana.
* Reinício remoto pelo gerenciador exige confirmação manual no player.
* Faixas de áudio e playlists sonoras não são excluídas de verdade ou continuam aparecendo após arquivamento.
* Criação de usuário não permite definir senha nem envia acesso por e-mail.
* Spot da rádio entra por cima da música, misturando som.
* Função de minimizar tela no Windows está funcionando, mas entra no meio do conteúdo.
* Vídeos no player ficam travando/picotando, mesmo rodando normalmente no gerenciador.
* Exclusão de mídias precisa permitir seleção em massa, não apenas item por item.

Este SPEC deve guiar uma implementação orientada por comportamento esperado, testes e critérios de aceite.

---

# 2. Objetivo Geral

Garantir que o PlayWave funcione em modo operacional real de loja/TV, com player autônomo, comandos remotos sem intervenção manual, rádio/spot sem sobreposição indevida, gerenciamento correto de mídias/áudios/usuários e reprodução de vídeo estável no player.

---

# 3. Fora de Escopo

Este SPEC não cobre:

* Redesign completo do painel administrativo.
* Nova arquitetura total do player.
* Troca obrigatória de tecnologia do frontend/backend.
* Refatoração visual ampla.
* Novos relatórios comerciais.
* Mudança de regra de negócio de campanhas que não esteja ligada aos problemas descritos.

---

# 4. Prioridade dos Problemas

## P0 — Crítico / Bloqueia uso em loja

1. Player não inicia automaticamente.
2. Reinício remoto exige confirmação manual.
3. Spot mistura com música da rádio.
4. Vídeos travam/picotam no player.
5. Minimizar no Windows entra no meio do conteúdo.

## P1 — Importante / Prejudica operação

6. Usuário cria login, mas não cria senha nem recebe acesso.
7. Faixas de áudio e playlists sonoras arquivadas continuam aparecendo.
8. Exclusão de mídias sem seleção em massa.

## P2 — Qualidade / Experiência

9. Melhorar feedback visual de comandos remotos.
10. Melhorar logs e diagnóstico do player.

---

# 5. SPEC-001 — Inicialização Automática do Player sem Intervenção

## Problema

O app/player não inicializa automaticamente. Mesmo configurando no Windows, ao abrir ele pede algo como:

* “Manter sessão atual”
* “Começar do zero”

Isso obriga alguém a clicar manualmente no ponto/player para iniciar.

## Comportamento Esperado

Quando o dispositivo liga ou o app abre, o player deve:

1. Restaurar automaticamente a última sessão válida.
2. Entrar direto no modo player/kiosk.
3. Buscar configuração do dispositivo.
4. Sincronizar campanha/playlist atual.
5. Começar a reprodução sem pedir clique humano.
6. Registrar no backend que inicializou.

## Regra de Negócio

O player de exibição não pode depender de decisão manual para iniciar em ambiente de produção.

Se existir sessão anterior válida, usar sessão anterior.

Se não existir sessão válida, usar o código de pareamento salvo localmente.

Se o código de pareamento não existir, exibir tela de pareamento.

## Tarefas Técnicas

### Frontend / Player

* [ ] Localizar fluxo que exibe “manter sessão atual” ou “começar do zero”.
* [ ] Criar modo `AUTO_BOOT=true` para produção/kiosk.
* [ ] Persistir `device_id`, `pairing_code`, `tenant_id`, `player_token` e `last_known_config` em storage local seguro.
* [ ] Ao iniciar, tentar restaurar sessão sem modal.
* [ ] Se sessão for inválida, chamar endpoint de revalidação do dispositivo.
* [ ] Se offline, usar última configuração válida em cache.
* [ ] Exibir modal apenas quando não houver nenhuma sessão/código válido.
* [ ] Adicionar log local: `PLAYER_AUTO_BOOT_STARTED`, `PLAYER_AUTO_BOOT_SUCCESS`, `PLAYER_AUTO_BOOT_FAILED`.

### Backend

* [ ] Validar endpoint para restaurar sessão do device.
* [ ] Garantir que o player consiga se identificar por `device_id` ou `pairing_code`.
* [ ] Criar/validar endpoint de heartbeat inicial.
* [ ] Registrar última inicialização do player em `last_seen_at`.
* [ ] Registrar versão do player, sistema operacional e status de boot.

### Testes

* [ ] Testar player abrindo com sessão válida.
* [ ] Testar player abrindo sem internet.
* [ ] Testar player abrindo com sessão expirada.
* [ ] Testar player abrindo sem pareamento.
* [ ] Testar reinicialização do Windows e abertura automática do player.

## Critérios de Aceite

* [ ] Ao ligar o dispositivo, o player abre sem clique humano.
* [ ] A tela de escolha de sessão não aparece em modo produção.
* [ ] Se houver sessão válida, a reprodução inicia automaticamente.
* [ ] Se estiver offline, o player usa o último cache válido.
* [ ] O backend registra que o player iniciou.
* [ ] O gerenciador mostra status atualizado do dispositivo.

---

# 6. SPEC-002 — Reinício Remoto sem Confirmação Manual

## Problema

No gerenciador, ao enviar comando de reiniciar app/player, o comando chega, mas é necessário acessar fisicamente o player para clicar em “ok” ou confirmar.

## Comportamento Esperado

O comando remoto de reinício deve ser executado sem interação humana.

## Regra de Negócio

Comandos administrativos enviados pelo gerenciador devem ser executados automaticamente pelo player, desde que venham autenticados e autorizados.

## Tarefas Técnicas

### Backend

* [ ] Revisar tabela/modelo de comandos pendentes.
* [ ] Garantir status: `pending`, `received`, `executing`, `success`, `failed`.
* [ ] Adicionar timeout e retry controlado.
* [ ] Registrar erro do comando quando falhar.
* [ ] Garantir que comando `restart_player` seja idempotente.

### Player

* [ ] Ao receber comando `restart_player`, pausar reprodução.
* [ ] Salvar estado atual.
* [ ] Confirmar recebimento para backend.
* [ ] Executar reinício sem modal.
* [ ] Após reiniciar, enviar `restart_success`.
* [ ] Se falhar, enviar `restart_failed` com motivo.

### App Windows / Plugin

* [ ] Validar se o restart está chamando `window.location.reload`, restart do processo ou comando nativo.
* [ ] Evitar prompts nativos que exijam confirmação.
* [ ] Garantir restart silencioso em modo kiosk.

## Critérios de Aceite

* [ ] Ao clicar em reiniciar no gerenciador, o player reinicia sem confirmação manual.
* [ ] O comando muda de `pending` para `success`.
* [ ] O player volta para a campanha/playlist anterior.
* [ ] Nenhum modal bloqueia a reprodução.
* [ ] O log do dispositivo mostra horário e resultado do comando.

---

# 7. SPEC-003 — Exclusão Correta de Faixas de Áudio

## Problema

Antes era possível excluir faixas de áudio. Agora o sistema apenas arquiva, e os itens continuam aparecendo.

## Comportamento Esperado

O sistema deve diferenciar claramente:

* Arquivar
* Restaurar
* Excluir definitivamente

Por padrão, itens arquivados não devem aparecer nas listas operacionais.

## Regra de Negócio

Faixas arquivadas não podem aparecer em seleção de rádio, playlist sonora, campanha ou player, salvo quando o usuário ativar filtro “mostrar arquivadas”.

A exclusão definitiva deve remover ou inutilizar a faixa, respeitando dependências.

## Tarefas Técnicas

### Backend

* [ ] Auditar model/tabela de faixas de áudio.
* [ ] Verificar campos: `status`, `is_active`, `archived_at`, `deleted_at`.
* [ ] Padronizar soft delete com `deleted_at`.
* [ ] Criar endpoint para arquivar.
* [ ] Criar endpoint para restaurar.
* [ ] Criar endpoint para excluir definitivamente, se permitido.
* [ ] Impedir exclusão definitiva se a faixa estiver em uso ativo, ou remover vínculos com segurança.
* [ ] Garantir que queries padrão filtrem `deleted_at IS NULL` e `archived_at IS NULL`.

### Frontend

* [ ] Separar botão “Arquivar” de “Excluir definitivamente”.
* [ ] Adicionar confirmação antes da exclusão definitiva.
* [ ] Adicionar filtro “Mostrar arquivadas”.
* [ ] Esconder arquivadas por padrão.
* [ ] Atualizar listagem imediatamente após ação.

### Testes

* [ ] Criar faixa.
* [ ] Arquivar faixa.
* [ ] Verificar que ela não aparece por padrão.
* [ ] Ativar filtro de arquivadas e verificar que aparece.
* [ ] Restaurar faixa.
* [ ] Excluir faixa definitivamente.
* [ ] Verificar que não aparece em nenhuma seleção operacional.

## Critérios de Aceite

* [ ] Faixas arquivadas não aparecem na operação padrão.
* [ ] Excluir definitivamente remove a faixa da listagem.
* [ ] O usuário entende visualmente a diferença entre arquivar e excluir.
* [ ] Não existem faixas “fantasmas” aparecendo no player ou nas playlists.

---

# 8. SPEC-004 — Exclusão Correta de Playlist Sonora

## Problema

Playlist sonora não exclui corretamente. Apenas arquiva e continua aparecendo no sistema.

## Comportamento Esperado

Playlist sonora arquivada não deve aparecer nas listas principais nem ser usada pelo player.

## Regra de Negócio

Playlist sonora com `archived_at` ou `deleted_at` não pode ser elegível para reprodução.

## Tarefas Técnicas

### Backend

* [ ] Auditar endpoints de playlist sonora.
* [ ] Verificar se listagens filtram arquivadas/deletadas.
* [ ] Criar endpoint `archive`.
* [ ] Criar endpoint `restore`.
* [ ] Criar endpoint `delete`.
* [ ] Garantir que player não receba playlists arquivadas.
* [ ] Garantir que campanhas/radio não usem playlist arquivada.

### Frontend

* [ ] Ajustar listagem para esconder arquivadas por padrão.
* [ ] Adicionar filtro de arquivadas.
* [ ] Adicionar botão restaurar.
* [ ] Adicionar ação de excluir definitivamente quando permitido.
* [ ] Remover playlist da tela após exclusão/arquivamento.

## Critérios de Aceite

* [ ] Playlist arquivada desaparece da lista padrão.
* [ ] Playlist arquivada não toca no player.
* [ ] Playlist excluída não aparece mais.
* [ ] O sistema não quebra vínculos existentes sem aviso.

---

# 9. SPEC-005 — Criação de Usuário com Senha e Acesso por E-mail

## Problema

O sistema cria usuário, mas:

* Não abre opção para criar senha.
* O e-mail criado para login não recebe acesso.
* O usuário não consegue entrar.

## Comportamento Esperado

Ao criar um usuário, o administrador deve poder:

1. Criar usuário com e-mail e perfil.
2. Escolher entre definir senha manualmente ou enviar convite.
3. O usuário deve receber e-mail de criação de senha.
4. O link deve permitir criar senha e acessar o sistema.
5. O login deve funcionar após ativação.

## Regra de Negócio

Usuário criado sem senha deve ficar como `pending_invite`.

Usuário só pode acessar após definir senha ou ter senha temporária válida.

Convite deve expirar por segurança.

## Tarefas Técnicas

### Backend

* [ ] Auditar model de usuário.
* [ ] Verificar campos: `email`, `password_hash`, `status`, `role`, `tenant_id`, `invite_token`, `invite_expires_at`.
* [ ] Criar endpoint para criar usuário com convite.
* [ ] Criar endpoint para reenviar convite.
* [ ] Criar endpoint para aceitar convite e definir senha.
* [ ] Criar endpoint para reset de senha, se ainda não existir.
* [ ] Validar envio de e-mail SMTP/provider.
* [ ] Criar logs de envio de convite.
* [ ] Não permitir login de usuário sem senha ativa.

### Frontend

* [ ] No modal de criar usuário, adicionar escolha:

  * Enviar convite por e-mail
  * Definir senha manualmente
* [ ] Adicionar tela de aceitar convite.
* [ ] Adicionar feedback de envio de convite.
* [ ] Adicionar botão “reenviar convite”.
* [ ] Mostrar status do usuário: ativo, convite pendente, bloqueado.

### Testes

* [ ] Criar usuário com convite.
* [ ] Verificar recebimento/envio de e-mail.
* [ ] Abrir link de convite.
* [ ] Criar senha.
* [ ] Fazer login.
* [ ] Reenviar convite.
* [ ] Tentar login antes de criar senha.
* [ ] Testar convite expirado.

## Critérios de Aceite

* [ ] Usuário criado recebe forma real de acesso.
* [ ] Admin consegue definir senha ou enviar convite.
* [ ] Login funciona após ativação.
* [ ] Usuário pendente não consegue logar sem senha.
* [ ] Sistema exibe status correto do usuário.

---

# 10. SPEC-006 — Spot da Rádio sem Misturar com Música

## Problema

Spot não aguarda terminar música. Ele entra direto e, às vezes, toca em cima da música da rádio, misturando o som.

## Comportamento Esperado

O spot deve obedecer política configurável, com padrão seguro:

* Não misturar áudio.
* Não tocar por cima da música.
* Aguardar fim da música ou fazer pausa controlada.
* Retomar rádio corretamente após o spot.

## Regra de Negócio

Por padrão, spot da rádio deve tocar entre músicas, não por cima da música atual.

Política padrão: `WAIT_TRACK_END`.

Políticas possíveis:

1. `WAIT_TRACK_END`: aguarda terminar a música atual.
2. `INTERRUPT_WITH_FADE`: interrompe com fade-out, toca spot e retorna.
3. `DUCKING`: baixa volume da música e toca spot por cima, somente se explicitamente configurado.
4. `IMMEDIATE`: toca imediatamente, somente para emergência.

Para o caso do cliente, usar `WAIT_TRACK_END`.

## Tarefas Técnicas

### Backend

* [ ] Adicionar ou validar campo `insertion_policy` em spot/agendamento.
* [ ] Validar `interval_seconds`.
* [ ] Validar janela de horário do spot.
* [ ] Retornar ao player a próxima oportunidade de spot.
* [ ] Registrar evento de spot agendado, tocado, pulado ou atrasado.
* [ ] Evitar enviar spot elegível repetidamente sem controle.

### Player / Audio Engine

* [ ] Criar fila de spot separada da fila de música.
* [ ] Nunca permitir dois elementos de áudio tocando ao mesmo tempo, exceto modo `DUCKING`.
* [ ] Implementar lock de áudio: `audioPlaybackLock`.
* [ ] Quando spot ficar elegível durante música:

  * Marcar spot como pendente.
  * Aguardar evento `ended` da música.
  * Tocar spot.
  * Retomar próxima música.
* [ ] Garantir fade-out/fade-in quando aplicável.
* [ ] Registrar logs:

  * `SPOT_ELIGIBLE`
  * `SPOT_QUEUED`
  * `SPOT_STARTED`
  * `SPOT_FINISHED`
  * `RADIO_RESUMED`
  * `SPOT_SKIPPED_REASON`

### Testes

* [ ] Música tocando e spot fica elegível.
* [ ] Spot aguarda fim da música.
* [ ] Spot toca sozinho.
* [ ] Música seguinte toca após spot.
* [ ] Não existe sobreposição de áudio.
* [ ] Spot não entra duplicado.
* [ ] Spot respeita intervalo.
* [ ] Spot respeita horário/dia/período.

## Critérios de Aceite

* [ ] Spot não mistura com música.
* [ ] Spot aguarda a música terminar no modo padrão.
* [ ] Rádio retoma corretamente após spot.
* [ ] Logs mostram a decisão do player.
* [ ] Não há loop infinito de spot.
* [ ] Não há dois áudios tocando ao mesmo tempo.

---

# 11. SPEC-007 — Minimizar Tela no Windows sem Cortar Conteúdo

## Problema

A função de minimizar tela no Windows é necessária para uso em loja, mas atualmente minimiza por cima dos conteúdos, sem esperar o término do que está passando.

Cliente deseja que:

* O sistema espere o conteúdo atual terminar.
* Opcionalmente exiba uma arte/aviso alguns segundos antes.
* Depois minimize a tela.
* Não interrompa vídeos, campanhas ou playlist no meio.

## Comportamento Esperado

O comando/agendamento de minimizar deve ser tratado como uma ação de fila, não como interrupção imediata.

## Regra de Negócio

Minimização programada deve respeitar o conteúdo atual.

Política padrão: `WAIT_CONTENT_END`.

Fluxo esperado:

1. Sistema recebe comando/agendamento de minimizar.
2. Player verifica se existe mídia em execução.
3. Se houver mídia, agenda minimização para o fim da mídia.
4. X segundos antes do fim, exibe aviso visual configurável.
5. Ao terminar mídia, minimiza.
6. Após tempo configurado, restaura/expande se essa for a regra definida.
7. Registra sucesso/falha.

## Tarefas Técnicas

### Backend

* [ ] Criar configuração de minimização por dispositivo ou grupo.
* [ ] Campos sugeridos:

  * `enabled`
  * `interval_seconds`
  * `duration_seconds`
  * `policy`
  * `show_warning`
  * `warning_seconds_before`
  * `warning_media_id`
  * `warning_text`
* [ ] Criar endpoint para enviar comando `minimize_screen`.
* [ ] Criar endpoint para enviar comando `restore_screen`.
* [ ] Registrar histórico de execução.

### Player

* [ ] Receber comando de minimizar.
* [ ] Se política for `WAIT_CONTENT_END`, não minimizar imediatamente.
* [ ] Calcular tempo restante da mídia atual.
* [ ] Exibir aviso antes do fim, se configurado.
* [ ] Emitir evento para plugin Windows no momento correto.
* [ ] Bloquear múltiplos comandos simultâneos.

### Plugin Windows

* [ ] Receber comando local do player.
* [ ] Minimizar app/janela sem prompt.
* [ ] Restaurar app/janela após tempo configurado.
* [ ] Confirmar execução ao player/backend.
* [ ] Não roubar foco indevidamente.
* [ ] Não interromper reprodução antes da hora.

### Frontend / Gerenciador

* [ ] Criar configuração de minimização por dispositivo.
* [ ] Permitir configurar:

  * Ativar/desativar
  * Intervalo
  * Duração minimizado
  * Aguardar fim do conteúdo
  * Aviso antes de minimizar
  * Texto/arte do aviso
* [ ] Exibir status da última execução.

## Critérios de Aceite

* [ ] Minimização não acontece no meio do vídeo/conteúdo.
* [ ] Player espera o conteúdo terminar.
* [ ] Aviso aparece antes, se configurado.
* [ ] Janela minimiza corretamente no Windows.
* [ ] Janela restaura corretamente, se configurado.
* [ ] O gerenciador mostra sucesso/falha.
* [ ] Não há necessidade de acesso físico ao player.

---

# 12. SPEC-008 — Travamento/Picotamento de Vídeo no Player

## Problema

Vídeos rodam normalmente no gerenciador, mas no player ficam travando/picotando, principalmente animações.

## Hipóteses Técnicas

Possíveis causas:

* Player usando renderização diferente do gerenciador.
* Vídeo sem preload adequado.
* Cache mal gerenciado.
* Arquivo pesado para hardware do dispositivo.
* Codec incompatível ou mal otimizado.
* Re-renderizações excessivas no React.
* Troca de mídia desmontando/remontando vídeo.
* Uso incorreto de `window.location.reload`.
* Concorrência entre áudio, vídeo, rádio e spot.
* Falta de hardware acceleration no WebView/Electron/Capacitor.
* Serviço de mídia entregando arquivo sem headers adequados.
* Streaming sem suporte a range request.

## Comportamento Esperado

O player deve reproduzir vídeo de forma fluida, com preload/cache, sem travar animações em condições normais.

## Tarefas Técnicas

### Diagnóstico

* [ ] Comparar reprodução do mesmo arquivo no gerenciador e no player.
* [ ] Verificar codec, bitrate, resolução, FPS e tamanho do vídeo.
* [ ] Verificar se backend suporta HTTP Range Requests.
* [ ] Verificar headers:

  * `Accept-Ranges`
  * `Content-Length`
  * `Content-Type`
  * `Cache-Control`
* [ ] Medir tempo de carregamento do vídeo no player.
* [ ] Medir quedas de frame se possível.
* [ ] Verificar uso de CPU/memória no dispositivo.
* [ ] Verificar se o player re-renderiza durante reprodução.
* [ ] Verificar se existe áudio/radio/spot interferindo.

### Backend / Mídia

* [ ] Garantir entrega eficiente de arquivos de vídeo.
* [ ] Suportar range request para vídeo.
* [ ] Configurar cache adequado.
* [ ] Validar MIME type correto.
* [ ] Criar endpoint de diagnóstico de mídia.
* [ ] Armazenar metadata do vídeo:

  * duração
  * resolução
  * codec
  * bitrate
  * fps
  * tamanho

### Player

* [ ] Implementar preload da próxima mídia.
* [ ] Evitar desmontar o componente de vídeo desnecessariamente.
* [ ] Usar buffer/cache local quando possível.
* [ ] Evitar `reload` total da página em troca de campanha.
* [ ] Separar renderização de UI do loop de reprodução.
* [ ] Garantir que apenas a mídia ativa consome recursos.
* [ ] Implementar fallback quando vídeo não carrega.
* [ ] Registrar eventos:

  * `VIDEO_LOAD_START`
  * `VIDEO_CAN_PLAY`
  * `VIDEO_STALLED`
  * `VIDEO_WAITING`
  * `VIDEO_PLAYING`
  * `VIDEO_ERROR`
  * `VIDEO_ENDED`

### Testes

* [ ] Testar vídeo leve.
* [ ] Testar vídeo pesado.
* [ ] Testar animação curta.
* [ ] Testar loop de playlist com múltiplos vídeos.
* [ ] Testar player em Windows.
* [ ] Testar player em Linux.
* [ ] Testar player em Android/TV Box, se aplicável.
* [ ] Testar sem rádio.
* [ ] Testar com rádio.
* [ ] Testar com spot agendado.

## Critérios de Aceite

* [ ] O mesmo vídeo que roda bem no gerenciador roda bem no player.
* [ ] Player não trava animação em uso normal.
* [ ] Logs indicam causa quando houver travamento.
* [ ] Vídeo não é reiniciado indevidamente.
* [ ] Player não faz reload total sem necessidade.
* [ ] Backend entrega vídeo com headers corretos.

---

# 13. SPEC-009 — Exclusão de Mídias com Seleção em Massa

## Problema

Exclusão de mídias está limitada a 1 por 1. Cliente solicita opção de seleção múltipla para excluir/arquivar várias mídias.

## Comportamento Esperado

Tela de mídias deve permitir selecionar múltiplos itens e aplicar ação em lote.

## Regra de Negócio

Ações em massa devem respeitar dependências.

Se uma mídia estiver em uso ativo, o sistema deve:

* Avisar o usuário.
* Permitir arquivar em vez de excluir.
* Impedir exclusão definitiva quando necessário.
* Mostrar quais mídias não puderam ser excluídas.

## Tarefas Técnicas

### Backend

* [ ] Criar endpoint bulk para arquivar mídias.
* [ ] Criar endpoint bulk para excluir mídias, se permitido.
* [ ] Retornar resultado por item:

  * `success`
  * `failed`
  * `reason`
* [ ] Validar permissões do usuário.
* [ ] Garantir isolamento por `tenant_id`.

### Frontend

* [ ] Adicionar checkbox por mídia.
* [ ] Adicionar selecionar todas.
* [ ] Adicionar barra de ações em lote.
* [ ] Adicionar confirmação antes de excluir/arquivar.
* [ ] Mostrar resumo:

  * Quantas foram selecionadas.
  * Quantas foram arquivadas.
  * Quantas falharam.
  * Motivo das falhas.
* [ ] Atualizar lista após ação.

### Testes

* [ ] Selecionar uma mídia.
* [ ] Selecionar várias mídias.
* [ ] Selecionar todas.
* [ ] Arquivar em massa.
* [ ] Excluir em massa.
* [ ] Testar mídia em uso.
* [ ] Testar sem permissão.
* [ ] Testar outro tenant.

## Critérios de Aceite

* [ ] Usuário consegue selecionar várias mídias.
* [ ] Usuário consegue arquivar/excluir em lote.
* [ ] Sistema informa falhas por item.
* [ ] Mídias em uso não causam erro geral.
* [ ] Não há vazamento entre tenants.

---

# 14. SPEC-010 — Auditoria de Arquivamento vs Exclusão no Sistema

## Problema Geral

Há confusão entre arquivar e excluir em:

* Faixas de áudio
* Playlist sonora
* Mídias

Itens arquivados continuam aparecendo onde não deveriam.

## Comportamento Esperado

Todo recurso gerenciável deve seguir padrão único:

* Ativo: aparece e pode ser usado.
* Arquivado: não aparece na operação padrão, mas pode ser restaurado.
* Excluído: não aparece e não pode ser usado.

## Tarefas Técnicas

* [ ] Criar padrão global para `status`, `archived_at`, `deleted_at`.
* [ ] Revisar todos os CRUDs.
* [ ] Revisar todos os services.
* [ ] Revisar todos os schemas.
* [ ] Revisar queries do player.
* [ ] Revisar queries do gerenciador.
* [ ] Garantir que arquivado/deletado não vá para o player.
* [ ] Garantir que arquivado/deletado não apareça em selects.
* [ ] Criar testes automatizados para filtros.

## Critérios de Aceite

* [ ] Arquivados não aparecem por padrão.
* [ ] Excluídos não aparecem nunca.
* [ ] Player não recebe itens arquivados/deletados.
* [ ] Gerenciador só mostra arquivados quando filtro for ativado.

---

# 15. Definition of Done Geral

Uma tarefa só deve ser considerada concluída quando:

* [ ] Backend implementado.
* [ ] Frontend implementado.
* [ ] Player implementado, quando aplicável.
* [ ] Plugin Windows implementado, quando aplicável.
* [ ] Testes manuais documentados.
* [ ] Testes automatizados adicionados, quando possível.
* [ ] Logs úteis adicionados.
* [ ] Erros tratados com mensagem clara.
* [ ] Não há dados mockados envolvidos.
* [ ] Não quebra tenant isolation.
* [ ] Não quebra fluxo atual de campanha/player.
* [ ] Critérios de aceite do SPEC foram validados.

---

# 16. Plano de Execução por Sprint

## Sprint 1 — Estabilidade Operacional do Player

* [ ] SPEC-001 — Inicialização automática.
* [ ] SPEC-002 — Reinício remoto sem confirmação.
* [ ] SPEC-008 — Diagnóstico inicial de vídeo travando.

Entrega esperada: player inicia e reinicia sozinho, com logs melhores.

## Sprint 2 — Rádio e Spot

* [ ] SPEC-006 — Spot sem misturar com música.
* [ ] Testes de fila, intervalo e política de inserção.
* [ ] Logs de áudio e spot.

Entrega esperada: rádio toca música e spot sem sobreposição.

## Sprint 3 — Windows / Minimizar

* [ ] SPEC-007 — Minimizar aguardando fim do conteúdo.
* [ ] Aviso antes de minimizar.
* [ ] Integração com plugin Windows.

Entrega esperada: função de loja funcionando sem cortar conteúdo.

## Sprint 4 — Gestão Administrativa

* [ ] SPEC-003 — Excluir/arquivar faixas.
* [ ] SPEC-004 — Excluir/arquivar playlist sonora.
* [ ] SPEC-009 — Exclusão em massa de mídias.
* [ ] SPEC-010 — Padronização arquivamento/exclusão.

Entrega esperada: gerenciador limpo, sem itens fantasmas.

## Sprint 5 — Usuários e Acesso

* [ ] SPEC-005 — Usuário com senha/convite.
* [ ] E-mail de convite.
* [ ] Tela de criação de senha.
* [ ] Reenvio de convite.

Entrega esperada: usuário criado consegue acessar o sistema.

---

# 17. Checklist de Auditoria para a IA/Dev Antes de Implementar

Antes de alterar código, auditar:

## Backend

* [ ] Models.
* [ ] Schemas.
* [ ] Routers.
* [ ] Services.
* [ ] CRUD.
* [ ] Tasks.
* [ ] WebSocket/SSE/polling de comandos.
* [ ] Regras de tenant.
* [ ] Migrations.
* [ ] Seeds.
* [ ] Envio de e-mail.
* [ ] Entrega de mídia/vídeo.
* [ ] Logs.

## Frontend Gerenciador

* [ ] Telas de mídias.
* [ ] Telas de áudio/faixas.
* [ ] Tela de playlist sonora.
* [ ] Tela de usuários.
* [ ] Tela de dispositivos.
* [ ] Tela de comandos.
* [ ] Tela de configuração do Windows/minimizar.
* [ ] Filtros de arquivado/deletado.
* [ ] Ações em lote.

## Player

* [ ] Boot inicial.
* [ ] Cache local.
* [ ] Sessão do device.
* [ ] Reprodução de vídeo.
* [ ] Reprodução de rádio.
* [ ] Reprodução de spot.
* [ ] Fila de mídia.
* [ ] Fila de áudio.
* [ ] Comandos remotos.
* [ ] Logs.
* [ ] Reloads indevidos.
* [ ] Concorrência de áudio.

## Windows Plugin

* [ ] Inicialização automática.
* [ ] Minimizar.
* [ ] Restaurar.
* [ ] Restart silencioso.
* [ ] Comunicação com player/backend.
* [ ] Confirmação de comandos.
* [ ] Logs locais.

---

# 18. Prompt para IA Implementar

Você é uma IA engenheira de software atuando no projeto PlayWave.

Sua missão é implementar os SPECs abaixo com abordagem SPEC Driven Development.

Antes de codar:

1. Audite backend, frontend, player e plugin Windows.
2. Identifique arquivos, funções, endpoints, models, schemas e services impactados.
3. Verifique se já existe implementação parcial.
4. Não duplique regra de negócio.
5. Não crie mock.
6. Não quebre tenant isolation.
7. Não remova funcionalidades existentes sem justificar.
8. Não implemente solução superficial apenas na UI.
9. Sempre conecte frontend, backend e player quando o fluxo exigir.
10. Crie ou atualize testes.

Implemente na seguinte ordem:

1. SPEC-001 — Inicialização automática do player.
2. SPEC-002 — Reinício remoto sem confirmação.
3. SPEC-006 — Spot da rádio sem misturar com música.
4. SPEC-008 — Diagnóstico e correção de vídeo travando no player.
5. SPEC-007 — Minimizar tela no Windows sem cortar conteúdo.
6. SPEC-003 — Exclusão correta de faixas de áudio.
7. SPEC-004 — Exclusão correta de playlist sonora.
8. SPEC-009 — Exclusão de mídias com seleção em massa.
9. SPEC-005 — Criação de usuário com senha/convite.
10. SPEC-010 — Padronização de arquivamento vs exclusão.

Para cada SPEC, entregue:

* Diagnóstico do estado atual.
* Arquivos impactados.
* Plano técnico.
* Implementação.
* Testes.
* Critérios de aceite validados.
* Riscos e pendências.

Não considere concluído enquanto o comportamento real do player, gerenciador e backend não estiver coerente de ponta a ponta.

---

# 19. Resultado Esperado Final

Ao final da implementação:

* O player liga sozinho.
* O player reinicia remotamente sem clique humano.
* O spot não mistura com a música da rádio.
* O minimizar no Windows espera o conteúdo terminar.
* Pode aparecer aviso antes da minimização.
* Vídeos rodam de forma fluida no player.
* Faixas e playlists arquivadas não aparecem indevidamente.
* Mídias podem ser excluídas/arquivadas em massa.
* Usuários recebem acesso real com senha ou convite.
* O sistema fica pronto para operação em loja sem depender de acesso físico constante ao player.

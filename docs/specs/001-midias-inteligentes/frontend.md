# SPEC 001 — Frontend

## Arquivos analisados

- `frontend/src/api/midias.js`
- `frontend/src/pages/BibliotecaMidias.jsx`
- `frontend/src/pages/MidiaUpload.jsx`
- `frontend/src/components/media/MediaFormModal.jsx`
- `frontend/src/components/media/MediaThumb.jsx`
- `frontend/src/components/campaigns/CampaignFormModal.jsx`
- `frontend/src/pages/CampanhaPreview.jsx`
- `frontend/src/utils/mediaUtils.js`

## Estado atual

### API client

`frontend/src/api/midias.js` contem funcoes para:

- listar midias;
- buscar midia;
- upload;
- criar midia externa;
- atualizar midia;
- substituir arquivo;
- buscar uso;
- listar versoes;
- deletar midia.

### Biblioteca de midias

`BibliotecaMidias.jsx` lista midias, filtra por tipo/categoria, exibe thumbnail e permite editar/excluir/preview.

### Formulario de midia

`MediaFormModal.jsx` possui:

- upload;
- URL externa;
- nome;
- descricao;
- tipo;
- duracao;
- categoria;
- tags;
- observacoes.

Pontos relacionados a esta SPEC:

- Video/audio devem exibir duracao detectada.
- Imagem/link devem permitir duracao manual.
- Edicao deve permitir substituir arquivo.
- Datas de inicio/fim devem aparecer no formulario.

### Campanha

`CampaignFormModal.jsx` ainda seleciona midias diretamente, com modelo simples baseado em `media_ids`.

Observacao:

- Esta SPEC nao substitui esse fluxo por playlist relacional.
- Deve apenas garantir que midias invalidas sejam visiveis/alertadas quando usadas.

## Requisitos de UI

### Tela de criacao/edicao de midia

Campos:

- nome;
- descricao;
- tipo;
- arquivo ou URL;
- duracao detectada;
- duracao personalizada opcional;
- inicio de exibicao;
- fim de exibicao;
- categoria;
- tags;
- observacoes;
- status ativo/inativo;
- substituir arquivo quando for edicao.

### Comportamento por tipo

Video:

- mostrar duracao detectada;
- mostrar "Reproducao: ate o fim do arquivo";
- permitir duracao personalizada opcional.

Audio:

- mostrar duracao detectada;
- permitir duracao personalizada opcional.

Imagem:

- exigir ou sugerir duracao manual.

Link/webview/html:

- exigir duracao manual.

### Biblioteca

Deve mostrar:

- tipo;
- tamanho;
- duracao real/configurada;
- periodo de exibicao;
- status calculado;
- uso em campanhas;
- tags/categoria.

## Regras de frontend

- Nao usar mock/localStorage para simular funcionalidade administrativa.
- Todo dado deve vir da API real.
- Nao permitir salvar video/audio exigindo duracao manual.
- Nao permitir `ends_at` menor que `starts_at` quando validacao client-side for adicionada.
- Mostrar erro amigavel retornado pelo backend.

## Pendencias

- Modal detalhado de historico de versoes.
- Aviso detalhado antes de substituir midia usada em campanhas.
- Confirmacao forte para exclusao forcada.
- Alertas na tela de campanha para midia expirada/agendada.
- Ajustar preview de campanha para respeitar novas duracoes/status.

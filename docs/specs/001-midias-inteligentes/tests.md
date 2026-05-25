# SPEC 001 — Test Plan

## Objetivo dos testes

Garantir que midias inteligentes funcionem sem quebrar campanhas existentes, agendamentos e player.

## Testes de backend

### Upload de video

Passos:

1. Enviar arquivo MP4 valido para `/media/upload`.
2. Conferir resposta.
3. Conferir banco.

Esperado:

- `duration_seconds` preenchido.
- `display_duration_seconds` nulo se nao informado.
- `file_hash` preenchido.
- `file_version = 1`.
- `media_versions` criada.

### Upload de audio

Esperado:

- `duration_seconds` preenchido.
- Usuario nao informa duracao manual.

### Upload de imagem

Esperado:

- `duration_seconds` nulo.
- `display_duration_seconds` preenchido por valor enviado ou padrao.

### Periodo invalido

Entrada:

- `starts_at = 2026-05-21`
- `ends_at = 2026-05-20`

Esperado:

- API retorna erro 422.

### Midia agendada

Entrada:

- `starts_at` no futuro.

Esperado:

- `availability_status = scheduled`.
- Midia nao aparece como valida no payload do player.

### Midia expirada

Entrada:

- `ends_at` no passado.

Esperado:

- `availability_status = expired`.
- Midia nao aparece como valida no payload do player.

### Substituir arquivo

Passos:

1. Criar midia.
2. Vincular a campanha.
3. Chamar `POST /media/{id}/replace-file`.
4. Conferir campanha.

Esperado:

- `media.id` nao muda.
- Campanha continua referenciando a mesma midia.
- `file_version` incrementa.
- Nova linha em `media_versions`.
- Cache dos devices afetados e invalidado.

## Testes de frontend

- Formulario nao exige duracao manual para video.
- Formulario nao exige duracao manual para audio.
- Formulario exige/sugere duracao para imagem.
- Formulario exibe duracao detectada.
- Formulario permite duracao customizada opcional.
- Formulario permite inicio/fim.
- Listagem mostra status calculado.
- Listagem mostra periodo de exibicao.
- Botao "Substituir arquivo" aparece apenas em edicao.
- Erros do backend aparecem para o usuario.

## Testes de player

### Video ate o fim

Entrada:

- Midia video com `display_duration_seconds = null`.

Esperado:

- Player avanca apenas no `onEnded`.

### Video com duracao customizada

Entrada:

- `duration_seconds = 60`
- `display_duration_seconds = 30`

Esperado:

- Player avanca em 30 segundos.

### Imagem

Entrada:

- `display_duration_seconds = 15`

Esperado:

- Player avanca em 15 segundos.

### Cache invalido

Entrada:

- Mesmo `media_id`, novo `file_version` ou `file_hash`.

Esperado:

- Player nao reutiliza arquivo antigo.

## Testes de regressao

- Campanha existente com `media_ids` continua funcionando.
- Campanha existente com `media_order` continua funcionando.
- Player antigo que usa `duration` nao quebra.
- Delete de midia em uso nao remove silenciosamente campanhas.
- Upload de arquivo invalido retorna erro amigavel.

## Comandos sugeridos

Backend:

```bash
python3 -m py_compile backend/api/v1/media.py backend/api/v1/devices.py backend/core/models.py backend/core/schemas_completos.py
```

Frontend:

```bash
cd frontend
npm run build
```

Manual:

```bash
curl -X POST /media/upload
curl /media/{id}/usage
curl /media/{id}/versions
curl /devices/{device_id}/playlist
```

## Criterio de aceite final

- Video/audio detectam duracao real.
- Midia possui periodo de exibicao.
- Midia expirada/agendada nao toca.
- Substituicao preserva `media_id`.
- Campanhas nao perdem vinculo.
- Player recebe nova versao.
- Cache antigo e invalidado.
- Frontend mostra status e duracao corretamente.

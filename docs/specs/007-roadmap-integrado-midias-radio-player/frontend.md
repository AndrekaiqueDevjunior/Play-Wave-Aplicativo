# SPEC 007 — Frontend Admin

## Telas envolvidas

- `BibliotecaMidias.jsx`
- `MediaFormModal.jsx`
- `Campanhas.jsx`
- `CampaignFormModal.jsx`
- `FaixasAudio.jsx`
- `AudioTrackFormModal.jsx`
- `PlaylistsSonoras.jsx`
- `AudioPlaylistsFormModal.jsx`
- `DispositivoDetalhe.jsx`
- `ConfigEmpresa.jsx`

## Estado atual

### Midia

Ja possui:

- upload simples;
- duracao manual para imagem/URL;
- duracao detectada exibida para video/audio;
- periodo inicio/fim;
- substituir arquivo;
- status de disponibilidade.

Lacunas:

- historico de versoes ainda nao tem modal dedicado;
- erro de `ffprobe` poderia ser mais claro na UI de upload;
- imagem ainda usa duracao fixa local, precisa default configuravel por tenant.

### Campanha

Atual:

- `CampaignFormModal` usa checkboxes/lista clicavel de midias e salva `media_ids`;
- backend relacional de itens ja existe, mas UI nao usa como fluxo principal.

Alvo:

- criar `CampaignPlaylistBuilder`;
- usar endpoints `/campaigns/{id}/items`;
- mostrar item por item com ordem, duracao, periodo, ativo/inativo, repeat;
- suporte a drag and drop e botoes mover.

### Radio

Atual:

- `FaixasAudio` lista, filtra, toca preview e arquiva;
- `AudioTrackFormModal` faz upload individual;
- `AudioPlaylistsFormModal` adiciona faixas uma a uma e reordena por drag simples;
- `shuffle_enabled` ja aparece.

Alvo:

- upload multiplo em `FaixasAudio`;
- selecao multipla de faixas;
- pastas de audio;
- agenda de pastas por horario;
- spots com intervalo;
- status de upload por arquivo.

### Dispositivos/comandos

Atual:

- `DispositivoDetalhe` tem comandos, audio policy, OSD e eventos de pareamento;
- componentes de confirmacao destrutiva e timeline existem.

Alvo:

- evidenciar `platform_unsupported`;
- mostrar ciclo `pending > received > executing > completed/failed`;
- filtro de comandos por status;
- instrucoes por plataforma no painel.

## Componentes novos propostos

- `CampaignPlaylistBuilder.jsx`
- `AddCampaignMediaDrawer.jsx`
- `CampaignPlaylistItemEditor.jsx`
- `MultiAudioUploadDialog.jsx`
- `AudioFolderList.jsx`
- `AudioFolderFormModal.jsx`
- `AudioFolderTrackPicker.jsx`
- `RadioScheduleEditor.jsx`
- `AudioSpotFormModal.jsx`
- `AudioSpotScheduleList.jsx`
- `CommandStatusPanel.jsx`

## Remocoes/migracoes de UI

- Checkbox simples de midia em campanha deixa de ser fluxo principal.
- `AudioPlaylist.track_ids` segue exibido por compat, mas formulario passa a preferir `audio_playlist_items`.

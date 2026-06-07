# SPEC 009 - Banco de Dados

## Tabela alvo

Adicionar campos na tabela `devices`.

Justificativa:

- comportamento e especifico do player/dispositivo;
- `Device` ja possui `group`, `os`, `player_version`, `config_version`;
- permite override por dispositivo desde o primeiro rollout;
- heranca por tenant/grupo pode ser implementada depois sem acoplar em campanhas.

## Campos propostos

```text
desktop_exposure_enabled boolean not null default false
desktop_exposure_interval_seconds integer null
desktop_exposure_duration_seconds integer null
desktop_exposure_restore_fullscreen boolean not null default true
desktop_exposure_updated_at timestamp null
```

## Validacoes

- `desktop_exposure_interval_seconds`: 10 a 86400 quando enabled.
- `desktop_exposure_duration_seconds`: 1 a 300 quando enabled.
- `duration_seconds < interval_seconds`.
- defaults devem deixar a feature desligada para todos os devices existentes.

## Migration

Nome sugerido:

`backend/alembic/versions/20260601_1800_desktop_exposure_config.py`

## Backfill

Backfill simples:

- `desktop_exposure_enabled=false`;
- `desktop_exposure_restore_fullscreen=true`;
- interval/duration nulos.

## Indices

Nao criar indice no PR inicial.

Racional: leitura ocorre por `device_id`, usando PK existente. Se futuramente houver tela de listagem por devices com feature ativa, criar indice parcial em `desktop_exposure_enabled`.

## Compatibilidade

Players antigos ignoram campos ausentes ou desconhecidos.

Backend deve serializar config como objeto:

```json
{
  "enabled": false,
  "interval_seconds": null,
  "duration_seconds": null,
  "restore_fullscreen": true,
  "updated_at": null
}
```



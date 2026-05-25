# SPEC NNN — Banco

## Migrations existentes (nao mexer)

- {lista, se aplicavel}.

## Migration nova: `2026XXXX_descricao.py`

### Tabelas

```sql
CREATE TABLE ...
```

### Alteracoes em tabelas existentes

```sql
ALTER TABLE ...
```

### Indices

```sql
CREATE INDEX ...
```

### Backfill

{Descrever como dados existentes sao migrados, se aplicavel.}

### Downgrade

```sql
DROP TABLE ...
ALTER TABLE ... DROP COLUMN ...
```

## Mudanca em models Python

```python
class ...
```

## Validacoes no codigo (nao no banco)

- {validacao 1}.
- {validacao 2}.

## Compatibilidade com dados existentes

- {tratamento de NULLs, defaults, backfills}.

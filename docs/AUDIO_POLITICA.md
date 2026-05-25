# Politica de audio do player

Este documento explica como o PlayWave decide entre radio ambiente e audio nativo de videos.

## Regra principal

Quando uma campanha tem playlist de radio e tambem exibe videos, o player usa a politica de audio efetiva da midia atual. A hierarquia e:

1. Midia individual.
2. Campanha.
3. Dispositivo.
4. Empresa.
5. Padrao do sistema: `auto`.

Se um nivel estiver como "herdar", o PlayWave consulta o proximo nivel.

## Politicas disponiveis

| Politica | Comportamento |
| --- | --- |
| Automatico | Se o video tem audio, pausa a radio e toca o video com som. Se nao tem audio, mantem a radio. |
| Apenas radio | Mantem a radio e deixa o video mudo. |
| Apenas audio da midia | Pausa a radio e usa somente o audio do video. |
| Misturar ambos | Toca radio e audio do video ao mesmo tempo. Use apenas em casos especificos. |
| Video mudo com radio ambiente | Mantem a radio e sempre deixa o video mudo. |

## Onde configurar

- Empresa: define o padrao global.
- Dispositivo: sobrescreve o padrao da empresa para uma TV/player especifico.
- Campanha: define o comportamento de todos os itens da campanha.
- Midia: excecao mais especifica para um video individual.

## Deteccao de audio em videos

Nos uploads novos, o backend usa `ffprobe` para detectar se o video tem faixa de audio. Videos antigos podem aparecer como "nao detectado"; nesses casos, o player assume que videos tem audio para evitar misturar som por engano.

Para reanalisar um video antigo, use o botao "Recalcular" na tela da midia. Em lote, a equipe tecnica pode rodar:

```bash
cd backend
python3 -m tasks.media.backfill_has_audio --limit 100
```

Para simular sem gravar no banco:

```bash
cd backend
python3 -m tasks.media.backfill_has_audio --dry-run
```

## Recomendacao operacional

Use `Automatico` como padrao. Ele evita mistura indesejada quando o video tem audio e preserva a radio para imagens ou videos sem som.

Use `Misturar ambos` apenas quando o conteudo foi preparado para isso, como video instrumental ou conteudo sem voz competindo com a radio.

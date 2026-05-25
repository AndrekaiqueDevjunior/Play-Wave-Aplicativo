# SPEC 005 — Frontend Admin

## Arquivos afetados

- `frontend/src/utils/audioPolicy.js` (novo) — enum + labels.
- `frontend/src/components/shared/AudioPolicySelector.jsx` (novo) — selector reusavel.
- `frontend/src/components/campaigns/CampaignFormModal.jsx` — adicionar campo.
- `frontend/src/components/media/MediaFormModal.jsx` — adicionar campo + indicador `has_audio`.
- `frontend/src/components/devices/DeviceEditDrawer.jsx` — adicionar campo.
- `frontend/src/pages/DispositivoDetalhe.jsx` — secao de configuracao de audio.
- `frontend/src/pages/ConfigEmpresa.jsx` — secao de audio para tenant.
- `frontend/src/api/midias.js`, `campanhas.js`, `dispositivos.js`, `tenants.js` — funcoes novas/atualizadas.

## `audioPolicy.js` (utilitario)

```javascript
export const AUDIO_POLICY = {
  AUTO: "auto",
  RADIO_ONLY: "radio_only",
  MEDIA_AUDIO_ONLY: "media_audio_only",
  MIX: "mix",
  MUTED_VIDEO_WITH_RADIO: "muted_video_with_radio",
};

export const AUDIO_POLICY_OPTIONS = [
  {
    value: "auto",
    label: "Automatico (recomendado)",
    description: "Se a midia tem audio, pausa a radio. Se nao tem, mantem a radio.",
  },
  {
    value: "radio_only",
    label: "Apenas radio",
    description: "Video sempre mudo. Radio sempre ativa.",
  },
  {
    value: "media_audio_only",
    label: "Apenas audio da midia",
    description: "Radio pausa enquanto video com audio toca.",
  },
  {
    value: "mix",
    label: "Misturar ambos",
    description: "Audio da midia + radio simultaneamente. Pode soar confuso.",
  },
  {
    value: "muted_video_with_radio",
    label: "Video mudo com radio ambiente",
    description: "Video sempre mudo. Radio ativa quando configurada.",
  },
];

export const AUDIO_POLICY_LABEL = Object.fromEntries(
  AUDIO_POLICY_OPTIONS.map((o) => [o.value, o.label])
);
```

## `AudioPolicySelector.jsx` (componente reusavel)

```javascript
import { AUDIO_POLICY_OPTIONS } from "../../utils/audioPolicy";

/**
 * Selector de politica de audio.
 *
 * Props:
 *  - value: string | null
 *  - onChange: (value: string | null) => void
 *  - allowNull: boolean — se true, oferece "Usar default do nivel superior"
 *  - inheritedLabel: string — texto a mostrar quando value=null (ex: "Usar default da empresa (Automatico)")
 *  - disabled: boolean
 */
export function AudioPolicySelector({
  value,
  onChange,
  allowNull = false,
  inheritedLabel = "Herdar do nivel superior",
  disabled = false,
}) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium">Politica de audio</label>
      <div className="space-y-1">
        {allowNull && (
          <RadioRow
            checked={value === null || value === undefined}
            onChange={() => onChange(null)}
            label={inheritedLabel}
            disabled={disabled}
          />
        )}
        {AUDIO_POLICY_OPTIONS.map((opt) => (
          <RadioRow
            key={opt.value}
            checked={value === opt.value}
            onChange={() => onChange(opt.value)}
            label={opt.label}
            description={opt.description}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
}

function RadioRow({ checked, onChange, label, description, disabled }) {
  return (
    <label className={`flex gap-2 p-2 rounded cursor-pointer hover:bg-gray-50 ${disabled ? "opacity-50" : ""}`}>
      <input
        type="radio"
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className="mt-1"
      />
      <div className="flex-1">
        <div className="text-sm font-medium">{label}</div>
        {description && <div className="text-xs text-gray-500 mt-0.5">{description}</div>}
      </div>
    </label>
  );
}
```

## `CampaignFormModal.jsx`

Adicionar nova secao no formulario:

```javascript
<Section title="Audio">
  <AudioPolicySelector
    value={form.audio_policy}
    onChange={(v) => setForm({ ...form, audio_policy: v })}
    allowNull
    inheritedLabel={`Usar default do dispositivo/empresa (resolvido: ${resolvedDefault})`}
  />

  {/* Campo legado video_muted oculto/deprecated */}
  <details className="text-xs text-gray-400">
    <summary>Configuracoes legadas</summary>
    <label className="flex items-center gap-2 mt-2">
      <input
        type="checkbox"
        checked={form.video_muted}
        onChange={(e) => setForm({ ...form, video_muted: e.target.checked })}
      />
      Forcar video mudo (legado — preferivel usar Politica de audio acima)
    </label>
  </details>
</Section>
```

`resolvedDefault` vem do backend (campo `audio_policy_default` ja calculado considerando device+tenant). Mostrar como hint para o operador entender o que vai acontecer se deixar nulo.

## `MediaFormModal.jsx`

Adicionar:

```javascript
<Section title="Audio">
  <AudioPolicySelector
    value={form.audio_policy}
    onChange={(v) => setForm({ ...form, audio_policy: v })}
    allowNull
    inheritedLabel="Usar politica da campanha"
  />

  {form.type === "video" && (
    <div className="mt-3 p-3 bg-gray-50 rounded text-sm">
      <div className="flex items-center justify-between">
        <span>
          Audio nativo: {form.has_audio === null ? "nao detectado" : form.has_audio ? "presente" : "ausente"}
        </span>
        <button
          type="button"
          onClick={() => recomputeAudioDetection(form.id).then(refetch)}
          className="text-blue-600 hover:underline text-xs"
        >
          Recalcular
        </button>
      </div>
      {form.has_audio === null && (
        <p className="text-xs text-amber-600 mt-1">
          Esta midia ainda nao foi analisada. Recalcule para detectar.
        </p>
      )}
    </div>
  )}
</Section>
```

## `DispositivoDetalhe.jsx`

Adicionar card "Audio" na pagina de detalhes:

```javascript
<Card title="Audio">
  <AudioPolicySelector
    value={device.audio_policy_default}
    onChange={(v) => mutateDevice({ audio_policy_default: v })}
    allowNull
    inheritedLabel={`Usar default da empresa (${tenantPolicy})`}
  />
</Card>
```

## `ConfigEmpresa.jsx`

Adicionar secao "Configuracao de Audio" no menu/formulario do tenant:

```javascript
<Section title="Configuracao de Audio">
  <AudioPolicySelector
    value={tenant.audio_policy_default}
    onChange={(v) => mutateTenant({ audio_policy_default: v })}
    allowNull={false}  // tenant sempre tem default
  />

  <div className="mt-4">
    <label className="block text-sm font-medium">
      Tempo de fade (ms): {tenant.audio_fade_ms || 200}
    </label>
    <input
      type="range"
      min="0"
      max="2000"
      step="50"
      value={tenant.audio_fade_ms || 200}
      onChange={(e) => mutateTenant({ audio_fade_ms: parseInt(e.target.value, 10) })}
      className="w-full"
    />
    <p className="text-xs text-gray-500 mt-1">
      Suavizacao de transicao entre radio e audio de midia. 0 = sem fade, 200 = padrao recomendado.
    </p>
  </div>
</Section>
```

## API clients

### `frontend/src/api/midias.js`

```javascript
export async function recomputeAudioDetection(mediaId) {
  const { data } = await http.post(`/media/${mediaId}/recompute-audio-detection`);
  return data;
}
```

`atualizarMidia` ja envia campos arbitrarios — sem mudanca obrigatoria.

### `frontend/src/api/tenants.js`

```javascript
export async function atualizarConfigAudioEmpresa(tenantId, payload) {
  const { data } = await http.patch(`/tenants/${tenantId}/audio-config`, payload);
  return data;
}
```

### `frontend/src/api/campanhas.js` e `dispositivos.js`

Funcoes existentes (`atualizarCampanha`, `atualizarDispositivo`) ja enviam o body inteiro — sem mudanca.

## Mostrar politica efetiva no preview do player

`frontend/src/pages/CampanhaPreview.jsx`:

Quando preview eh aberto, mostrar tag por midia:

```javascript
<div className="flex gap-2 text-xs">
  <span className="px-2 py-0.5 rounded bg-blue-100">
    Audio: {AUDIO_POLICY_LABEL[media.audio_policy_effective] || "auto"}
  </span>
  {media.has_audio === true && <span className="px-2 py-0.5 rounded bg-green-100">Tem audio nativo</span>}
  {media.has_audio === false && <span className="px-2 py-0.5 rounded bg-gray-100">Sem audio</span>}
</div>
```

## Componente de aviso para `mix`

Quando operador seleciona `mix` em qualquer nivel, mostrar warning inline:

```javascript
{selectedPolicy === "mix" && (
  <Alert variant="warning">
    Atencao: ambos os audios tocam simultaneamente. Pode soar confuso.
    Recomendado apenas para casos especificos como video instrumental sobre radio ambiente.
  </Alert>
)}
```

## Feedback visual de mudanca

- Toast de sucesso ao salvar.
- Indicador "Aplicado em N dispositivos" apos mudanca de campanha.
- Para tenant: "Aplicado em todos os dispositivos da empresa (N)."

## Acessibilidade

- Selector usa `<input type="radio">` real, com labels associados.
- Tooltips via `<details>` ou ARIA `describedby`.
- Foco no primeiro radio ao abrir modal.

## Estados de loading

- Selector desabilitado durante mutation.
- Skeleton em `has_audio` indicator enquanto detecta.
- Botao "Recalcular" mostra spinner durante request.

## Casos de uso

### Caso 1: Operador quer somente radio em todas as TVs

- Vai em ConfigEmpresa → Audio.
- Seleciona "Apenas radio".
- Todas campanhas com `audio_policy=NULL` passam a se comportar como `radio_only`.

### Caso 2: Uma campanha especifica precisa de audio do video

- Operador abre CampaignFormModal.
- Define `audio_policy = media_audio_only`.
- Apenas essa campanha override o default.

### Caso 3: Video instrumental especifico que deve mixar

- Operador abre MediaFormModal do video.
- Define `audio_policy = mix`.
- Apenas esse video override a campanha.

### Caso 4: Dispositivo num ambiente sem radio

- Operador abre DispositivoDetalhe.
- Define `audio_policy_default = media_audio_only`.
- Todas campanhas neste device priorizam audio da midia.

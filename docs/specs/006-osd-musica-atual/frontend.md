# SPEC 006 — Frontend Admin

## Arquivos afetados

- `frontend/src/components/shared/OSDConfigForm.jsx` (novo) — formulario reusavel.
- `frontend/src/components/shared/OSDConfigPreview.jsx` (novo) — preview ao vivo.
- `frontend/src/pages/DispositivoDetalhe.jsx` — secao "Overlay OSD".
- `frontend/src/pages/ConfigEmpresa.jsx` — secao "Overlay OSD".
- `frontend/src/api/dispositivos.js` — `atualizarOSDConfigDispositivo`.
- `frontend/src/api/tenants.js` — `atualizarOSDConfigEmpresa`.

## `OSDConfigForm.jsx`

Formulario reusavel. Props:

```javascript
<OSDConfigForm
  value={config}                  // {show_current_audio, position, duration_seconds, opacity, font_size}
  onChange={onChange}
  allowNull={true}                // true para device (pode resetar para herancar), false para tenant
  inheritedFrom={tenantConfig}    // mostra o que esta sendo herdado
/>
```

Layout:

```javascript
export function OSDConfigForm({ value, onChange, allowNull = false, inheritedFrom = null }) {
  const update = (key) => (v) => onChange({ ...value, [key]: v });

  return (
    <div className="space-y-4">
      {/* Show / Hide toggle */}
      <Field label="Mostrar nome da musica" hint={allowNull && inheritedFrom ? `Herdado: ${inheritedFrom.show_current_audio ? "Sim" : "Nao"}` : null}>
        <NullableToggle
          value={value.show_current_audio}
          onChange={update("show_current_audio")}
          allowNull={allowNull}
        />
      </Field>

      {/* Position */}
      <Field label="Posicao na tela" hint={allowNull && inheritedFrom ? `Herdado: ${POSITION_LABELS[inheritedFrom.position]}` : null}>
        <PositionPicker
          value={value.position}
          onChange={update("position")}
          allowNull={allowNull}
        />
      </Field>

      {/* Duration */}
      <Field label="Duracao (segundos)" hint="0 = sempre visivel">
        <NullableNumberInput
          value={value.duration_seconds}
          onChange={update("duration_seconds")}
          min={0}
          max={3600}
          allowNull={allowNull}
          inheritedValue={inheritedFrom?.duration_seconds}
        />
      </Field>

      {/* Opacity */}
      <Field label={`Opacidade do fundo: ${Math.round((value.opacity ?? inheritedFrom?.opacity ?? 0.6) * 100)}%`}>
        <NullableSlider
          value={value.opacity}
          onChange={update("opacity")}
          min={0}
          max={1}
          step={0.05}
          allowNull={allowNull}
          inheritedValue={inheritedFrom?.opacity}
        />
      </Field>

      {/* Font size */}
      <Field label="Tamanho da fonte">
        <select
          value={value.font_size ?? ""}
          onChange={(e) => update("font_size")(e.target.value || null)}
          className="..."
        >
          {allowNull && <option value="">Herdar ({inheritedFrom?.font_size || "medium"})</option>}
          <option value="small">Pequena</option>
          <option value="medium">Media</option>
          <option value="large">Grande</option>
        </select>
      </Field>
    </div>
  );
}

const POSITION_LABELS = {
  top_left: "Superior esquerdo",
  top_right: "Superior direito",
  bottom_left: "Inferior esquerdo",
  bottom_right: "Inferior direito",
};
```

## `PositionPicker.jsx` (subcomponente)

Visual de 4 quadrantes:

```javascript
function PositionPicker({ value, onChange, allowNull }) {
  return (
    <div className="grid grid-cols-2 gap-1 w-32 h-20 border rounded">
      {["top_left", "top_right", "bottom_left", "bottom_right"].map((pos) => (
        <button
          key={pos}
          type="button"
          onClick={() => onChange(pos)}
          className={`p-1 text-xs ${value === pos ? "bg-blue-500 text-white" : "bg-gray-100 hover:bg-gray-200"}`}
        >
          {pos === "top_left" && "↖"}
          {pos === "top_right" && "↗"}
          {pos === "bottom_left" && "↙"}
          {pos === "bottom_right" && "↘"}
        </button>
      ))}
      {allowNull && (
        <button
          type="button"
          onClick={() => onChange(null)}
          className="col-span-2 mt-1 text-xs text-gray-500 hover:underline"
        >
          Herdar do nivel superior
        </button>
      )}
    </div>
  );
}
```

## `OSDConfigPreview.jsx`

Mini-viewport 16:9 com overlay sample renderizado:

```javascript
export function OSDConfigPreview({ config }) {
  const posClass = {
    top_left: "top-2 left-2",
    top_right: "top-2 right-2",
    bottom_left: "bottom-2 left-2",
    bottom_right: "bottom-2 right-2",
  }[config.position] || "top-2 right-2";

  const fontClass = {
    small: "text-[10px]",
    medium: "text-xs",
    large: "text-sm",
  }[config.font_size] || "text-xs";

  return (
    <div className="relative w-full aspect-video bg-gradient-to-br from-gray-700 to-gray-900 rounded-lg overflow-hidden">
      {/* Fake content */}
      <div className="absolute inset-0 flex items-center justify-center text-gray-500 text-xs">
        [Visualizacao da TV]
      </div>

      {/* Overlay sample */}
      {config.show_current_audio && (
        <div
          className={`absolute ${posClass}`}
          style={{ opacity: 1 }}
        >
          <div
            className={`inline-flex items-center gap-1 rounded px-2 py-1 ${fontClass}`}
            style={{ backgroundColor: `rgba(0, 0, 0, ${config.opacity})` }}
          >
            <span className="text-white">♫</span>
            <span className="text-white truncate" style={{ maxWidth: "120px" }}>
              Nome da Musica Exemplo
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
```

## `DispositivoDetalhe.jsx`

Adicionar card "Overlay OSD":

```javascript
import { OSDConfigForm, OSDConfigPreview } from "../components/shared/...";

function DispositivoDetalhe() {
  const { data: device } = useQuery(["device", id], () => buscarDispositivo(id));
  const { data: tenant } = useQuery(["tenant", currentTenantId], () => buscarTenant(currentTenantId));

  const [localConfig, setLocalConfig] = useState(device?.osd_config_local || {});
  const effectiveConfig = mergeConfigs(localConfig, tenant?.osd_config); // device > tenant > default

  const saveMutation = useMutation((cfg) => atualizarOSDConfigDispositivo(id, cfg));

  return (
    <Card title="Overlay com nome da musica">
      <div className="grid grid-cols-2 gap-6">
        <OSDConfigForm
          value={localConfig}
          onChange={setLocalConfig}
          allowNull={true}
          inheritedFrom={tenant?.osd_config}
        />
        <div>
          <h4 className="text-sm font-medium mb-2">Preview</h4>
          <OSDConfigPreview config={effectiveConfig} />
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-4">
        <Button variant="outline" onClick={() => setLocalConfig({})}>
          Resetar para padrao da empresa
        </Button>
        <Button onClick={() => saveMutation.mutate(localConfig)} disabled={saveMutation.isLoading}>
          Salvar
        </Button>
      </div>
    </Card>
  );
}
```

## `ConfigEmpresa.jsx`

Similar mas sem `allowNull`:

```javascript
<Section title="Overlay de musica (padrao para todos os dispositivos)">
  <div className="grid grid-cols-2 gap-6">
    <OSDConfigForm
      value={tenantOSDConfig}
      onChange={setTenantOSDConfig}
      allowNull={false}
    />
    <div>
      <h4 className="text-sm font-medium mb-2">Preview</h4>
      <OSDConfigPreview config={tenantOSDConfig} />
    </div>
  </div>
  <Button onClick={() => saveMutation.mutate(tenantOSDConfig)}>
    Salvar e aplicar a todos os dispositivos
  </Button>
</Section>
```

## Card "Estado atual" em DispositivoDetalhe

Adicionar info da musica atualmente tocando:

```javascript
<Card title="Estado atual">
  <Row label="Online" value={device.last_seen_recent ? "Sim" : "Nao"} />
  <Row label="Campanha" value={device.current_campaign?.name || "—"} />
  <Row label="Midia atual" value={device.current_media_name || "—"} />
  <Row
    label="Tocando agora (musica)"
    value={
      device.current_audio_track_name
        ? `${device.current_audio_track_name} (ha ${formatElapsed(device.current_audio_track_started_at)})`
        : "—"
    }
  />
</Card>
```

`formatElapsed(ts)` → "15s", "1min 20s", etc.

## API clients

### `frontend/src/api/dispositivos.js`

```javascript
export async function atualizarOSDConfigDispositivo(deviceId, config) {
  const { data } = await http.patch(`/devices/${deviceId}/osd-config`, config);
  return data;
}
```

### `frontend/src/api/tenants.js`

```javascript
export async function atualizarOSDConfigEmpresa(tenantId, config) {
  const { data } = await http.patch(`/tenants/${tenantId}/osd-config`, config);
  return data;
}
```

## Feedback visual

- Toast "Configuracao salva. Aplicada em N dispositivos."
- Para tenant: "Aplicada em N dispositivos (que estavam usando configuracao padrao)."
- Para device: "Configuracao deste dispositivo atualizada."

## Estados de loading

- Botao "Salvar" desabilitado durante mutation.
- Preview atualiza em tempo real conforme operador mexe (sem precisar salvar).

## Acessibilidade

- Sliders com `aria-valuenow`, `aria-valuemin`, `aria-valuemax`.
- Selects com labels associados.
- PositionPicker com botoes acessiveis por teclado.

## Casos de uso

### Caso 1: Operador habilita overlay para toda empresa

- Vai em ConfigEmpresa → "Overlay de musica".
- Marca "Mostrar nome da musica".
- Escolhe posicao "Top right".
- Salva.
- Todos os dispositivos que nao tem config propria mostram overlay imediatamente.

### Caso 2: Operador customiza apenas uma TV

- Vai em DispositivoDetalhe da TV problematica.
- Em "Overlay OSD", muda posicao para "Bottom left" (porque top esquerdo tem reflexo na vitrine).
- Salva.
- Apenas essa TV usa nova posicao.

### Caso 3: Operador desabilita overlay em uma TV

- Marca "Mostrar nome da musica" como Nao (override do tenant).
- Salva.
- Apenas essa TV nao mostra overlay.

### Caso 4: Operador verifica musica tocando agora

- Abre DispositivoDetalhe.
- Card "Estado atual" mostra "Tocando agora: Nome (ha 25s)".
- Confirma visualmente que esta tocando a faixa correta.

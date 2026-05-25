import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const POSITIONS = [
  ["top_left", "Sup. esq."],
  ["top_right", "Sup. dir."],
  ["bottom_left", "Inf. esq."],
  ["bottom_right", "Inf. dir."],
];

const FONT_SIZES = [
  ["small", "Pequena"],
  ["medium", "Media"],
  ["large", "Grande"],
];

function Field({ label, children }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function NullableToggle({ value, onChange, allowNull, inheritedValue }) {
  const effective = value ?? inheritedValue ?? true;
  return (
    <div className="flex flex-wrap gap-2">
      <Button
        type="button"
        size="sm"
        variant={effective === true && value != null ? "default" : "outline"}
        onClick={() => onChange(true)}
      >
        Sim
      </Button>
      <Button
        type="button"
        size="sm"
        variant={effective === false && value != null ? "default" : "outline"}
        onClick={() => onChange(false)}
      >
        Nao
      </Button>
      {allowNull && (
        <Button
          type="button"
          size="sm"
          variant={value == null ? "secondary" : "outline"}
          onClick={() => onChange(null)}
        >
          Herdar
        </Button>
      )}
    </div>
  );
}

function PositionPicker({ value, onChange, allowNull, inheritedValue }) {
  return (
    <div className="space-y-2">
      <div className="grid w-44 grid-cols-2 gap-1 rounded-md border p-1">
        {POSITIONS.map(([pos, label]) => (
          <Button
            key={pos}
            type="button"
            size="sm"
            variant={(value ?? inheritedValue) === pos && value != null ? "default" : "outline"}
            className="h-9"
            onClick={() => onChange(pos)}
          >
            {label}
          </Button>
        ))}
      </div>
      {allowNull && (
        <Button
          type="button"
          size="sm"
          variant={value == null ? "secondary" : "outline"}
          onClick={() => onChange(null)}
        >
          Herdar posicao
        </Button>
      )}
    </div>
  );
}

function NullableNumberInput({ value, onChange, allowNull, inheritedValue }) {
  return (
    <div className="flex items-center gap-2">
      <Input
        type="number"
        min="0"
        max="3600"
        value={value ?? inheritedValue ?? 8}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-28"
      />
      {allowNull && (
        <Button
          type="button"
          size="sm"
          variant={value == null ? "secondary" : "outline"}
          onClick={() => onChange(null)}
        >
          Herdar
        </Button>
      )}
    </div>
  );
}

function NullableSlider({ value, onChange, allowNull, inheritedValue }) {
  const current = value ?? inheritedValue ?? 0.6;
  return (
    <div className="flex items-center gap-3">
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={current}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
      <span className="w-10 text-right text-xs text-muted-foreground">
        {Math.round(current * 100)}%
      </span>
      {allowNull && (
        <Button
          type="button"
          size="sm"
          variant={value == null ? "secondary" : "outline"}
          onClick={() => onChange(null)}
        >
          Herdar
        </Button>
      )}
    </div>
  );
}

export function OSDConfigForm({ value, onChange, allowNull = false, inheritedFrom = null }) {
  const update = (key) => (nextValue) => onChange({ ...value, [key]: nextValue });

  return (
    <div className="space-y-4">
      <Field label="Mostrar musica atual">
        <NullableToggle
          value={value.show_current_audio}
          inheritedValue={inheritedFrom?.show_current_audio}
          onChange={update("show_current_audio")}
          allowNull={allowNull}
        />
      </Field>

      <Field label="Posicao">
        <PositionPicker
          value={value.position}
          inheritedValue={inheritedFrom?.position}
          onChange={update("position")}
          allowNull={allowNull}
        />
      </Field>

      <Field label="Duracao em segundos">
        <NullableNumberInput
          value={value.duration_seconds}
          inheritedValue={inheritedFrom?.duration_seconds}
          onChange={update("duration_seconds")}
          allowNull={allowNull}
        />
      </Field>

      <Field label="Opacidade">
        <NullableSlider
          value={value.opacity}
          inheritedValue={inheritedFrom?.opacity}
          onChange={update("opacity")}
          allowNull={allowNull}
        />
      </Field>

      <Field label="Tamanho da fonte">
        <select
          value={value.font_size ?? ""}
          onChange={(e) => update("font_size")(e.target.value || null)}
          className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
        >
          {allowNull && <option value="">Herdar</option>}
          {FONT_SIZES.map(([size, label]) => (
            <option key={size} value={size}>
              {label}
            </option>
          ))}
        </select>
      </Field>
    </div>
  );
}

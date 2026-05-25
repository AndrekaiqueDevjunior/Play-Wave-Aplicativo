// @ts-nocheck
/**
 * AudioPolicySelector — SPEC 005: selector reutilizável de política de áudio.
 *
 * Props:
 *   value          — string | null (null = herda do nível superior)
 *   onChange       — (value: string | null) => void
 *   allowNull      — se true, mostra opção "Herdar do nível superior"
 *   inheritedLabel — texto mostrado quando value=null
 *   disabled       — boolean
 */

import React from "react";
import { AUDIO_POLICY_OPTIONS } from "@/utils/audioPolicy";
import { AlertTriangle } from "lucide-react";

export function AudioPolicySelector({
  value,
  onChange,
  allowNull = false,
  inheritedLabel = "Herdar do nível superior",
  disabled = false,
}) {
  const isNull = value === null || value === undefined;

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Política de áudio
      </label>
      <div className="space-y-1">
        {allowNull && (
          <RadioRow
            checked={isNull}
            onChange={() => onChange(null)}
            label={inheritedLabel}
            description="Usa a configuração definida no nível superior (campanha/empresa)"
            disabled={disabled}
            isInherit
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

      {value === "mix" && (
        <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 mt-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>
            Ambos os áudios tocam simultaneamente. Pode soar confuso.
            Recomendado apenas para casos específicos como vídeo instrumental
            sobre rádio ambiente.
          </span>
        </div>
      )}
    </div>
  );
}

function RadioRow({ checked, onChange, label, description, disabled, isInherit }) {
  return (
    <label
      className={[
        "flex gap-3 p-2 rounded-md cursor-pointer transition-colors",
        checked
          ? "bg-blue-50 border border-blue-200"
          : "hover:bg-gray-50 border border-transparent",
        disabled ? "opacity-50 cursor-not-allowed" : "",
        isInherit ? "border-dashed border-gray-300 hover:border-gray-400" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <input
        type="radio"
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className="mt-0.5 flex-shrink-0 accent-blue-600"
      />
      <div className="flex-1 min-w-0">
        <div className={`text-sm font-medium ${isInherit ? "text-gray-500" : ""}`}>
          {label}
        </div>
        {description && (
          <div className="text-xs text-gray-500 mt-0.5 leading-relaxed">
            {description}
          </div>
        )}
      </div>
    </label>
  );
}

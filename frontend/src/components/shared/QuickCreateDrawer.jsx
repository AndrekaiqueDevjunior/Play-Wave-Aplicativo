import React, { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

/**
 * QuickCreateDrawer — minimal right-side drawer for creating a named item.
 *
 * Props:
 *   open         – boolean
 *   onClose      – () => void
 *   title        – drawer title, e.g. "Nova Localização"
 *   description  – optional subtitle
 *   label        – label for the name field (default "Nome")
 *   placeholder  – placeholder for the name input
 *   initialValue – pre-fills the input (e.g. the search query)
 *   onSave       – (name: string) => Promise<void> | void
 *   extra        – optional additional JSX rendered below the name field
 */
export default function QuickCreateDrawer({
  open,
  onClose,
  title,
  description = undefined,
  label = "Nome",
  placeholder = "Digite um nome...",
  initialValue = "",
  onSave,
  extra = null,
}) {
  const [name, setName] = useState(initialValue);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setName(initialValue);
      setError("");
    }
  }, [open, initialValue]);

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Campo obrigatório.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await onSave(trimmed);
      onClose();
    } catch (err) {
      setError(err?.message || "Erro ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-[360px] flex flex-col p-0"
      >
        <SheetHeader className="px-6 pt-6 pb-4 border-b">
          <SheetTitle className="text-base">{title}</SheetTitle>
          {description && (
            <SheetDescription className="text-xs">
              {description}
            </SheetDescription>
          )}
        </SheetHeader>

        <form
          onSubmit={handleSubmit}
          className="flex flex-col flex-1 overflow-y-auto"
        >
          <div className="px-6 py-5 space-y-4 flex-1">
            <div className="space-y-1.5">
              <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {label}
              </Label>
              <Input
                autoFocus
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setError("");
                }}
                placeholder={placeholder}
              />
              {error && (
                <p className="text-xs text-destructive">{error}</p>
              )}
            </div>
            {extra}
          </div>

          <SheetFooter className="px-6 py-4 border-t bg-muted/30 flex-row gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={saving} className="flex-1">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Salvar
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}

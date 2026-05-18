import React, { useState, useRef, useEffect } from "react";
import { Check, ChevronsUpDown, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

/**
 * ComboSearch — Select with inline search + optional "Create new" action.
 *
 * Props:
 *   options      – [{ value, label }]
 *   value        – currently selected value (string)
 *   onChange     – (value: string) => void
 *   placeholder  – trigger placeholder text
 *   searchPlaceholder – input placeholder
 *   onCreate     – (rawText: string) => void | undefined   (enables + button)
 *   createLabel  – text shown in the "create" row
 *   disabled     – boolean
 *   className    – extra class for trigger
 */
export default function ComboSearch({
  options = [],
  value,
  onChange,
  placeholder = "Selecionar...",
  searchPlaceholder = "Buscar...",
  onCreate = undefined,
  onCreateClick = undefined,
  createLabel = "Criar novo",
  disabled = false,
  className = undefined,
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const filtered = options.filter((o) =>
    o.label.toLowerCase().includes(query.toLowerCase())
  );

  const selected = options.find((o) => o.value === value);

  const handleSelect = (v) => {
    onChange(v === value ? "" : v);
    setOpen(false);
  };

  const handleCreate = () => {
    const text = query.trim();
    if (!text) return;
    if (onCreateClick) {
      setOpen(false);
      onCreateClick(text);
    } else if (onCreate) {
      onCreate(text);
      setOpen(false);
    }
  };

  const hasCreateAction = onCreate || onCreateClick;
  const showCreate =
    hasCreateAction &&
    query.trim().length > 0 &&
    !options.some((o) => o.label.toLowerCase() === query.trim().toLowerCase());

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn(
            "w-full justify-between font-normal h-9 px-3 text-sm",
            !selected && "text-muted-foreground",
            className
          )}
        >
          <span className="truncate">{selected ? selected.label : placeholder}</span>
          <ChevronsUpDown className="ml-2 h-3.5 w-3.5 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="p-0 w-[var(--radix-popover-trigger-width)] min-w-[200px]"
        align="start"
        sideOffset={4}
      >
        <div className="flex items-center border-b px-2">
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={searchPlaceholder}
            className="border-0 h-8 text-sm focus-visible:ring-0 focus-visible:ring-offset-0 px-1"
          />
        </div>
        <div className="max-h-52 overflow-y-auto py-1">
          {filtered.length === 0 && !showCreate && (
            <p className="py-4 text-center text-xs text-muted-foreground">
              Nenhum resultado.
            </p>
          )}
          {filtered.map((o) => (
            <button
              key={o.value}
              type="button"
              onClick={() => handleSelect(o.value)}
              className={cn(
                "flex w-full items-center gap-2 px-3 py-1.5 text-sm hover:bg-accent cursor-pointer text-left",
                value === o.value && "font-medium"
              )}
            >
              <Check
                className={cn(
                  "h-3.5 w-3.5 shrink-0",
                  value === o.value ? "opacity-100 text-primary" : "opacity-0"
                )}
              />
              {o.label}
            </button>
          ))}
          {showCreate && (
            <button
              type="button"
              onClick={handleCreate}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-sm text-primary hover:bg-accent cursor-pointer font-medium border-t mt-1"
            >
              <Plus className="h-3.5 w-3.5 shrink-0" />
              {createLabel} &ldquo;{query.trim()}&rdquo;
            </button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}

import { useEffect, useRef, useState } from "react";
import { Search, Loader2 } from "lucide-react";
import { ingredientApi } from "../../api/ingredientApi";
import { FOOD_GROUP_LABELS } from "../../lib/labels";
import type { Ingredient } from "../../types";

interface IngredientPickerProps {
  onSelect: (ingredient: Ingredient) => void;
  placeholder?: string;
  label?: string;
}

export function IngredientPicker({ onSelect, placeholder = "Tìm nguyên liệu...", label }: IngredientPickerProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const term = query.trim();
    if (term.length < 1) {
      setResults([]);
      return;
    }
    let active = true;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const items = await ingredientApi.list({ search: term, limit: 8, active_only: true });
        if (active) {
          setResults(items);
          setOpen(true);
        }
      } catch {
        if (active) setResults([]);
      } finally {
        if (active) setLoading(false);
      }
    }, 350);
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [query]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const pick = (ing: Ingredient) => {
    onSelect(ing);
    setQuery("");
    setResults([]);
    setOpen(false);
  };

  return (
    <div className="relative" ref={boxRef}>
      {label && <label className="mb-1.5 block text-sm font-medium text-gray-700">{label}</label>}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder={placeholder}
          className="w-full rounded-xl border border-sand-200 bg-white py-2.5 pl-9 pr-9 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
        {loading && <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-gray-400" />}
      </div>
      {open && results.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-xl border border-sand-200 bg-white py-1 shadow-lg">
          {results.map((ing) => (
            <li key={ing.id}>
              <button
                type="button"
                onClick={() => pick(ing)}
                className="flex w-full items-center justify-between gap-2 px-3.5 py-2 text-left text-sm hover:bg-brand-50"
              >
                <span className="font-medium text-gray-800">{ing.name}</span>
                <span className="shrink-0 text-xs text-gray-500">{FOOD_GROUP_LABELS[ing.food_group]}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {open && !loading && query.trim() && results.length === 0 && (
        <div className="absolute z-20 mt-1 w-full rounded-xl border border-sand-200 bg-white px-3.5 py-2.5 text-sm text-gray-500 shadow-lg">
          Không tìm thấy nguyên liệu phù hợp.
        </div>
      )}
    </div>
  );
}

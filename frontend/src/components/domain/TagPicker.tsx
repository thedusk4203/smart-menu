import { useEffect, useMemo, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import type { Tag } from "../../api/tagApi";

interface TagPickerProps {
  tags: Tag[];
  selected: string[];
  onChange: (names: string[]) => void;
  label?: string;
}

export function TagPicker({ tags, selected, onChange, label = "Thẻ ưu tiên (tuỳ chọn)" }: TagPickerProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const results = useMemo(() => tags.filter((tag) => !selected.includes(tag.name) && tag.name.toLocaleLowerCase("vi").includes(query.trim().toLocaleLowerCase("vi"))).slice(0, 8), [query, selected, tags]);

  useEffect(() => {
    const close = (event: MouseEvent) => { if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const add = (name: string) => { onChange([...selected, name]); setQuery(""); setOpen(false); };
  return <div ref={ref} className="relative"><label className="mb-1.5 block text-sm font-medium text-gray-700">{label}</label><div className="rounded-xl border border-sand-200 bg-white p-2 focus-within:ring-2 focus-within:ring-brand-400"><div className="flex flex-wrap gap-1.5">{selected.map((name) => <span key={name} className="inline-flex items-center gap-1 rounded-lg bg-brand-100 px-2 py-1 text-xs font-medium text-brand-800">#{name}<button type="button" onClick={() => onChange(selected.filter((tag) => tag !== name))} className="rounded text-brand-700 hover:bg-brand-200" aria-label={`Bỏ thẻ ${name}`}><X className="h-3.5 w-3.5" /></button></span>)}<div className="relative min-w-40 flex-1"><Search className="pointer-events-none absolute left-1 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" /><input value={query} onFocus={() => setOpen(true)} onChange={(event) => { setQuery(event.target.value); setOpen(true); }} placeholder={selected.length ? "Tìm thêm thẻ..." : "Tìm thẻ..."} className="w-full bg-transparent py-1 pl-6 text-sm outline-none placeholder:text-gray-400" /></div></div></div>{open && query.trim() && <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-sand-200 bg-white py-1 shadow-lg">{results.length ? <ul>{results.map((tag) => <li key={tag.id}><button type="button" onClick={() => add(tag.name)} className="w-full px-3.5 py-2 text-left text-sm font-medium text-gray-800 hover:bg-brand-50">#{tag.name}</button></li>)}</ul> : <p className="px-3.5 py-2.5 text-sm text-gray-500">Không tìm thấy thẻ phù hợp.</p>}</div>}<p className="mt-1.5 text-xs text-gray-500">Chỉ chọn thẻ đã được quản trị viên tạo.</p></div>;
}

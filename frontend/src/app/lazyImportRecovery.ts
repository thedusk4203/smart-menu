const DYNAMIC_IMPORT_PATTERNS = [
  "failed to fetch dynamically imported module",
  "error loading dynamically imported module",
  "importing a module script failed",
];

export function isDynamicImportError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error ?? "");
  const normalized = message.toLowerCase();
  return DYNAMIC_IMPORT_PATTERNS.some((pattern) => normalized.includes(pattern));
}

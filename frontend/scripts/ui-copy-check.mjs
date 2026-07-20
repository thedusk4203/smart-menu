import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const targets = [resolve(root, "src/pages"), resolve(root, "src/components/domain")];
const forbidden = [
  /\bBMR\b/,
  /\bTDEE\b/,
  /\bmacro\b/i,
  /\bplanner\b/i,
  /\bsolver\b/i,
  /\bRetry\b/,
  /\bV3\b/,
];

async function sourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(async (entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "admin") return [];
      return sourceFiles(path);
    }
    return [".ts", ".tsx"].includes(extname(entry.name)) ? [path] : [];
  }));
  return nested.flat();
}

for (const target of targets) {
  for (const file of await sourceFiles(target)) {
    const content = await readFile(file, "utf8");
    for (const pattern of forbidden) {
      if (pattern.test(content)) {
        throw new Error(`${relative(root, file)} chứa thuật ngữ kỹ thuật dành cho UI người dùng: ${pattern}`);
      }
    }
  }
}

console.log("UI copy check passed.");

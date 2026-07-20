import { readFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const files = [
  ["src/pages/auth/Login.tsx", ["Điền nhanh tài khoản demo", "admin@demo.com", "admin123"]],
  ["src/pages/ai/Assistant.tsx", ["Đang kết nối", "nhật ký vận hành được giữ tối đa 30 ngày", "provider_name"]],
];

for (const [file, forbidden] of files) {
  const content = await readFile(resolve(root, file), "utf8");
  for (const text of forbidden) {
    if (content.includes(text)) {
      throw new Error(`${file} vẫn chứa nội dung không được phát hành: ${text}`);
    }
  }
}

execFileSync(process.execPath, [resolve(root, "scripts/ui-copy-check.mjs")], { stdio: "inherit" });

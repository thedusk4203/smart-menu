# Smart Menu Frontend

React/TypeScript frontend chạy Vite local ở port `5173`; `/api` proxy tới backend `127.0.0.1:8001`.

```powershell
npm install
npm run dev
npm run build
npm run lint
npm run check:release
```

Route ở `src/app/router.tsx`, page ở `src/pages/`, contract HTTP ở `src/api/` và low-level client ở `src/lib/apiClient.ts`. Đọc [frontend handbook](../docs/code/frontend.md), [API reference](../docs/code/api/README.md) và [maintenance workflow](../docs/code/maintenance.md) trước khi thêm page hoặc sửa contract.

# Frontend (Vue Vben Admin - Single Admin Setup)

## Overview

This frontend is bootstrapped from [vue-vben-admin](https://github.com/vbenjs/vue-vben-admin) and trimmed for a single administrator experience. The codebase keeps the Naive UI implementation only and removes alternative UI variants, playgrounds, and documentation assets to stay focused on our use case.

## Project layout

- `apps/web-naive`: Main SPA entry (Naive UI powered admin console).
- `packages/*`: Shared Vben workspace packages referenced by the app.
- `scripts/*`: Utility scripts retained from the upstream monorepo.

## Getting started

```bash
cd frontend
# Ensure pnpm is available (Node 20+ is recommended by upstream)
corepack enable
pnpm install

# Local development (single admin app)
pnpm dev

# Type check & lint
pnpm typecheck
pnpm lint

# Production build
pnpm build
```

## Notes

- Non-essential applications (`web-antd`, `web-ele`, `web-tdesign`, `backend-mock`) and auxiliary content (`docs`, `playground`, localized READMEs) were removed to keep the workspace lean.
- Scripts in `package.json` now target only the Naive UI admin to match the single-admin requirement.

## License

MIT (inherited from vue-vben-admin).

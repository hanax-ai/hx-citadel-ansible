
citadel-shield-ui/
├── README.md
├── FEATURES_README.md
├── FIORI_README.md
├── package.json
├── package-lock.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── eslint.config.js
├── components.json
├── .env
├── .gitignore
├── bun.lockb
│
├── public/
│   ├── favicon.ico
│   ├── placeholder.svg
│   └── robots.txt
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── App.css
│   ├── index.css
│   ├── vite-env.d.ts
│   │
│   ├── a11y/
│   │   └── aria-live.ts
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── AsyncButton.tsx
│   │   │   ├── ProgressSteps.tsx
│   │   │   └── Spinner.tsx
│   │   │
│   │   ├── fiori/
│   │   │   ├── EmptyState.tsx
│   │   │   ├── KPICard.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── MessagePopover.tsx
│   │   │   ├── MessageStrip.tsx
│   │   │   ├── ShellBar.tsx
│   │   │   ├── SideNav.tsx
│   │   │   └── StatusBadge.tsx
│   │   │
│   │   └── ui/
│   │       ├── accordion.tsx
│   │       ├── alert-dialog.tsx
│   │       ├── alert.tsx
│   │       ├── aspect-ratio.tsx
│   │       ├── avatar.tsx
│   │       ├── badge.tsx
│   │       ├── breadcrumb.tsx
│   │       ├── button.tsx
│   │       ├── calendar.tsx
│   │       ├── card.tsx
│   │       ├── carousel.tsx
│   │       ├── chart.tsx
│   │       ├── checkbox.tsx
│   │       ├── collapsible.tsx
│   │       ├── command.tsx
│   │       ├── context-menu.tsx
│   │       ├── dialog.tsx
│   │       ├── drawer.tsx
│   │       ├── dropdown-menu.tsx
│   │       ├── form.tsx
│   │       ├── hover-card.tsx
│   │       ├── input-otp.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── menubar.tsx
│   │       ├── navigation-menu.tsx
│   │       ├── pagination.tsx
│   │       ├── popover.tsx
│   │       ├── progress.tsx
│   │       ├── radio-group.tsx
│   │       ├── resizable.tsx
│   │       ├── scroll-area.tsx
│   │       ├── select.tsx
│   │       ├── separator.tsx
│   │       ├── sheet.tsx
│   │       ├── sidebar.tsx
│   │       ├── skeleton.tsx
│   │       ├── slider.tsx
│   │       ├── sonner.tsx
│   │       ├── switch.tsx
│   │       ├── table.tsx
│   │       ├── tabs.tsx
│   │       ├── textarea.tsx
│   │       ├── toast.tsx
│   │       ├── toaster.tsx
│   │       ├── toggle-group.tsx
│   │       ├── toggle.tsx
│   │       ├── tooltip.tsx
│   │       └── use-toast.ts
│   │
│   ├── hooks/
│   │   ├── use-agui-stream.ts
│   │   ├── use-aria-modal.ts
│   │   ├── use-focus-trap.ts
│   │   ├── use-inkbar.ts
│   │   ├── use-mobile.tsx
│   │   ├── use-roving.ts
│   │   └── use-toast.ts
│   │
│   ├── integrations/
│   │   └── supabase/
│   │       ├── client.ts
│   │       └── types.ts
│   │
│   ├── lib/
│   │   ├── utils.ts
│   │   └── telemetry.ts
│   │
│   ├── pages/
│   │   ├── Index.tsx
│   │   ├── Admin.tsx
│   │   ├── Audit.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Graph.tsx
│   │   ├── Ingest.tsx
│   │   ├── Jobs.tsx
│   │   ├── NotFound.tsx
│   │   └── Queries.tsx
│   │
│   ├── services/
│   │   └── mockData.ts
│   │
│   └── types/
│       ├── index.ts
│       └── agui.ts
│
└── supabase/
    ├── config.toml
    │
    └── functions/
        ├── deno.json
        │
        ├── agents-crawl/
        │   └── index.ts
        │
        └── agents-query/
            └── index.ts
citadel-shield-ui/
├── README.md
├── FEATURES_README.md
├── FIORI_README.md
├── package.json
├── package-lock.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── eslint.config.js
├── components.json
├── .env
├── .gitignore
├── bun.lockb
│
├── public/
│   ├── favicon.ico
│   ├── placeholder.svg
│   └── robots.txt
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── App.css
│   ├── index.css
│   ├── vite-env.d.ts
│   │
│   ├── a11y/
│   │   └── aria-live.ts
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── AsyncButton.tsx
│   │   │   ├── ProgressSteps.tsx
│   │   │   └── Spinner.tsx
│   │   │
│   │   ├── fiori/
│   │   │   ├── EmptyState.tsx
│   │   │   ├── KPICard.tsx
│   │   │   ├── Layout.tsx
│   │   │   ├── MessagePopover.tsx
│   │   │   ├── MessageStrip.tsx
│   │   │   ├── ShellBar.tsx
│   │   │   ├── SideNav.tsx
│   │   │   └── StatusBadge.tsx
│   │   │
│   │   └── ui/
│   │       ├── accordion.tsx
│   │       ├── alert-dialog.tsx
│   │       ├── alert.tsx
│   │       ├── aspect-ratio.tsx
│   │       ├── avatar.tsx
│   │       ├── badge.tsx
│   │       ├── breadcrumb.tsx
│   │       ├── button.tsx
│   │       ├── calendar.tsx
│   │       ├── card.tsx
│   │       ├── carousel.tsx
│   │       ├── chart.tsx
│   │       ├── checkbox.tsx
│   │       ├── collapsible.tsx
│   │       ├── command.tsx
│   │       ├── context-menu.tsx
│   │       ├── dialog.tsx
│   │       ├── drawer.tsx
│   │       ├── dropdown-menu.tsx
│   │       ├── form.tsx
│   │       ├── hover-card.tsx
│   │       ├── input-otp.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── menubar.tsx
│   │       ├── navigation-menu.tsx
│   │       ├── pagination.tsx
│   │       ├── popover.tsx
│   │       ├── progress.tsx
│   │       ├── radio-group.tsx
│   │       ├── resizable.tsx
│   │       ├── scroll-area.tsx
│   │       ├── select.tsx
│   │       ├── separator.tsx
│   │       ├── sheet.tsx
│   │       ├── sidebar.tsx
│   │       ├── skeleton.tsx
│   │       ├── slider.tsx
│   │       ├── sonner.tsx
│   │       ├── switch.tsx
│   │       ├── table.tsx
│   │       ├── tabs.tsx
│   │       ├── textarea.tsx
│   │       ├── toast.tsx
│   │       ├── toaster.tsx
│   │       ├── toggle-group.tsx
│   │       ├── toggle.tsx
│   │       ├── tooltip.tsx
│   │       └── use-toast.ts
│   │
│   ├── hooks/
│   │   ├── use-agui-stream.ts
│   │   ├── use-aria-modal.ts
│   │   ├── use-focus-trap.ts
│   │   ├── use-inkbar.ts
│   │   ├── use-mobile.tsx
│   │   ├── use-roving.ts
│   │   └── use-toast.ts
│   │
│   ├── integrations/
│   │   └── supabase/
│   │       ├── client.ts
│   │       └── types.ts
│   │
│   ├── lib/
│   │   ├── utils.ts
│   │   └── telemetry.ts
│   │
│   ├── pages/
│   │   ├── Index.tsx
│   │   ├── Admin.tsx
│   │   ├── Audit.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Graph.tsx
│   │   ├── Ingest.tsx
│   │   ├── Jobs.tsx
│   │   ├── NotFound.tsx
│   │   └── Queries.tsx
│   │
│   ├── services/
│   │   └── mockData.ts
│   │
│   └── types/
│       ├── index.ts
│       └── agui.ts
│
└── supabase/
    ├── config.toml
    │
    └── functions/
        ├── deno.json
        │
        ├── agents-crawl/
        │   └── index.ts
        │
        └── agents-query/
            └── index.ts

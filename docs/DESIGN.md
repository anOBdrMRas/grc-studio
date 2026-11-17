# Design — the web interface

This document describes the layout of the Resource Planner web interface (`src/ui/planner_ui`) as a
reusable blueprint: which parts exist, the rules they follow, and the exact wiring between them. It
is written so that a reader who has never seen this repository — a human or an AI agent — can
rebuild an interface with the same shape in another project without reading this codebase. The
document describes the interface only; the system around it is in [`docs/architecture.md`](docs/architecture.md).

---

## The contract

These rules hold everywhere in the interface. An interface that breaks one of them is not this
design.

1. **Server-rendered HTML.** Jinja2 templates render pages and fragments. Dynamic behaviour is
   HTMX swapping fragments in; the page script only reacts to `data-*` attributes and to events the
   server triggers. There is no client-side rendering of data, no client-side routing, no client
   template language.
2. **Strict CSP by construction.** No inline script, no `eval`, no remote asset, no CDN. Every
   script, style sheet, font and image is served by the interface's own origin. The one concession
   is `style-src-attr 'unsafe-inline'`: colours of objects are data and travel as `style="…"`
   attributes (see *Interactivity model* for the full policy).
3. **A pure client.** The interface calls the HTTP API with the signed-in user's session cookie and
   CSRF token. It has no database access and never recomputes a figure the API returns; every
   number shown is a number the API produced.
4. **Class names are literal.** Every CSS class appears written out in full in the templates or in
   `static/js/*.js`; none is assembled from parts at run time. The stylesheet build keeps what it
   can find (see *Asset pipeline*).
5. **One theme switcher, one sidebar switcher.** Both states live on the `<html>` element
   (`data-theme`, `data-sidebar`) and are set before the first paint by a small blocking script
   (`js/init.js`), so the page never flickers or snaps.
6. **Colour is never the only carrier of meaning.** State comes with text or an icon; drop targets
   are marked by a dashed frame (a shape) and the rest is dimmed, not recoloured.
7. **Every text goes through `_()`** — the gettext wrapper — when it is written and has a German
   catalogue entry. English is the source language: the message id is the English text.
8. **Keyboard and screen readers work.** The board, the dialogs and every list page are operable
   without a mouse; see *Accessibility floor*.

---

## Stack

| Layer | Choice | Why |
|---|---|---|
| Server framework | FastAPI | Renders HTML, serves static files, one security-header middleware |
| Templates | Jinja2, `StrictUndefined`, `autoescape`, `jinja2.ext.i18n` | Missing context fails loudly; escaping on by default |
| Partial updates | HTMX 2 | Fragments in, forms out; no client state to mirror |
| Small local state | Alpine.js, **CSP build** | Components by name; no expressions in markup |
| Drag and drop | SortableJS | Pointer and touch events, `forceFallback` |
| Styling | Tailwind CSS 3 + daisyUI 4, two custom themes | Utilities in the markup, components from daisyUI, tokens in themes |
| Fonts | Manrope (brand), IBM Plex Sans (body), vendored `.woff2` | No Google Fonts, no runtime font loading |
| Icons | Tabler outline icons, vendored per icon, inlined as SVG | Take the text colour, no request, no CSP exception |
| Dates and numbers | Babel | Locale-aware formats in template filters |
| Translations | gettext `.po` catalogues, compiled in memory at start | No binary files in the repository, no build step |

All browser libraries are **vendored at build time** from npm (build tooling only; the running
process needs no Node and no network). Their versions are pinned in `src/ui/package.json`.

---

## File map

```
src/ui/
  package.json                        build-time dependencies only
  tailwind.config.js                  daisyUI themes, brand fonts        [brand layer: verbatim]
  tailwind.brand.css                  fonts, logo, color-scheme         [brand layer: verbatim]
  tailwind.app.css                    app shell rules (sidebar, focus…)  [adapt per project]
  scripts/build-css.mjs               brand + app → static/app.css
  scripts/vendor.mjs                  npm → static/vendor, static/fonts, icons/
  planner_ui/
    main.py                           app factory, CSP middleware, error handlers
    templating.py                     Jinja environment, render(), toast()/trigger()
    nav.py                            navigation model, permission filtering
    i18n.py, texts.py                 .po catalogues; error-code texts
    icons.py                          inline SVG icon helper
    session.py                        UiContext: principal, permissions, CSRF token
    security.py                       security headers, the CSP string
    resources.py, crud.py, schema_form.py    generic list/form/page machinery
    routes/                           one module per area (pages, planning, admin, …)
    templates/                        see Template hierarchy
    icons/<name>.svg                  the icon subset, committed
    static/
      favicon.svg
      js/init.js                      pre-paint: theme and sidebar state
      js/app.js                       all page behaviour (one IIFE)
      app.css                         [generated by the build, not committed]
      vendor/*.min.js                 [generated: htmx, alpine-csp, sortable + licences]
      fonts/files/*.woff2             [generated: the six font files]
    locale/messages.pot               template catalogue
    locale/de/LC_MESSAGES/messages.po the German translations
```

Bracketed `[generated]` paths are gitignored; the image build and `npm run build` recreate them.
`[brand layer: verbatim]` files carry the stamp comment `fidonis-brand: 2` and are shared
byte-identical with the other interfaces of the same brand; a change to one belongs in the same
revision of all of them, bumping the stamp together.

---

## Asset pipeline

Two build steps, run with `npm run build` (or `npm run watch` for the style sheet while developing):

- **`scripts/vendor.mjs`** copies a fixed list out of `node_modules` into the package:
  `htmx.min.js`, `alpine-csp.min.js`, `sortable.min.js` into `static/vendor/`; six `.woff2` fonts
  (Manrope latin 500/700/800, IBM Plex Sans latin 400/500/600) into `static/fonts/files/`; every
  used Tabler outline icon into `planner_ui/icons/<name>.svg`; the licences into
  `static/vendor/licenses/` (they feed `THIRD_PARTY_LICENSES.md`).
- **`scripts/build-css.mjs`** concatenates `tailwind.brand.css` and `tailwind.app.css` (Tailwind
  takes one input; the `@tailwind` directives lead), runs the Tailwind CLI and writes the minified
  result to `static/app.css`.

Class scanning: the CLI is called with `--content planner_ui/templates/**/*.html,
planner_ui/static/js/*.js`. Everything the scanner must see is a literal string in those files.
Two consequences, both deliberate:

- Tailwind **utilities** that never appear literally do not exist in the build. That is why macros
  carry their variant classes written out (an `alert alert-warning` in a template, not
  `alert alert- + kind` in a script). daisyUI's **component** classes (`btn`, `alert`, `modal`,
  `table`, `badge`, `menu`, `join`, `toast`, `dropdown`, `progress`, …) are always present in the
  build, but the project writes them literally anyway.
- Rules that hang off data attributes the scanner cannot see (`[data-sidebar]`, `#board[data-dragging]`,
  `:focus-visible`) are kept **outside** any `@layer` in `tailwind.app.css`, so the purge cannot
  strip them.

Static files are served with a version fingerprint: `asset_url("app.css")` produces
`/static/app.css?v=<10 hex>` (a hash of the file), so caches can be aggressive for `/static/` while
every page ships with `Cache-Control: no-store`.

---

## Template hierarchy

```
layout.html        the HTML skeleton: <head>, meta, scripts, <body> frame
  ├── base.html    the application shell (sidebar, header, toasts, modal)
  │     └── <area>/index.html      full pages
  └── bare.html    a centred card (sign-in, first password, error page)
        └── login.html, change_password.html, error.html
macros.html        shared pieces (brand mark, theme toggle, form fields, pager, badges, …)
<area>/_*.html      fragments: parts swapped in by HTMX, included by the pages
crud/_*.html       generic fragments for edit, delete, import, one-time secrets
```

Blocks a page can fill: `title` (page title plus `" · "`), `page_title`, `page_subtitle`,
`page_actions` (the row of buttons in the header), `content`, `head_scripts` (page-only scripts,
e.g. Sortable on the board), `body_attrs`.

**Canonical ids that the script and the templates agree on — keep them when porting:**

| Id | What it is |
|---|---|
| `#list` | the row area of a list page (filter forms and dialogs swap here) |
| `#board` | the planning board area (a drop redraws it) |
| `#modal`, `#modal-body` | the one shared `<dialog>` and its content |
| `#toasts` | the container alerts are appended to |

The shell (`base.html`) sets `body_attrs` so every HTMX request of a shell page carries the CSRF
token:

```jinja
{% block body_attrs %} hx-headers='{{ {"X-CSRF-Token": csrf_token}|tojson }}'{% endblock %}
```

and `<body>` carries translated strings the script needs, as data attributes
(`data-msg-unreachable`, `data-msg-copied`) — the script itself holds no text of its own.

Every page is rendered through one helper (`templating.render`) with the context: `request`,
`path`, `me` (the signed-in principal), `csrf_token`, `can(permission)` (a boolean test) and
`nav_groups`. The navigation is data, not markup: `nav.py` holds `NavItem`s
(`href`, `icon`, `label` message id, `permission`, `group`); groups whose items the user lacks a
permission for vanish; the active row is `path == href or path.startswith(href + "/")` and gets
`aria-current="page"`.

---

## The application shell (`base.html`)

Side by side on the page:

- **`aside.app-sidebar`**, fixed, `w-64` (16 rem): brand mark + name; grouped navigation; and at the
  bottom: the collapse toggle, the theme toggle, and the account dropdown (language picker, your
  account, change password, sign out).
- **`.app-main`**, `ml-64`: a sticky `header` (page title, optional subtitle, `page_actions`
  buttons) and `main`, both capped at `max-w-[1680px]`.

Header button grammar: secondary actions are `btn btn-ghost btn-sm` with an icon, the one
creating action is `btn btn-primary btn-sm`. Nothing else is filled.

**Sidebar states** on `<html data-sidebar>`:

| State | Meaning | Geometry |
|---|---|---|
| `pinned` | full panel, pushes the content (default) | width/margin from the `w-64`/`ml-64` utilities |
| `collapsed` | icon rail (4 rem); hovering peeks the panel over the content | `--sidebar-rail: 4rem` |
| `open` | transient drawer, below `lg` only | `--sidebar-w: 16rem` as an overlay |

Rules: only `pinned` and `collapsed` are persisted (localStorage key `rp-sidebar`), so a phone
session never overwrites the desktop choice; below `lg` the rail is forced; the collapse animation
is `0.2s ease` on width and margin, and labels are `display: none` before it starts so rows never
reflow. The expanded geometry lives in the markup utilities, the deviations in CSS — if `app.css`
is missing the page still lays out expanded instead of dropping content under a shrunk panel.

The peek needs a separation the dark background cannot give a shadow alone, so the dark theme
separates it with a hairline + shadow (`--sidebar-peek-shadow`).

---

## Theming

Two daisyUI themes, `fidonis-light` (default) and `fidonis-dark` (`prefersdark: true`), defined in
`tailwind.config.js`. `<html data-theme="fidonis-light|fidonis-dark">` switches them;
`js/init.js` sets it **before the first paint** from localStorage (`rp-theme`), falling back to
`prefers-color-scheme`. `<meta name="theme-color">` is declared per scheme (#ffffff / #101214).

**Surface contract — the grounding rule of all colour decisions** (and the opposite of daisyUI's
own convention, on purpose):

| Token | Meaning |
|---|---|
| `base-100` | raised surface: cards, the modal, inputs, the header, the sidebar |
| `base-200` | page ground: `<body>` |
| `base-300` | borders and hover ground |

**One meaning per accent role — a colour is never decoration:**

| Role | Meaning |
|---|---|
| `primary` | the filled action; at most one solid button per page |
| `secondary` | navigation, links, focus, "you are here" (tinted row `bg-secondary/15`) |
| `accent` | "update available" and the brand gold of the logo |
| `info` / `success` / `warning` / `error` | state, and nothing else |

`primary` and `secondary` are both blue in the dark theme; they are told apart by form, not hue
(filled is an action, tinted is navigation). The state colours are tuned to clear WCAG AA
(4.5:1) against `base-100` and `base-200`, where they actually appear. Radii: `--rounded-box`
0.75 rem, `--rounded-btn` 0.5 rem. Typography: Manrope for headings and `.font-brand`, IBM Plex
Sans for everything else.

Tokens of the two themes (the values, for rebuilding elsewhere):

| Token | light | dark |
|---|---|---|
| `primary` | `#0a2f4d` | `#2b6fa8` |
| `secondary` | `#1b5e8c` | `#4ba5dd` |
| `accent` | `#c8972a` | `#d1a33c` |
| `base-100` / `-200` / `-300` | `#ffffff` / `#f3f5f7` / `#e0e5ea` | `#17191c` / `#101214` / `#272c32` |
| `base-content` | `#0b0e12` | `#eef1f4` |
| `info` / `success` / `warning` / `error` | `#1b6f9e` / `#0d724e` / `#8a6014` / `#c53c3c` | `#4ba5dd` / `#46c98a` / `#e0a63a` / `#ef6a6a` |

Long values split across two columns only to stay readable; rebuild the table in whatever shape
fits the target project, but keep the *values* — they are tuned for contrast against `base-100`
and `base-200`, not picked for taste.

The brand mark is inline SVG in `macros.html`: one gold square (fixed colour) and three navy
squares (`.brand-mark-ink`, retinted to light blue-gray in the dark theme so the mark stays legible
on graphite).

Surfaces carry **borders, not shadows** — cards are `rounded-box border border-base-300 bg-base-100`
on a `bg-base-200` body. Shadows are restricted to overlays (the peeked sidebar, the dialog, toasts,
the drag ghost).

---

## Interactivity model

Three moving parts, in load order: `js/init.js` (blocking, sets `data-theme` and `data-sidebar`
before the first paint), then `htmx.min.js`, `alpine-csp.min.js` and `js/app.js` (all `defer`).
A page needing Sortable loads `vendor/sortable.min.js` through its `head_scripts` block.

**htmx is configured for the CSP and for this design's answers** (the `htmx-config` meta tag):

```json
{"allowEval":false,"allowScriptTags":false,"includeIndicatorStyles":false,
 "selfRequestsOnly":true,"historyCacheSize":0,
 "responseHandling":[
   {"code":"204","swap":false},
   {"code":"[23]..","swap":true},
   {"code":"^(409|412|422|428)$","swap":true,"error":false},
   {"code":"[45]..","swap":false,"error":true}]}
```

That is: never eval, never injected scripts, only same-origin requests, no history cache, no
indicator styles (the page defines its own). `204` swaps nothing (a successful small change);
conflict and validation codes (`409`, `412`, `422`, `428`) are swapped **as content without erroring**
— the server answers with the form again, errors next to the fields or a stale-version banner in
it; everything else swaps nothing and raises the error path.

**The page script (`js/app.js`) is one IIFE.** It holds no text (translations come from `data-`
attributes), no state store and no framework; it wires three kinds of hooks:

1. `data-action` buttons, by delegated clicks:

   | `data-action` | Effect |
   |---|---|
   | `toggle-sidebar` | pinned ⇄ collapsed; below `lg`: collapsed ⇄ open |
   | `toggle-theme` | light ⇄ dark; syncs every toggle's icon, label and `aria-pressed` |
   | `close-modal` | closes the dialog |
   | `back` | `window.history.back()` |
   | `copy-secret` | selects and copies the input named by `data-copy-from`, then a toast |
   | `toggle-details` | shows/hides the row named by `aria-controls`, tracking `aria-expanded` |
   | `remove-row` | drops the closest `[data-row]` (a repeating form row) |

2. Attribute-driven behaviours: fields that exist only while another input has a value
   (`data-show-when` / `data-show-value`, applied on load, on change and on `htmx:load`); a search
   box filtering check boxes (`data-filter-choices` + `aria-controls`).

3. Server-triggered events, sent by the `HX-Trigger` response header (`templating.trigger()` and
   `templating.toast()` add it):

   | Event | Payload | The script's reaction |
   |---|---|---|
   | `toast` | `{kind: "success"|"error"|"warning"|"info", message}` | append an `alert alert-<kind>` to `#toasts` |
   | `modalClose` | — | close the dialog |
   | `refreshList` | — | refetch `#list` (the dialog stays open, e.g. while showing a secret) |

   The toast alert carries `role="alert"` for error and warning, else `role="status"`, and stays
   10 s for errors, otherwise 5 s.

**Modal lifecycle.** Buttons open it with `hx-get="…/new" hx-target="#modal-body" hx-swap="innerHTML"`;
on `htmx:afterSwap` into `#modal-body` the script calls `showModal()` and focuses the first
`[autofocus]`/input/select/textarea inside — unless the answer carried `HX-Reswap: none` (nothing
was swapped, the dialog may already have been closed by its own `modalClose`). On `close`, the
script empties `#modal-body`. The dialog is a native `<dialog class="modal" aria-modal="true">`
with a `method="dialog"` backdrop form labelled *Close*; CSS hides a closed `dialog.modal`
entirely (`display: none`) because daisyUI would otherwise keep its invisible grid reachable by Tab.

**Errors** are decided in one place, by the framework exception handlers (`main.py`):

| Situation | Fragment request | Full page |
|---|---|---|
| not signed in (`401`) | `HX-Redirect` to `/login?next=<current>` | redirect to `/login` |
| API problem, conflict, validation | status code + `toast` trigger + `HX-Reswap: none` | `error.html` with the message |
| API unreachable (`sendError`/`timeout`) | a toast from `data-msg-unreachable` | `error.html` |

**Alpine (CSP build)** is for small, named components only; the build forbids expressions in
markup, so components are registered in `app.js` on `alpine:init` (`Alpine.data("ownChoice")`,
`Alpine.data("colorField")`) and used as `x-data="colorField"` with `x-ref`s. If a behaviour needs
more than a few properties, it is server-driven HTMX instead.

**Drag and drop (the board)** stands for the pattern "a gesture is only a request": Sortable's
`onEnd` never changes data itself — it sends the request (`htmx.ajax`), the server books it and
answers with the board drawn again; the fragment replaces `#board` (`outerHTML`). Valid drop
targets are computed from `data-skills` on each cell and marked `data-target="valid|invalid"` while
dragging (`aria-busy` on the board during the request); a failed or lost request leads to a
redraw, never to a client-side patch of the moved row.

---

## A standard list page

The recipe every area follows (`tasks/`, `teams/`, `members/`, `skills/`, `absences/`, …),
portable as-is:

1. `templates/<area>/index.html` extends `base.html`; fills `title`, `page_title`,
   `page_actions` (ghost buttons for secondary actions, one `btn-primary` for *New …*; the primary
   one only behind `can("…:write")`).
2. A filter form (`role="search"`) above the list: `hx-get` to itself, `hx-target="#list"`,
   `hx-swap="outerHTML"`, `hx-trigger="input delay:300ms, change, submit"`, `hx-push-url="true"` —
   so typing, selecting and pressing enter all update the list, the URL always matches the view,
   and following the URL without JavaScript works too. Controls: the `search_input` macro plus
   `select select-bordered` filters with an "all" empty option.
3. `{% include "<area>/_list.html" %}` — the fragment. Its root is `<div id="list">`, so every
   swap replaces the whole fragment (list + pager + empty state) and the id survives.
4. The list: `<div class="overflow-x-auto rounded-box border border-base-300 bg-base-100">`
   around a daisyUI `table`. Columns that do not fit narrow screens get
   `hidden lg:table-cell` / `hidden xl:table-cell` (progressive disclosure, not a responsive
   burger regime). The actions column is `class="w-px"` with an `sr-only` header. Numbers are
   `tabular-nums`; amounts render through the `days` filter (person-days without trailing zeros).
5. Per row: badges (`badge badge-sm badge-outline`, status colours from a macro), a
   `progress progress-secondary` for shares, `row_actions` (ghost `btn-xs`, pencil and trash,
   behind `row.writable`, `aria-label` naming the row) which `hx-get` `…/edit` and `…/delete`
   into `#modal-body`. Detail rows toggle through `toggle-details` with a hidden `<tr>`.
6. The `pager` macro under the table: "x–y of z", `join`-grouped `btn-sm`s, prev/next as real
   `href`s **and** `hx-get`s (same wiring as the filter form).
7. The empty state: the `empty` macro — a dashed-border card, message plus optional hint, no
   illustration by default.

Dialog fragments (`crud/_form.html`, `crud/_confirm_delete.html`, `crud/_import.html`,
`crud/_secret.html`) are generic: the form posts to `#list` (`hx-put` for edits) with
`hx-disable-elt="find button[type=submit]"` (no double submits), carries a hidden `version`
field, and shows a stale-version banner (`alert-warning` with a *Load current values* button)
when the answer came back a conflict (`412` for `If-Match`, `409` for a version in the body).

---

## Forms

One macro renders every field (`form_field` in `macros.html`), from a field object that couples
the server's view of the field (name, kind, required, min/max, maxlength, autocomplete) with the
submitted value, the resolved label and help text, and the error the API returned. Kinds:
`text`, `number` (step 1, `inputmode`), `email`, `date`, `password`, `select` (with an empty "—"
option when not required), `textarea`, `checkbox`, `multiselect` (check boxes in a scroll box),
`color` (picker + hex text input, wired by the Alpine `colorField` component), plus the composite
kinds the domain needs (`roles`, `efforts`).

Every error is text next to the field (`text-xs text-error`, `role="alert"`) and the control gets
`aria-invalid="true"` + `aria-describedby`; required fields carry an `aria-hidden` asterisk and the
`required` attribute; help text sits in `aria-describedby`. Server-managed fields
(`f.readonly`) render disabled with a note (*Maintained by the connected system.*) and carry a
hidden input, so a submit is not silently truncated.

Two form generators build on this: the CRUD machinery above, and the schema-driven settings form
(`schema_form.py`), which draws provider settings from the provider's Pydantic schema — a new
integration needs no interface code. Its schema markers (`x-showWhen`, `x-remoteOptions`) map to
the `data-show-when` and `data-filter-choices` hooks of the page script.

---

## Styling conventions

- Layout in Tailwind utilities in the markup; components from daisyUI; page-level geometry and
  attribute-driven rules in `tailwind.app.css`, unlayered where the scanner cannot see them.
- Muted text is the same trick everywhere: `opacity-50`…`opacity-70` on `base-content`, never a
  grey of its own — so it survives both themes and the AA tuning stays done once.
- Sticky header on `base-100` with a `base-300` border; the sidebar the same. Content sits on
  `base-200`.
- The focus floor, for everything daisyUI does not already style:

  ```css
  :focus-visible { outline: 2px solid var(--fallback-s, oklch(var(--s)));
                   outline-offset: 2px; border-radius: 2px; }
  ```

  The fallback guard exists because daisyUI 4 stores its tokens as bare OKLCH components;
  wrapping them in `hsl()` would drop the whole shorthand and the ring would silently vanish.
  `:focus-visible` only — a mouse click must not paint a ring.
- `dialog.modal:not([open]) { display: none; }` (a closed dialog is not tabbable).
- `@media (prefers-reduced-motion: reduce)` turns off the sidebar transition.
- Team colours and other object colours arrive as inline `style` attributes — the reason for
  `style-src-attr 'unsafe-inline'` and nothing else from CSP's unsafe list.

The content security policy, verbatim:

```text
default-src 'self'; script-src 'self'; style-src 'self'; style-src-attr 'unsafe-inline';
img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none';
form-action 'self'; frame-ancestors 'none'
```

With it: `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `X-Frame-Options: DENY`,
`Permissions-Policy: camera=(), microphone=(), geolocation=()`, `Strict-Transport-Security` when
the public address is https, and `Cache-Control: no-store` on everything that is not `/static/`.

---

## Icons

`icons.py` inlines the Tabler outline subset (`planner_ui/icons/<name>.svg`, vendored by name)
directly into the HTML: `<svg viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
aria-hidden="true">` plus the icon's inner paths — the invisible bounding-box path is stripped.
The default class is `h-4 w-4 shrink-0`; `icon("pencil", "h-4 w-4 transition-transform")` to vary.
Inline SVG takes the text colour, needs no request and no CSP exception. Icon-only buttons always
carry a translated `aria-label`; a decorative icon next to text pairs with an `sr-only` label when
it carries meaning of its own (the lock on source-managed fields).

---

## Internationalisation

- The message id **is** the English text (no `tasks.title` keys); the source language needs no
  catalogue and is always offered.
- A language is a directory: `locale/<code>/LC_MESSAGES/messages.po`. The `.po` files are read
  and compiled in memory at start; nothing binary in the repository, no build step. A broken
  catalogue is logged and left out, never down the page.
- The request language is a `ContextVar` set once per request (account setting, else the browser's
  `Accept-Language`) — so `problem_text` and route messages see it too, not only templates.
- Templates translate with `_()` (and plural forms through the i18n extension); Python-side
  message ids (the navigation) are marked with `N_()`.
- Formats come from Babel, as Jinja filters: `date`, `datetime`, `number` (with places),
  `days` (quantities without trailing zeros), `daymonth`, `weekday` — never hand-rolled formats.
- The language picker lives in the account menu: a POST per choice (hidden CSRF input, the chosen
  code as the button's value), each option named in its own language, the current one marked with
  ✓ and `aria-current`. A test fails when a text or an error code has no translation.

---

## Accessibility floor

- Operable by keyboard: the board (drag and drop has an *Assign…* dialog as its full equivalent),
  every dialog (native `<dialog>`, focus moved to the first field, Esc and backdrop close), the
  pager (real links), the dropdowns (Tab opens, focus ring visible).
- Announced state: `#toasts` is `aria-live="polite"`; alerts carry `role="alert"` or `status` by
  kind; the board sets `aria-busy` while a booking runs.
- Never colour alone: full and over-booked weeks carry text and an icon; drop targets get a dashed
  frame and the rest is dimmed; toasts differ by more than their colour.
- Semantics: `<nav aria-label>`, `aria-current="page"`, real `<thead>` header cells (`scope` on
  the complex tables: the board, the absence calendar), `sr-only` texts for icon-only actions,
  `aria-expanded`/`aria-controls` on every disclosure, `<html lang>` from the request language,
  `lang` on the language options; decorative icons are `aria-hidden="true"`.
- Motion: transitions respect `prefers-reduced-motion`.

---

## Porting the layout to another project

What to do, in order, when reusing this design elsewhere:

1. **Copy the brand layer verbatim and keep it verbatim**: `tailwind.brand.css` and
   `tailwind.config.js` (fonts, logo colours, theme tokens) — these are the files shared
   byte-identical across interfaces of the same brand, marked by the `fidonis-brand: <stamp>`
   comment. If the destination project has no shared counterpart, the stamp may start fresh at 1,
   but then it must still be bumped on every later change of these files everywhere.
2. **Copy `tailwind.app.css` and adapt it**: the sidebar geometry, the focus floor, the dialog fix
   and the reduced-motion rules are portable; the board drag rules are board-specific (or get
   replaced by the rules of whatever attribute-driven states the new project has).
3. **Copy the template skeleton**: `layout.html` → `base.html`/`bare.html`, `macros.html`.
   Rename per project: the `<title>` suffix and the visible name, the `localStorage` keys (`rp-theme`,
   `rp-sidebar` — pick a short, project-unique prefix), the theme names, the icon set, and the
   navigation contents (`nav.py`). Keep the block names, the canonical ids (`#list`, `#modal`,
   `#modal-body`, `#toasts`), the `data-action` vocabulary and the server event names — the page
   script and the templates agree on exactly those.
4. **Copy `js/init.js` (unchanged but for the storage keys and theme names) and `js/app.js`,
   pruning the parts the project does not have** (the board section if there is no board).
5. **Rebuild the feeder code equivalent**: a Jinja environment (autoescape, `StrictUndefined`,
   the i18n extension), the `render()` context (`me`, `csrf_token`, `can`, `nav_groups`),
   `asset_url` fingerprinting, the security-header middleware, and the exception handlers
   (login redirect, forced password change, failure-as-toast, unreachable). The CSP must not be
   loosened to make a page work — that page is wrong, not the policy.
6. **Re-run the vendoring** for the new project's exact versions (`scripts/vendor.mjs`
   equivalents) and keep the licence files in the image; the third-party list must stay honest.
7. Then every screen is the *standard list page* recipe, a `bare.html` page for the auth screens,
   and fragments — nothing else.

What not to port: the API side, the sync machinery, the domain maths. This file covers the
interface. The boundaries of the interface are one sentence, and it holds in the next project too:
the interface renders what the API returns, decides nothing on its own, and talks to exactly one
other component — the API.

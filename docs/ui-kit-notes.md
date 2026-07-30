# UI kit notes (Phase 1–6 close-out — M13/M14)

Minimal officer cockpit styling — not a full design system yet.

## Tokens (Tailwind / CSS)

| Token | Usage |
|---|---|
| `primary` | CTAs, brand shield accents |
| `slate-*` | Text hierarchy, borders, muted labels |
| Status badges | Role colours: admin emerald, supervisor purple, officer blue |

## Components in use

- `components/ui/{Button,Badge,Card}` — shared primitives
- Layout: `Navbar` + page shells (Cases list / detail / Health / Login)
- Intake: `CaseIntakeModal` (form interaction; card container OK)

## Theme unification (M14)

- Prefer slate neutrals + primary accent; avoid introducing a second palette per page
- Keep Phase labels in muted mono badges, not competing heroes
- Notification UI deferred until Phase 17 (bell removed from navbar)

## Phase 7+

Do not expand the kit until intake/import flows stabilize; reuse Card/Button/Badge first.

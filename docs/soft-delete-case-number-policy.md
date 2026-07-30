# Soft-delete & `case_number` policy (L9)

## Soft-delete

- Core Postgres entities use `deleted_at` (nullable timestamp).
- Default list/detail queries **must** exclude `deleted_at IS NOT NULL` rows.
- Soft-deleted rows remain for audit/history; hard DELETE is not used for investigative records.

## `case_number` uniqueness

- `case_number` has a **unique** DB constraint across the table (including soft-deleted rows).
- **Reuse policy:** never reissue a soft-deleted case’s `case_number` to a new complaint.
- New intakes always generate a fresh `MH-CYBER-YYYY-####` (or officer-supplied unused value).
- If an officer needs to “revive” a mistaken delete, clear `deleted_at` on the same row rather than creating a duplicate number.

## Naming canonical fields (M5)

| Discovery shorthand | Canonical DB / API field |
|---|---|
| `ncrp_ref` | `ncrp_acknowledgement_number` |
| complainant / victim contact | `complainant_*` on Case; victim bank identifiers on `victim_*` fields |
| hop layer | Prefer **trail / CaseAccount role** (`suspect_layer1`, …). Account.`layer_number` is a legacy hint only — Phase 8+ should treat hop depth as trail-scoped. |

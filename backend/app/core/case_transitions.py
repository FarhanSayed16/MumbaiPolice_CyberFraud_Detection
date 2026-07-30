"""Validated case lifecycle transitions (Phase 16 audit H14)."""

from app.models.enums import CaseStatusEnum, RoleEnum

OFFICER_TRANSITIONS: dict[CaseStatusEnum, set[CaseStatusEnum]] = {
    CaseStatusEnum.REPORTED: {CaseStatusEnum.INTAKE_COMPLETE},
    CaseStatusEnum.INTAKE_COMPLETE: {CaseStatusEnum.TRACING},
    CaseStatusEnum.TRACING: {
        CaseStatusEnum.NOTICE_PENDING,
        CaseStatusEnum.AWAITING_BANK,
        CaseStatusEnum.DEAD_END,
    },
    CaseStatusEnum.NOTICE_PENDING: {CaseStatusEnum.NOTICE_SENT, CaseStatusEnum.TRACING},
    CaseStatusEnum.NOTICE_SENT: {CaseStatusEnum.AWAITING_BANK, CaseStatusEnum.ACTION_TAKEN},
    # Entry: after notice sent or while tracing bank freeze response; sets notice-response SLA (M16).
    CaseStatusEnum.AWAITING_BANK: {
        CaseStatusEnum.ACTION_TAKEN,
        CaseStatusEnum.PARTIALLY_RECOVERED,
        CaseStatusEnum.TRACING,
    },
    CaseStatusEnum.ACTION_TAKEN: {CaseStatusEnum.PARTIALLY_RECOVERED, CaseStatusEnum.CLOSED},
    CaseStatusEnum.PARTIALLY_RECOVERED: {CaseStatusEnum.CLOSED},
    CaseStatusEnum.CLOSED: set(),
    CaseStatusEnum.DEAD_END: set(),
}

ELEVATED_TRANSITIONS: dict[CaseStatusEnum, set[CaseStatusEnum]] = {
    CaseStatusEnum.REPORTED: {CaseStatusEnum.INTAKE_COMPLETE, CaseStatusEnum.TRACING, CaseStatusEnum.DEAD_END},
    CaseStatusEnum.INTAKE_COMPLETE: {
        CaseStatusEnum.TRACING,
        CaseStatusEnum.NOTICE_PENDING,
        CaseStatusEnum.AWAITING_BANK,
        CaseStatusEnum.DEAD_END,
        CaseStatusEnum.CLOSED,
    },
    CaseStatusEnum.TRACING: {
        CaseStatusEnum.NOTICE_PENDING,
        CaseStatusEnum.NOTICE_SENT,
        CaseStatusEnum.AWAITING_BANK,
        CaseStatusEnum.ACTION_TAKEN,
        CaseStatusEnum.DEAD_END,
        CaseStatusEnum.CLOSED,
    },
    CaseStatusEnum.NOTICE_PENDING: {
        CaseStatusEnum.NOTICE_SENT,
        CaseStatusEnum.TRACING,
        CaseStatusEnum.AWAITING_BANK,
        CaseStatusEnum.CLOSED,
        CaseStatusEnum.DEAD_END,
    },
    CaseStatusEnum.NOTICE_SENT: {
        CaseStatusEnum.AWAITING_BANK,
        CaseStatusEnum.ACTION_TAKEN,
        CaseStatusEnum.PARTIALLY_RECOVERED,
        CaseStatusEnum.CLOSED,
        CaseStatusEnum.DEAD_END,
    },
    # awaiting_bank: bank freeze/response window — sla_due_at set on entry; exit to action/recovery/tracing (M16).
    CaseStatusEnum.AWAITING_BANK: {
        CaseStatusEnum.ACTION_TAKEN,
        CaseStatusEnum.PARTIALLY_RECOVERED,
        CaseStatusEnum.TRACING,
        CaseStatusEnum.NOTICE_SENT,
        CaseStatusEnum.CLOSED,
        CaseStatusEnum.DEAD_END,
    },
    CaseStatusEnum.ACTION_TAKEN: {
        CaseStatusEnum.PARTIALLY_RECOVERED,
        CaseStatusEnum.CLOSED,
        CaseStatusEnum.AWAITING_BANK,
    },
    CaseStatusEnum.PARTIALLY_RECOVERED: {CaseStatusEnum.CLOSED, CaseStatusEnum.ACTION_TAKEN},
    CaseStatusEnum.CLOSED: set(),
    CaseStatusEnum.DEAD_END: {CaseStatusEnum.TRACING, CaseStatusEnum.INTAKE_COMPLETE},
}


def allowed_next_statuses(current: CaseStatusEnum, role: RoleEnum) -> set[CaseStatusEnum]:
    if role in (RoleEnum.SUPERVISOR, RoleEnum.ADMIN):
        return ELEVATED_TRANSITIONS.get(current, set())
    return OFFICER_TRANSITIONS.get(current, set())


def validate_status_transition(
    current: CaseStatusEnum,
    target: CaseStatusEnum,
    role: RoleEnum,
) -> bool:
    if current == target:
        return True
    return target in allowed_next_statuses(current, role)

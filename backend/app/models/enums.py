import enum


class RoleEnum(str, enum.Enum):
    OFFICER = "officer"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class CaseStatusEnum(str, enum.Enum):
    """Aligned to master plan §3.2 case lifecycle (audit H6)."""
    REPORTED = "reported"
    INTAKE_COMPLETE = "intake_complete"
    TRACING = "tracing"
    NOTICE_PENDING = "notice_pending"
    NOTICE_SENT = "notice_sent"
    AWAITING_BANK = "awaiting_bank"
    ACTION_TAKEN = "action_taken"
    PARTIALLY_RECOVERED = "partially_recovered"
    CLOSED = "closed"
    DEAD_END = "dead_end"


class NoticeStatusEnum(str, enum.Enum):
    DRAFTED = "drafted"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    ACTION_TAKEN = "action_taken"
    OVERDUE = "overdue"
    REJECTED = "rejected"
    CLARIFICATION_REQUESTED = "clarification_requested"


class FraudCategoryEnum(str, enum.Enum):
    DIGITAL_ARREST = "digital_arrest"
    INVESTMENT_SCAM = "investment_scam"
    ONLINE_TRADING_SCAM = "online_trading_scam"
    HACKING_DIGITAL_FRAUD = "hacking_digital_fraud"
    SEXTORTION = "sextortion"
    OTHER = "other"


class NoticeTypeEnum(str, enum.Enum):
    SECTION_94 = "section_94"
    SECTION_168 = "section_168"
    SECTION_106 = "section_106"
    UNFREEZE_ORDER = "unfreeze_order"
    CLARIFICATION = "clarification"

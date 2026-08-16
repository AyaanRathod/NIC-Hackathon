from enum import Enum

class Classification(str, Enum):
    HALAL = "Halal"
    HARAM = "Haram"
    MIXED = "Mixed"
    TENTATIVE = "Tentative"
    MISSING_INFO = "Missing Information"

class Category(str, Enum):
    CASH_BANK = "Cash & Bank Balances"
    INVESTMENTS = "Halal Investments"
    BUSINESS_INVENTORY = "Business Inventory"
    GOLD_SILVER = "Gold & Silver"
    RECEIVABLES = "Receivables / Invoices"
    CRYPTO = "Cryptocurrency"
    OTHER = "Other"

class Madhhab(str, Enum):
    MALIKI = "Maliki"

class RepaymentLikelihood(str, Enum):
    LIKELY = "likely"
    DOUBTFUL = "doubtful"
    NOT_APPLICABLE = "not_applicable"

class Direction(str, Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"

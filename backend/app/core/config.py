"""Configuration and constants for Maliki Zakat Calculator."""

class Settings:
    PROJECT_NAME: str = "Maliki Halal Income & Zakat Calculator"
    VERSION: str = "1.0.0"
    DEFAULT_GOLD_NISAB_CAD: float = 9250.00
    DEFAULT_SILVER_NISAB_CAD: float = 875.00
    ZAKAT_RATE: float = 0.025  # 2.5%
    LUNAR_MONTHS_HAWL: int = 12
    # Dated prototype spots for karat conversion only. Nisab stays on organizer CAD values.
    # Kitco CAD gold, 16 August 2026. Not fetched live at runtime.
    GOLD_SPOT_CAD_PER_GRAM: float = 195.21
    SILVER_SPOT_CAD_PER_GRAM: float = 3.48
    GOLD_SPOT_AS_OF: str = "2026-08-16"

settings = Settings()

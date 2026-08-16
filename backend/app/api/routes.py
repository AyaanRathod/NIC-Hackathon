from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import (
    ZakatCalculationRequest,
    ZakatCalculationResponse,
    ClassificationRequest,
    ClassificationResponse,
    UploadResponse,
)
from app.services.classifier import classify_entry
from app.services.zakat_calculator import calculate_maliki_zakat
from app.services.excel_parser import parse_workbook
from app.services.test_cases import get_all_test_cases
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["Zakat & Halal Income"])

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Maliki Halal Income & Zakat Calculator API",
        "madhhab": "Maliki",
        "version": "1.0.0",
    }

@router.post("/calculate", response_model=ZakatCalculationResponse)
def calculate_endpoint(payload: ZakatCalculationRequest):
    try:
        return calculate_maliki_zakat(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculation error: {str(e)}")

@router.post("/classify-transaction", response_model=ClassificationResponse)
def classify_endpoint(payload: ClassificationRequest):
    try:
        cls, explanation, matched_kw = classify_entry(
            description=payload.description,
            notes=payload.notes or "",
            category=payload.category,
        )
        return ClassificationResponse(
            classification=cls,
            explanation=explanation,
            matched_keyword=matched_kw,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Classification error: {str(e)}")

@router.post("/upload-file", response_model=UploadResponse)
async def upload_file_endpoint(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file name is required.")
    
    contents = await file.read()
    try:
        return parse_workbook(contents, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

@router.post("/upload-csv", response_model=UploadResponse)
async def upload_csv_endpoint(file: UploadFile = File(...)):
    return await upload_file_endpoint(file)

@router.get("/test-cases")
def list_test_cases():
    return {
        "test_cases": [
            {
                "id": "case_1",
                "title": "Test Case 1: Faris Mahmood (Practice B)",
                "description": "Stable wealth history ($9,250 Nisab), gold investment coins, screened stocks, long-term mortgage/student debt.",
                "expected_zakat_cad": 574.75,
            },
            {
                "id": "case_2",
                "title": "Test Case 2: Nadia Rahman (Practice A)",
                "description": "Emergency drop in Month 6 ($9,000 Nisab), hawl maintained above threshold, screened portfolio, personal jewelry exemption.",
                "expected_zakat_cad": 496.75,
            },
            {
                "id": "case_3",
                "title": "Test Case 3: Zayd Al-Ansari (E-Commerce Trader)",
                "description": "Mixed business revenue (both separated & retained portions), unscreened crypto, personal loan exemptions, 12-month debt limits.",
                "expected_zakat_cad": 697.50,
            },
        ]
    }

@router.get("/test-cases/{case_id}", response_model=ZakatCalculationRequest)
def get_test_case_payload(case_id: str):
    cases = get_all_test_cases()
    if case_id not in cases:
        raise HTTPException(status_code=404, detail=f"Test case '{case_id}' not found.")
    return cases[case_id]

@router.get("/metal-prices")
def metal_prices():
    return {
        "gold_cad_per_gram": settings.GOLD_SPOT_CAD_PER_GRAM,
        "silver_cad_per_gram": settings.SILVER_SPOT_CAD_PER_GRAM,
        "as_of": settings.GOLD_SPOT_AS_OF,
        "source": "Kitco CAD snapshot for the prototype. Not a live feed. Nisab still uses the organizer CAD value.",
        "nisab_gold_cad": settings.DEFAULT_GOLD_NISAB_CAD,
        "nisab_silver_cad": settings.DEFAULT_SILVER_NISAB_CAD,
    }


@router.post("/calculate-metal")
def calculate_metal_valuation(payload: dict):
    metal = payload.get("metal_type", "Gold")
    karat_str = str(payload.get("karat", "24K")).upper()
    weight = float(payload.get("weight", 0.0))
    unit = str(payload.get("unit", "grams")).lower()
    default_price = settings.GOLD_SPOT_CAD_PER_GRAM if metal == "Gold" else settings.SILVER_SPOT_CAD_PER_GRAM
    manual_price = float(payload.get("manual_price_per_gram_cad", default_price))
    is_customary = bool(payload.get("is_customary_jewelry", False))
    has_gemstones = bool(payload.get("has_gemstones", False))

    if unit == "tola":
        gross_grams = weight * 11.6638
    elif unit == "oz":
        gross_grams = weight * 31.1035
    else:
        gross_grams = weight

    if metal == "Gold":
        karat_map = {
            "24K": 24.0 / 24.0,
            "22K": 22.0 / 24.0,
            "21K": 21.0 / 24.0,
            "18K": 18.0 / 24.0,
            "14K": 14.0 / 24.0,
            "10K": 10.0 / 24.0,
        }
        fraction = karat_map.get(karat_str, 1.0)
        nisab_threshold_grams = 85.0
    else:
        silver_map = {"999": 0.999, "925": 0.925, "FINE": 0.999, "STERLING": 0.925}
        fraction = silver_map.get(karat_str, 0.999)
        nisab_threshold_grams = 595.0

    pure_grams = gross_grams * fraction
    total_val = pure_grams * manual_price

    notes = []
    if has_gemstones:
        notes.append("Diamonds and gemstones are excluded unless they are business inventory. This CAD value is metal only.")
    if is_customary:
        is_exempt = True
        ruling = "Worn customary jewelry is exempt under Maliki rules."
    else:
        is_exempt = False
        ruling = "Bullion, coins, bars, or investment jewelry is zakatable at pure metal value."

    return {
        "metal_type": metal,
        "karat": karat_str,
        "purity_fraction": round(fraction, 4),
        "gross_weight_grams": round(gross_grams, 2),
        "pure_weight_grams": round(pure_grams, 2),
        "unit": unit,
        "price_per_gram_cad": round(manual_price, 2),
        "total_cad_value": round(total_val, 2),
        "nisab_threshold_grams": nisab_threshold_grams,
        "is_above_metal_nisab": pure_grams >= nisab_threshold_grams,
        "is_maliki_exempt": is_exempt,
        "fiqh_ruling_summary": ruling + (" " + " ".join(notes) if notes else ""),
        "price_as_of": settings.GOLD_SPOT_AS_OF,
    }

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["madhhab"] == "Maliki"
    print("Health check endpoint PASSED!")

def test_classify_api():
    res = client.post("/api/classify-transaction", json={
        "description": "Stock dividend from shariah-screened fund",
        "category": "Halal Investments"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "Halal"
    print("Classify API endpoint PASSED!")

def test_test_cases_api():
    res = client.get("/api/test-cases")
    assert res.status_code == 200
    cases = res.json()["test_cases"]
    assert len(cases) == 3
    print("List Test Cases API endpoint PASSED!")

    # Test load Case 1
    res1 = client.get("/api/test-cases/case_1")
    assert res1.status_code == 200
    faris_payload = res1.json()
    assert len(faris_payload["entries"]) > 0

    # Test calculate Case 1
    res_calc = client.post("/api/calculate", json=faris_payload)
    assert res_calc.status_code == 200
    calc_data = res_calc.json()
    assert calc_data["zakat_due_cad"] == 574.75
    assert calc_data["is_eligible_for_zakat"] == True
    print("Faris Mahmood end-to-end calculation API PASSED!")

    # Test load & calculate Case 2 (Nadia)
    res2 = client.get("/api/test-cases/case_2")
    assert res2.status_code == 200
    nadia_payload = res2.json()
    res_calc2 = client.post("/api/calculate", json=nadia_payload)
    assert res_calc2.status_code == 200
    calc_data2 = res_calc2.json()
    assert calc_data2["zakat_due_cad"] == 496.75
    print("Nadia Rahman end-to-end calculation API PASSED!")

def test_upload_api():
    # Test uploading Faris Mahmood excel workbook
    excel_path = Path(__file__).resolve().parent.parent.parent / "Faris_Mahmood_Participant_Practice_B_.xlsx"
    if excel_path.exists():
        with open(excel_path, "rb") as f:
            res = client.post("/api/upload-file", files={"file": ("Faris.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
            assert res.status_code == 200
            data = res.json()
            assert len(data["entries"]) > 0
            assert len(data["debts"]) > 0
            assert len(data["wealth_history"]) > 0
            assert data["person_name"] == "Faris Mahmood"
            assert len(data["transactions"]) > 100
            assert data["income_inflow_count"] > 0
            tx_inv = next(s for s in data["sheet_inventory"] if s["sheet"] == "Transactions")
            assert tx_inv["rows_in_file"] == tx_inv["rows_kept"]
            assert tx_inv["rows_in_file"] >= 600
            crypto = next(e for e in data["entries"] if e["id"] == "FM-A12")
            assert crypto["classification"] == "Tentative"
            mixed = next(e for e in data["entries"] if e["id"] == "FM-A16")
            assert mixed["classification"] == "Mixed"
            assert mixed["is_mixed_separated"] is False
            jewelry = next(e for e in data["entries"] if e["id"] == "FM-A07")
            assert jewelry["is_personal_jewelry"] is True
            disposed = next(t for t in data["transactions"] if t.get("keyword") == "mixed_income_disposed")
            assert disposed["classification"] == "Mixed"
            assert disposed["is_mixed_separated"] is True
            assert disposed["halal_amount"] == 1600.0
            print("Excel Upload API endpoint PASSED!")

if __name__ == "__main__":
    test_health()
    test_classify_api()
    test_test_cases_api()
    test_upload_api()
    print("\nALL FASTAPI INTEGRATION TESTS PASSED PERFECTLY!")

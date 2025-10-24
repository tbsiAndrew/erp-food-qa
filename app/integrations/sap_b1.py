
import requests
from ..db import DB
from ..config import settings

_session = requests.Session()

def _login():
    r = _session.post(f"{settings.SAP_BASE_URL}/Login", json={
        "CompanyDB": settings.SAP_DB,
        "UserName": settings.SAP_USER,
        "Password": settings.SAP_PWD,
    }, timeout=15)
    r.raise_for_status()

def push_result_to_sap_async(qa_result_id: int):
    with DB() as db:
        rec = db.get_qa_result_with_image(qa_result_id)
    payload = {
        "U_ItemCode": rec["item_code"],
        "U_LotNo": rec["lot_no"],
        "U_Pass": "Y" if rec["pass"] else "N",
        "U_Grade": rec["grade"] or "",
        "U_Confidence": round(float(rec["confidence"] or 0.0), 3),
        "U_ReasonCodes": ";".join(rec["reason_codes"] or []),
        "U_QAImageLink": rec["s3_uri"],
        "U_QAResultId": int(rec["id"]),
        "U_Timestamp": rec["capture_ts"].isoformat(),
    }
    try:
        _login()
        rr = _session.post(f"{settings.SAP_BASE_URL}/U_QA_RESULTS", json=payload, timeout=20)
        rr.raise_for_status()
        with DB() as db:
            db.mark_erp_event(qa_result_id, status="OK", payload=payload)
    except Exception as e:
        with DB() as db:
            db.mark_erp_event(qa_result_id, status="ERR", error=str(e), payload=payload)

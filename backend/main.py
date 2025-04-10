from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import requests
import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import pandas as pd

app = FastAPI()

# Get absolute path to the frontend directory
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))

if not os.path.exists(frontend_path):
    raise RuntimeError(f"Frontend directory not found at: {frontend_path}")

app.mount("/app", StaticFiles(directory=frontend_path, html=True), name="frontend")

# --- Config ---
ERP_API_BASE = "https://Vintech.on.plex.com/api/datasources/"
headers = {
  'Authorization': 'Basic VmludGVjaFdTQHBsZXguY29tOmE0Y2Q3OGEtZmUxMi00',
  'Content-Type': 'application/json'
}

now = datetime.today()

# --- Mock In-Memory Store (can be replaced with DB) ---
valid_shippers = {}  
valid_serials = {}

# --- Pydantic Models ---
class ShipperRequest(BaseModel):
    shipper_number: str

class ScanRequest(BaseModel):
    shipper_number: str
    container_serial: str

class ScanResponse(BaseModel):
    status: str
    message: str

class TableModel(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    rowLimitExceeded: Optional[bool] = False


class ERPResponse(BaseModel):
    outputs: Dict[str, Any]
    tables: List[TableModel]
    transactionNo: str


# --- ERP Client ---
def fetch_valid_shippers_from_erp(begin_date: datetime, end_date: datetime) -> List[str]:
    shipper_list_id = "17477"

    begin_date = begin_date.isoformat(timespec='milliseconds').replace('+00:00', 'Z') + "Z"
    end_date = end_date.isoformat(timespec='milliseconds').replace('+00:00', 'Z') + "Z"
    print(f"Begin Date: {begin_date}")
    print(f"End Date: {end_date}")

    payload = json.dumps({
        "inputs": {
            "Begin_Ship_Date": f"{begin_date}",
            "End_Ship_Date": f"{end_date}"
        }
    })
    # print("Calling ERP with:")
    # print("URL:", f"{ERP_API_BASE}{shipper_list_id}/execute")
    # print("Headers:", headers)
    # print("Payload:", payload)
    response = requests.request(
        "POST",
        f"{ERP_API_BASE}{shipper_list_id}/execute",
        headers=headers,
        data=payload,
        timeout=10
    )
    # print("ERP Response:", response.status_code, response.json())
    if response.status_code == 200:
        columns = response.json().get("tables")[0].get("columns", [])
        rows = response.json().get("tables")[0].get("rows", [])
        df = pd.DataFrame(rows, columns=columns)
        return df
    else:
        raise HTTPException(status_code=502, detail="Failed to fetch valid shippers")
    

def get_open_shippers(shippers: pd.DataFrame) -> List[str]:
    shippers = shippers[shippers["Shipper_Status"] == "Open"]
    return shippers

def update_erp_with_load(shipper_number: str, container_serial: str) -> bool:
    response = requests.post(
        f"{ERP_API_BASE}/load_container",
        json={"shipper": shipper_number, "serial": container_serial},
        headers={headers},
        timeout=10
    )
    return response.status_code == 200

# --- API Routes ---
@app.post("/api/test")
def test():
    return {"message": "Success"}

@app.post("/api/get_valid_shippers")
async def get_valid_shippers():
    begin_date = now - timedelta(days = 31)
    end_date = now + timedelta(days = 31)
    shippers  = fetch_valid_shippers_from_erp(begin_date, end_date)
    open_shippers = get_open_shippers(shippers)
    print(open_shippers['Shipper_No'].tolist())
    return open_shippers['Shipper_No'].tolist()

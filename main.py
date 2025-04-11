from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
import requests
import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import pandas as pd

app = FastAPI()
templates = Jinja2Templates(directory="templates/")


# # Get absolute path to the frontend directory
# frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/"))

# if not os.path.exists(frontend_path):
#     raise RuntimeError(f"Frontend directory not found at: {frontend_path}")

app.mount("/static", StaticFiles(directory="static", html=True), name="static")



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


class UserInput(BaseModel):
    shipper_number: str




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



def shipper_no_to_keys(shipper: str) -> str:
    shipper_no_to_keys_id = "20168"
    url = f"{ERP_API_BASE}{shipper_no_to_keys_id}/execute"
    payload = json.dumps({
        "inputs": {
            "Shipper_No": f"{shipper}"
        }
    })
    print("[shipper_no_to_keys] payload: ", payload)
    response = requests.request("POST", url=url, headers=headers, data=payload)
    print("[shipper_no_to_keys] response: ", response.json())
    return str(response.json()['tables'][0]['rows'][0][0])
    



def get_shipper_details(shipper: str) -> Dict[str, int]:
    shipper_details_id = "9278"
    url = f"{ERP_API_BASE}{shipper_details_id}/execute"
    print("[get_shipper_details] url: ", url)
    shipper_keys = shipper_no_to_keys(shipper)
    print("[get_shipper_details] shipper_keys: ", shipper_keys)
    payload = json.dumps({
    "inputs": {
        "Shipper_Keys": shipper_keys
    }
    })
    print("[get_shipper_details] payload: ", payload)
    headers = {
    'Authorization': 'Basic VmludGVjaFdTQHBsZXguY29tOmE0Y2Q3OGEtZmUxMi00',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url=url, headers=headers, data=payload)
    print("[get_shipper_details] status code: ", response.status_code)
    print("[get_shipper_details] response: ", response.json())

    columns = response.json().get("tables")[0].get("columns", [])
    rows = response.json().get("tables")[0].get("rows", [])
    df = pd.DataFrame(rows, columns=columns)
    shipper_demand = dict(zip(df['Part_Key'], df['Quantity']))
    return shipper_demand





def get_valid_containers(shipper_demand: dict[str, int]) -> pd.DataFrame:
    for demand in shipper_demand.items():
        print("[get_valid_containers] demand: ", demand)
        all_containers = get_containers_by_part(demand)
        print("[get_valid_containers] all_containers: ")
        print(all_containers)
        all_containers['cumulative'] = all_containers['Quantity'].cumsum()
        # Filter rows where cumulative quantity is less than or equal to demand
        result_df = all_containers[all_containers['cumulative'] <= demand[1]]
        
        # Include the first row that crosses the demand
        if not result_df.empty and result_df['cumulative'].iloc[-1] < demand[1]:
            next_row = all_containers.iloc[len(result_df)]
            result_df = pd.concat([result_df, pd.DataFrame([next_row])], ignore_index=True)
        print("[get_valid_containers] result_df: ")
        print(result_df)
        # Drop the helper column if you don't want it
        result_df = result_df.drop(columns='cumulative')
        all_containers = all_containers[pd.to_datetime(all_containers['Add_Date']) < (pd.to_datetime(result_df['Add_Date'].iloc[-1]) + pd.Timedelta(days=3))]
        print("[get_valid_containers] all_containers: ")
        print(all_containers)
        print("---------------------------------------------------------------")
        return all_containers




def get_containers_by_part(shipper_demand: tuple[str, int]) -> pd.DataFrame:
    containers_by_part_id = "8566"
    url = f"{ERP_API_BASE}{containers_by_part_id}/execute"

    containers_by_part_id = "8566"
    url = f"{ERP_API_BASE}{containers_by_part_id}/execute"

    payload = json.dumps({
        "inputs": {
            "Part_Key": shipper_demand[0]
        }
    })
    headers = {
    'Authorization': 'Basic VmludGVjaFdTQHBsZXguY29tOmE0Y2Q3OGEtZmUxMi00',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url=url, headers=headers, data=payload)
    print(response.status_code)

    columns = response.json().get("tables")[0].get("columns", [])
    rows = response.json().get("tables")[0].get("rows", [])
    df = pd.DataFrame(rows, columns=columns)
    df = df[df['Container_Status'] == 'OK']
    df.sort_values(by='Add_Date', ascending=True, inplace=True)
    return df





def update_erp_with_load(shipper_number: str, container_serial: str) -> bool:
    response = requests.post(
        f"{ERP_API_BASE}/load_container",
        json={"shipper": shipper_number, "serial": container_serial},
        headers={headers},
        timeout=10
    )
    return response.status_code == 200




# --- API Routes ---
@app.post("/test")
def test():
    return {"message": "Success"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/", response_class=HTMLResponse)
async def get_valid_shippers(request: Request):
    begin_date = now - timedelta(days = 31)
    end_date = now + timedelta(days = 31)
    print("[get_valid_shippers] begin_date: ", begin_date)
    print("[get_valid_shippers] end_date: ", end_date)
    shippers  = fetch_valid_shippers_from_erp(begin_date, end_date)
    open_shippers = get_open_shippers(shippers)
    shipper_data = open_shippers[['Shipper_No', 'Customer_Code']].to_dict(orient="records")
    print(shipper_data)
    return JSONResponse(content=shipper_data)
    # return templates.TemplateResponse("index.html", {"request": request, "shipper": shipper_data}) 



@app.get("/shipper/{shipper_number}", response_class=HTMLResponse)
async def shipper_containers(request: Request, shipper_number: str):
    return templates.TemplateResponse("shipper_containers.html", {"request": request, "shipper_number": shipper_number})



# @app.post("/shipper/{shipper_number}")
# async def get_shipper_containers(request: Request, shipper_number: str):
#     print("[get_shipper_containers] input: ", shipper_number)
#     shipper_demand = get_shipper_details(shipper_number)
#     containers = get_valid_containers(shipper_demand)
#     print("[get_shipper_containers] containers: \n", containers)
#     return JSONResponse(content=containers)
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
templates = Jinja2Templates(directory="templates")


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
    



def get_shipper_details(shipper: str) -> Dict[str, tuple[str, int, bool, str]]:
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
    df['Load_complete'] = (df['Quantity_Loaded'] == df['Quantity'])
    # temp = df
    # for idx, row in temp.iterrows():
    #     if row['Quantity_Loaded'] == row['Quantity']:
    #         temp = temp.drop(idx)
    shipper_demand = dict(zip(df['Part_Key'], zip(df['Part_No_Revision'], df['Quantity'], df['Load_complete'], df['Building_Code'])))
    print("[get_shipper_details] shipper_demand: ", shipper_demand)
    return shipper_demand, shipper_keys





def get_valid_containers(demand:tuple[str, tuple[str, int, bool, str]]) -> pd.DataFrame:
    print("[get_valid_containers] demand: ", demand)
    columns = ['Part_No', 'Serial_No', 'Quantity', 'Location', 'Status', "Building_Code"]
    df = pd.DataFrame(columns=columns)
    if demand[1][2]: # if load complete, skip
        print('load complete')
        new_row = {'Part_No': demand[1][0], 'Serial_No': '', 'Quantity': '', 'Location': '', 'Status': 'Load Complete', 'Building_Code': demand[1][3]}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        return df
    else:
        all_containers = get_containers_by_part(demand)
        if all_containers.empty: # if no containers available
            print('no containers available')
            new_row = {'Part_No': demand[1][0], 'Serial_No': '', 'Quantity': '', 'Location': '', 'Status': 'No Containers Available', 'Building_Code': demand[1][3] }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            return df
        print('containers available')
        all_containers['Status'] = "Containers Available"
        all_containers['cumulative'] = all_containers['Quantity'].cumsum()
        # Filter rows where cumulative quantity is less than or equal to demand
        all_containers['Building_Code'] = demand[1][3]
        result_df = all_containers[all_containers['cumulative'] <= demand[1][1]]
        # Include the first row that crosses the demand
        if not result_df.empty and result_df['cumulative'].iloc[-1] < demand[1][1]:
            if len(all_containers) == len(result_df):
                return all_containers[['Part_No', 'Serial_No', 'Quantity', 'Location', 'Status', 'Building_Code']]
            else:
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
        print("demand[1][0], demand[1][1]: ", demand[1][0], demand[1][1])
        return all_containers[['Part_No', 'Serial_No', 'Quantity', 'Location', 'Status', 'Building_Code']]




def get_containers_by_part(shipper_demand: tuple[str, str]) -> pd.DataFrame:
    containers_by_part_id = "8566"
    url = f"{ERP_API_BASE}{containers_by_part_id}/execute"

    payload = json.dumps({
        "inputs": {
            "Part_Key": shipper_demand[0]
        }
    })

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


def update_container_location(serial_no: str, location: str) -> bool:
    update_container_location_id = "24134"
    url = f"{ERP_API_BASE}{update_container_location_id}/execute"

    payload = json.dumps({
    "inputs": {
        "Location": location,
        "Serial_No": serial_no
    }
    })
    print("[update_container_location] payload: ", payload)
    response = requests.request("POST", url=url, headers=headers, data=payload)
    print("[update_container_location] response: ", response.json())
    return response.status_code == 200



def send_to_erp_with_load(serial_no, shipper_key):
    print("[send_to_erp_with_load] serial_no: ", serial_no)

    load_container_id = "8512"
    url = f"{ERP_API_BASE}{load_container_id}/execute"

    payload = json.dumps({
        "inputs": {
            "Serial_No": serial_no,
            "Shipper_Key": shipper_key
        }
    })

    response = requests.request("POST", url=url, headers=headers, data=payload)
    print("[send_to_erp_with_load] response: ", response.json())
    return response.status_code == 200



def get_master_containers(master_unit_no: str) -> List[str]:
    master_containers_id = "230251"
    url = f"{ERP_API_BASE}{master_containers_id}/execute"
    payload = json.dumps({
        "inputs": {
            "Master_Unit_No": master_unit_no
        }
    })
    response = requests.request("POST", url=url, headers=headers, data=payload)
    print("[get_master_containers] response: ", response.json())
    columns = response.json().get("tables")[0].get("columns", [])
    rows = response.json().get("tables")[0].get("rows", [])
    df = pd.DataFrame(rows, columns=columns)
    print("[get_master_containers] df: ", df)
    return df


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



@app.get("/shipper/{shipper_number}", response_class=HTMLResponse)
async def shipper_containers(request: Request, shipper_number: str):
    return templates.TemplateResponse("shipper_containers.html", {"request": request, "shipper_number": shipper_number})



@app.post("/shipper/{shipper_number}")
async def get_shipper_containers(request: Request, shipper_number: str):
    try:
        print("[get_shipper_containers] input: ", shipper_number)
        shipper_demand, shipper_key = get_shipper_details(shipper_number)
        print("[get_shipper_containers] shipper_demand: ", shipper_demand)
        containers = []
        for key, value in shipper_demand.items():
            c = get_valid_containers((key, value))
            print("[get_shipper_containers] c: \n", c)
            containers.append(c)
        # continers, info = get_valid_containers(shipper_demand)
        print("[get_shipper_containers] containers: \n", containers)
        data = [df.to_dict(orient="records") for df in containers]
        print("[get_shipper_containers] data: \n", data)
        return JSONResponse(content={"dataframes": data})
    except Exception as e:
        print("[get_shipper_containers] error: ", e)
        return JSONResponse(content={"error": str(e)})



@app.post("/shipper/scan/{serial_no}")
async def load_container(request: Request, serial_no: str):
    data = await request.json()
    print("[load_container] data: ", data)
    serial_no = data.get("serial_no")
    # shipper_no = data.get("shipper_number")
    building_code = data.get("building_code")
    print("[load_container] building_code: ", building_code)
    # shipper_key = shipper_no_to_keys(shipper_no)
    location = ""
    if building_code == "Imlay":
        location = "Shipping-Staging"
    elif building_code == "IC West":
        location = "Stage/Ship - IW"
    elif building_code == "Almont":
        location = "Stage/Ship - Almont"
    print("[load_container] location: ", location)
    try:
        # result = send_to_erp_with_load(serial_no, shipper_key)
        result = update_container_location(serial_no, location)
        if result:
            return JSONResponse(content={"message": "Success"})
        else:
            return JSONResponse(content={"message": "Failed"})
    except Exception as e:
        print("[load_container] error: ", e)
        return JSONResponse(content={"message": "Failed"})
    

@app.post("/check/master_containers")
async def check_master_containers(request: Request, master_unit_no: str):
    data = await request.json()
    print("[load_container] data: ", data)
    master_unit_no = data.get("master_unit_no")
    print("[check_master_containers] master_unit_no: ", master_unit_no)
    get_master_containers(master_unit_no)
    return JSONResponse(content={"message": "Success"})


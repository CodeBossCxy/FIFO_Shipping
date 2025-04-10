import requests
import json
import pandas as pd
from typing import Dict
import sys


ERP_API_BASE = "https://Vintech.on.plex.com/api/datasources/"
headers = {
  'Authorization': 'Basic VmludGVjaFdTQHBsZXguY29tOmE0Y2Q3OGEtZmUxMi00',
  'Content-Type': 'application/json'
}




def get_shipper_details(shipper: str) -> Dict[str, int]:
    shipper_details_id = "9278"
    url = f"{ERP_API_BASE}{shipper_details_id}/execute"

    payload = json.dumps({
    "inputs": {
        "Shipper_Keys": shipper
    }
    })
    headers = {
    'Authorization': 'Basic VmludGVjaFdTQHBsZXguY29tOmE0Y2Q3OGEtZmUxMi00',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url=url, headers=headers, data=payload)
    print("[get_shipper_details] status code: ", response.status_code)

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




def get_containers_by_part(shipper_demand: tuple[str, int]) -> pd.DataFrame:
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



def main():
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    with open("output.txt", "w") as file:
      sys.stdout = file
      shipper_demand = {"2678456": 10000}
      print("shipper_demand: ", shipper_demand)
      valid_containers = get_valid_containers(shipper_demand)
      print(valid_containers)


if __name__ == "__main__":
    main()

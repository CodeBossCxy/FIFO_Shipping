import requests
import json

ERP_API_BASE = "https://Vintech.on.plex.com/api/datasources"
url = f"{ERP_API_BASE}/17477/execute"
print(url)

payload = json.dumps({
  "inputs": {
    "Begin_Ship_Date": "2025-04-09T00:00:00.175Z",
    "End_Ship_Date": "2025-04-09T17:25:54.175Z"
  }
})
headers = {
  'Authorization': 'Basic VmludGVjaFdTQHBsZXguY29tOmE0Y2Q3OGEtZmUxMi00',
  'Content-Type': 'application/json'
}

response = requests.request("POST", f"{ERP_API_BASE}/17477/execute", headers=headers, data=payload)
print(response.status_code)
print(response.json().get("tables")[0].get("rows", []))

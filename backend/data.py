import requests
import json
import pandas as pd

ERP_API_BASE = "https://Vintech.on.plex.com/api/datasources/"
id = "8566"
url = f"{ERP_API_BASE}{id}/execute"
print(url)

payload = json.dumps({
  "inputs": {
    "Part_Key": "2630873"
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
df.sort_values(by='Add_Date', ascending=True, inplace=True)
with open("output.txt", "w") as file:
    file.write(df.to_string())
    print(df['Add_Date'].dtype)
# # print(df)
# print(df['Part_No'])
# print(df['Quantity'])

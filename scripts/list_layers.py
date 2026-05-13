import requests

URL = (
    "https://gis.rvca.ca/server/rest/services/"
    "RVCA_Hydrology_Service/MapServer?f=pjson"
)

response = requests.get(URL)
data = response.json()

print("\nAvailable Layers:\n")

for layer in data["layers"]:
    print(f'ID: {layer["id"]} | Name: {layer["name"]}')
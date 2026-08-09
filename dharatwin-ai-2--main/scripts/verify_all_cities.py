"""Verify all 5 location predictions via API."""
import requests

for i in range(1, 6):
    try:
        r = requests.get(f"http://127.0.0.1:5000/api/predict/{i}", timeout=15)
        data = r.json()
        preds = data.get("predictions", {})
        errors = data.get("errors", {})
        temp = preds.get("temperature", {}).get("prediction", "N/A")
        rain = preds.get("rainfall", {}).get("prediction", "N/A")
        loc_id = data.get("location_id", i)
        print(f"Location {loc_id}: temp={temp}, rain={rain}, errors={errors}")
    except Exception as e:
        print(f"Location {i}: ERROR - {e}")

print()
# Also test locations endpoint
r = requests.get("http://127.0.0.1:5000/api/locations", timeout=10)
for loc in r.json().get("locations", []):
    print(f"  id={loc['id']} name={loc['name']} lat={loc['latitude']} lon={loc['longitude']}")

print()
# AI status
r = requests.get("http://127.0.0.1:5000/api/ai/status", timeout=10)
data = r.json()
for target, info in data.items():
    print(f"  {target}: {info.get('status', 'UNKNOWN')}")

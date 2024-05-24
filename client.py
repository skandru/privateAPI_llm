import requests

response = requests.post("https://7000-01hygkvng4h65en1z1b7mtfd9p.cloudspaces.litng.ai/predict", json={
    "ticker": "AAPL",
    "purchase_date": "2008-01-04",
    "shares": 100
})
print(f"Status: {response.status_code}\nResponse:\n{response.json()}")

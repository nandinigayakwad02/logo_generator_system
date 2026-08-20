import httpx

url = "http://localhost:8000/api/generate-logo"
payload = {
    "brand_name": "Apex Cybernetics",
    "description": "High tech AI and quantum robotics startup developing autonomous neural chips",
    "style": "cybertech",
    "colors": "Neon Cyan & Obsidian Dark"
}

print("Testing logo generation request...")
r = httpx.post(url, json=payload, timeout=60.0)
print("Status code:", r.status_code)
print("Response:", r.json())

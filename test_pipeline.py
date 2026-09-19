import requests
import time

API = "http://127.0.0.1:8000"

print("1. Submitting Prompt...")
res = requests.post(f"{API}/videos/", json={
    "prompt": "Create a 30-second educational video explaining 3 benefits of daily walking for university students.",
    "duration": "30-60 seconds",
    "language": "English",
    "style": "Educational",
    "target_platform": "TikTok"
})
if res.status_code != 200:
    print("Failed to generate plan:", res.text)
    exit(1)

video_id = res.json()["id"]
print(f"Plan generated! Video ID: {video_id}")

print("2. Starting Video Generation...")
res2 = requests.post(f"{API}/videos/{video_id}/generate")
if res2.status_code != 200:
    print("Failed to start generation:", res2.text)
    exit(1)

print("3. Waiting for generation to complete...")
while True:
    time.sleep(3)
    res3 = requests.get(f"{API}/videos/")
    videos = res3.json()
    v = next((v for v in videos if v["id"] == video_id), None)
    if not v:
        print("Video disappeared!")
        break
    
    status = v["status"]
    print(f"Status: {status}")
    if status == "approved":
        print("SUCCESS! Video Path:", v.get("video_path"))
        break
    elif status == "error":
        print("ERROR:", v.get("error_message"))
        break

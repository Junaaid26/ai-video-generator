import time
import os
import requests

API_URL = "http://127.0.0.1:8000"
ADMIN_HEADERS = {"X-Admin-Role": "admin"}
VIEWER_HEADERS = {"X-Admin-Role": "viewer"}

# CPU rendering on this machine takes ~120-180s per video, so we use 250s
RENDER_TIMEOUT = 250

def wait_for_status(video_id: int, target_status: str, timeout: int = RENDER_TIMEOUT):
    start = time.time()
    while time.time() - start < timeout:
        res = requests.get(f"{API_URL}/videos/{video_id}")
        assert res.status_code == 200, f"Failed to get video {video_id}: {res.text}"
        data = res.json()
        current_status = data.get("status")
        stage = data.get("generation_stage", "UNKNOWN")
        print(f"   [Video {video_id}] Status: {current_status} | Stage: {stage} ({int(time.time() - start)}s elapsed)")
        if current_status == target_status:
            return data
        if current_status in ["FAILED", "ERROR"]:
            raise Exception(f"Video {video_id} failed with error: {data.get('error_message')}")
        time.sleep(3)
    raise TimeoutError(f"Video {video_id} did not reach {target_status} within {timeout}s")

def run_all_tests():
    print("==================================================================")
    print("[START] RUNNING COMPREHENSIVE PHASE 4 APPROVAL SYSTEM TESTS")
    print("==================================================================")

    # 0. Health Check
    res = requests.get(f"{API_URL}/health")
    assert res.status_code == 200, f"API health check failed: {res.text}"
    print("[OK] 0. API is healthy and running.")

    # ------------------------------------------------------------------ #
    # PATH 1: Full Generation -> QA Validation -> APPROVE
    # ------------------------------------------------------------------ #
    print("\n--- TEST 1: Full Generation -> QA Validation -> APPROVE ---")
    create_res = requests.post(f"{API_URL}/videos/", json={
        "prompt": "Explain the benefits of drinking water every morning",
        "duration": "15 seconds",
        "language": "English",
        "style": "Educational",
        "target_platform": "TikTok"
    })
    assert create_res.status_code == 200, f"Creation failed: {create_res.text}"
    vid1 = create_res.json()["id"]
    print(f"1. Video created in DRAFT status. ID: {vid1}")

    gen_res = requests.post(f"{API_URL}/videos/{vid1}/generate")
    assert gen_res.status_code == 200, f"Generation trigger failed: {gen_res.text}"
    print("2. Video generation started. Waiting for PENDING_APPROVAL...")

    v1_pending = wait_for_status(vid1, "PENDING_APPROVAL")
    qa = v1_pending.get("qa_report") or {}
    print(f"3. Video reached PENDING_APPROVAL! QA: {qa.get('summary', 'N/A')}")
    assert v1_pending.get("video_path") and os.path.exists(v1_pending["video_path"]), "Video file missing on disk!"

    app_res = requests.post(f"{API_URL}/videos/{vid1}/approve", headers=ADMIN_HEADERS)
    assert app_res.status_code == 200, f"Approval failed: {app_res.text}"
    assert app_res.json()["status"] == "APPROVED"
    print("[PASS] TEST 1: Generate -> QA -> APPROVE: PASSED")

    # ------------------------------------------------------------------ #
    # PATH 2: REJECT with Reason
    # ------------------------------------------------------------------ #
    print("\n--- TEST 2: REJECT PATH with Stored Rejection Reason ---")
    create_res2 = requests.post(f"{API_URL}/videos/", json={
        "prompt": "Why sleep is crucial for university students",
        "duration": "15 seconds",
        "language": "English",
        "style": "Educational",
        "target_platform": "Instagram Reels"
    })
    assert create_res2.status_code == 200
    vid2 = create_res2.json()["id"]
    requests.post(f"{API_URL}/videos/{vid2}/generate")
    print(f"1. Video #{vid2} generation started...")
    wait_for_status(vid2, "PENDING_APPROVAL")

    reason_text = "Visual pacing is too fast for key study concepts."
    rej_res = requests.post(
        f"{API_URL}/videos/{vid2}/reject",
        headers=ADMIN_HEADERS,
        json={"action": "REJECT", "rejection_reason": reason_text}
    )
    assert rej_res.status_code == 200, f"Rejection failed: {rej_res.text}"
    v2_rejected = rej_res.json()
    assert v2_rejected["status"] == "REJECTED", f"Expected REJECTED, got {v2_rejected['status']}"
    assert v2_rejected["rejection_reason"] == reason_text, f"Reason mismatch: {v2_rejected.get('rejection_reason')}"
    print(f"[PASS] TEST 2: REJECT with reason '{reason_text}' verified in DB: PASSED")

    # ------------------------------------------------------------------ #
    # PATH 3: REGENERATE from REJECTED
    # ------------------------------------------------------------------ #
    print("\n--- TEST 3: REGENERATE PATH on Rejected Video ---")
    regen_res = requests.post(f"{API_URL}/videos/{vid2}/regenerate", headers=ADMIN_HEADERS)
    assert regen_res.status_code == 200, f"Regenerate trigger failed: {regen_res.text}"
    print(f"1. Regeneration started for Video #{vid2}...")
    v2_regen = wait_for_status(vid2, "PENDING_APPROVAL")
    assert v2_regen["status"] == "PENDING_APPROVAL"
    print("[PASS] TEST 3: REGENERATE -> PENDING_APPROVAL: PASSED")

    # ------------------------------------------------------------------ #
    # PATH 4: EDIT CONTENT THEN APPROVE
    # ------------------------------------------------------------------ #
    print("\n--- TEST 4: EDIT CONTENT THEN APPROVE ---")
    create_res3 = requests.post(f"{API_URL}/videos/", json={
        "prompt": "Quick 3-step morning stretch routine",
        "duration": "15 seconds",
        "language": "English",
        "style": "Standard",
        "target_platform": "TikTok"
    })
    assert create_res3.status_code == 200
    vid3 = create_res3.json()["id"]
    requests.post(f"{API_URL}/videos/{vid3}/generate")
    wait_for_status(vid3, "PENDING_APPROVAL")

    edited_title = "Ultimate Morning Stretch Routine (Admin Edited)"
    edited_caption = "Feel energized in 60 seconds!"
    edited_tags = ["#morningroutine", "#wellness", "#stretch"]
    edit_res = requests.put(
        f"{API_URL}/videos/{vid3}/content",
        headers=ADMIN_HEADERS,
        json={"title": edited_title, "caption": edited_caption, "hashtags": edited_tags}
    )
    assert edit_res.status_code == 200, f"Content edit failed: {edit_res.text}"
    v3_edited = edit_res.json()
    assert v3_edited["title"] == edited_title, "Title was not updated"
    assert v3_edited["caption"] == edited_caption, "Caption was not updated"
    assert v3_edited["original_plan"] is not None, "original_plan was overwritten!"
    print(f"1. Content edited. Title='{v3_edited['title']}'. original_plan preserved.")

    app3_res = requests.post(f"{API_URL}/videos/{vid3}/approve", headers=ADMIN_HEADERS)
    assert app3_res.status_code == 200, f"Approve after edit failed: {app3_res.text}"
    assert app3_res.json()["status"] == "APPROVED"
    print("[PASS] TEST 4: EDIT -> APPROVE with preserved original_plan: PASSED")

    # ------------------------------------------------------------------ #
    # PATH 5: Invalid/Failed video & Authorization Enforcement
    # ------------------------------------------------------------------ #
    print("\n--- TEST 5: Failed / Invalid Video Validation & Authorization ---")

    # 5a. Approve with no generated video file
    create_res4 = requests.post(f"{API_URL}/videos/", json={
        "prompt": "Draft video with no generated file",
        "duration": "15 seconds"
    })
    assert create_res4.status_code == 200
    vid4 = create_res4.json()["id"]

    bad_app_res = requests.post(f"{API_URL}/videos/{vid4}/approve", headers=ADMIN_HEADERS)
    assert bad_app_res.status_code == 400, f"Expected 400, got {bad_app_res.status_code}: {bad_app_res.text}"
    print(f"1. Correctly blocked approval of missing video: {bad_app_res.json()['detail']}")

    # 5b. Viewer cannot approve (403)
    auth_fail_res = requests.post(f"{API_URL}/videos/{vid1}/approve", headers=VIEWER_HEADERS)
    assert auth_fail_res.status_code == 403, f"Expected 403, got {auth_fail_res.status_code}"
    print("2. Correctly enforced admin authorization: Viewer received 403 Forbidden.")

    print("[PASS] TEST 5: Invalid video rejection + Auth enforcement: PASSED")

    print("\n==================================================================")
    print("[FINAL] ALL 5 APPROVAL PATHS PASSED SUCCESSFULLY!")
    print("==================================================================")

if __name__ == "__main__":
    run_all_tests()

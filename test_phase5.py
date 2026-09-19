"""
Comprehensive Automated Test Suite for Phase 5.
Tests:
1. Token encryption / decryption security (Never plain text in DB).
2. Social provider abstraction and platform capability specifications ($0 cost).
3. Exact platform validation rules (YouTube, Instagram, TikTok constraints).
4. Social account connection, listing (safe metadata), and disconnect.
5. Publishing Configuration data tracking (Video -> Config -> Platform -> Account -> Metadata -> Status).
6. Negative validation tests (unapproved video, missing account, constraint violations).
7. Positive validation flow -> Video and Config transition to READY_TO_SCHEDULE!
"""

import os
import sqlite3
import requests
from social import SocialProviderRegistry, encrypt_token, decrypt_token
from api import database, models

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ADMIN_HEADERS = {"X-Admin-Role": "admin"}


def test_crypto_token_security():
    print("\n--- TEST 1: Token Encryption & Credential Security ---")
    raw_token = "ya29.a0AfH6SMD_secret_google_oauth_access_token_12345"
    raw_refresh = "1//0gXYZ_secret_refresh_token_67890"

    enc_token = encrypt_token(raw_token)
    enc_refresh = encrypt_token(raw_refresh)

    assert enc_token != raw_token, "Encrypted token must NOT equal plain text!"
    assert raw_token not in enc_token, "Raw secret must not leak inside ciphertext!"
    assert enc_refresh != raw_refresh
    assert raw_refresh not in enc_refresh

    # Decrypt round trip
    dec_token = decrypt_token(enc_token)
    dec_refresh = decrypt_token(enc_refresh)
    assert dec_token == raw_token, "Decrypted token must match original!"
    assert dec_refresh == raw_refresh, "Decrypted refresh token must match original!"

    # None handling
    assert encrypt_token(None) is None
    assert decrypt_token(None) is None
    print("   [OK] Fernet AES-128-CBC authenticated encryption verified.")


def test_platform_capabilities_and_zero_cost():
    print("\n--- TEST 2: Platform Capabilities & $0-Cost Verification ---")
    platforms = SocialProviderRegistry.list_all_platforms()
    plat_names = [p["platform"] for p in platforms]
    assert "youtube" in plat_names, "YouTube provider missing"
    assert "instagram" in plat_names, "Instagram provider missing"
    assert "tiktok" in plat_names, "TikTok provider missing"

    for p in platforms:
        assert p["is_cost_free"] is True, f"Platform {p['platform']} must be $0 cost!"
        assert len(p["limitations"]) > 0, f"Platform {p['platform']} must document official limitations"
        print(f"   [OK] Platform: {p['display_name']} | API: {p['official_api_name']} | $0 Cost: {p['is_cost_free']}")


def test_platform_validation_rules():
    print("\n--- TEST 3: Official Platform Validation Rules ---")
    
    # 1. YouTube
    yt_provider = SocialProviderRegistry.get_provider("youtube")
    # Valid
    valid_yt = {"title": "Top 5 Productivity Habits", "privacy": "public", "description": "Notes", "tags": ["habit", "work"]}
    is_v, errs = yt_provider.validate_publishing_metadata(valid_yt)
    assert is_v is True and len(errs) == 0, f"Valid YouTube failed: {errs}"

    # Invalid: Title > 100 chars
    long_title_yt = {"title": "A" * 105, "privacy": "public"}
    is_v, errs = yt_provider.validate_publishing_metadata(long_title_yt)
    assert is_v is False, "YouTube title > 100 chars must fail validation"
    assert any("exceeds max length of 100" in e for e in errs)

    # Invalid: Bad privacy
    bad_priv_yt = {"title": "Normal Title", "privacy": "friends_only"}
    is_v, errs = yt_provider.validate_publishing_metadata(bad_priv_yt)
    assert is_v is False, "YouTube invalid privacy must fail"
    assert any("privacy" in e.lower() for e in errs)

    # 2. Instagram
    ig_provider = SocialProviderRegistry.get_provider("instagram")
    valid_ig = {"caption": "Quick video tip! #ai #tools", "hashtags": ["#ai", "#tools"]}
    is_v, errs = ig_provider.validate_publishing_metadata(valid_ig)
    assert is_v is True and len(errs) == 0, f"Valid Instagram failed: {errs}"

    # Invalid: Caption > 2200 chars
    long_cap_ig = {"caption": "I" * 2250}
    is_v, errs = ig_provider.validate_publishing_metadata(long_cap_ig)
    assert is_v is False, "Instagram caption > 2200 chars must fail"
    assert any("exceeds max length of 2200" in e for e in errs)

    # Invalid: > 30 hashtags
    too_many_tags = {"caption": "Tags", "hashtags": [f"#tag{i}" for i in range(35)]}
    is_v, errs = ig_provider.validate_publishing_metadata(too_many_tags)
    assert is_v is False, "Instagram > 30 hashtags must fail"
    assert any("maximum allowed hashtags of 30" in e for e in errs)

    # 3. TikTok
    tt_provider = SocialProviderRegistry.get_provider("tiktok")
    valid_tt = {"caption": "Check this out! #fyp", "privacy": "PUBLIC_TO_EVERYONE"}
    is_v, errs = tt_provider.validate_publishing_metadata(valid_tt)
    assert is_v is True and len(errs) == 0, f"Valid TikTok failed: {errs}"

    # Invalid: Bad privacy
    bad_tt_priv = {"caption": "Cool clip", "privacy": "UNLISTED"}
    is_v, errs = tt_provider.validate_publishing_metadata(bad_tt_priv)
    assert is_v is False, "TikTok invalid privacy must fail"
    assert any("privacy" in e.lower() for e in errs)

    print("   [OK] YouTube, Instagram, and TikTok constraint validations verified.")


def test_social_account_management_and_encryption_in_db():
    print("\n--- TEST 4: Account Connection & Safe Metadata (Tokens NOT Plain in DB) ---")
    db = database.SessionLocal()
    try:
        # Connect YouTube Sandbox Account
        yt_acc = models.SocialAccount(
            user_id=1,
            platform="youtube",
            account_id="UC_test_yt_01",
            account_name="TechShorts Channel",
            account_handle="@techshorts",
            encrypted_access_token=encrypt_token("secret_yt_access_token_999"),
            encrypted_refresh_token=encrypt_token("secret_yt_refresh_token_888"),
            status="ACTIVE",
            is_mock=True,
            metadata_json={"avatar_url": "https://example.com/yt.png"}
        )
        db.add(yt_acc)

        # Connect Instagram Sandbox Account
        ig_acc = models.SocialAccount(
            user_id=1,
            platform="instagram",
            account_id="1784140000001",
            account_name="AI Studio Reels",
            account_handle="@aistudio_reels",
            encrypted_access_token=encrypt_token("secret_ig_token_777"),
            status="ACTIVE",
            is_mock=True,
            metadata_json={"avatar_url": "https://example.com/ig.png"}
        )
        db.add(ig_acc)

        # Connect TikTok Sandbox Account
        tt_acc = models.SocialAccount(
            user_id=1,
            platform="tiktok",
            account_id="tt_open_01",
            account_name="Viral Clips",
            account_handle="@viralclips",
            encrypted_access_token=encrypt_token("secret_tt_token_666"),
            status="ACTIVE",
            is_mock=True,
            metadata_json={"avatar_url": "https://example.com/tt.png"}
        )
        db.add(tt_acc)
        db.commit()

        # Direct SQL inspection: verify that raw plain-text tokens are NOT in sqlite db
        conn = sqlite3.connect("app.db")
        rows = conn.execute("SELECT platform, encrypted_access_token FROM social_accounts").fetchall()
        for plat, enc_val in rows:
            assert "secret_" not in enc_val, f"Raw secret leaked in database row for {plat}!"
            assert enc_val.startswith("gAAAAA"), f"Token is not properly Fernet-encrypted for {plat}!"
        conn.close()

        # API query: verify tokens are excluded from public responses
        res = requests.get(f"{API_URL}/social/accounts")
        assert res.status_code == 200
        accs = res.json()
        assert len(accs) >= 3
        for a in accs:
            assert "access_token" not in a
            assert "encrypted_access_token" not in a
            assert "encrypted_refresh_token" not in a
            assert "account_name" in a and "account_handle" in a

        print("   [OK] Connected accounts verified. Plaintext tokens are NEVER stored in DB or exposed via API.")
        return yt_acc.id, ig_acc.id, tt_acc.id
    finally:
        db.close()


def test_publishing_configuration_and_milestone():
    print("\n--- TEST 5: Publishing Configuration, Validation & READY_TO_SCHEDULE ---")
    db = database.SessionLocal()
    try:
        # Create a mock video file for validation
        test_video_dir = "assets/test_video_phase5"
        os.makedirs(test_video_dir, exist_ok=True)
        test_mp4_path = os.path.join(test_video_dir, "final.mp4")
        with open(test_mp4_path, "wb") as f:
            f.write(b"0" * 5000)

        # 1. Create an APPROVED test video
        video = models.Video(
            prompt="5 micro-habits that save 2 hours every day",
            title="5 Micro-Habits That Save 2 Hours Daily",
            caption="Transform your daily workflow with these 5 simple habits! #productivity #lifehacks",
            hashtags=["#productivity", "#lifehacks"],
            script="Here are five simple habits that can dramatically save your time every morning...",
            video_path=test_mp4_path,
            status=models.VideoStatus.APPROVED,
            owner_id=1
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        vid = video.id

        # Fetch accounts
        yt_acc = db.query(models.SocialAccount).filter(models.SocialAccount.platform == "youtube").first()
        ig_acc = db.query(models.SocialAccount).filter(models.SocialAccount.platform == "instagram").first()
        tt_acc = db.query(models.SocialAccount).filter(models.SocialAccount.platform == "tiktok").first()

        # 2. Negative Test A: Unapproved video rejection
        unapproved_video = models.Video(
            prompt="Unapproved video prompt",
            status=models.VideoStatus.DRAFT,
            owner_id=1
        )
        db.add(unapproved_video)
        db.commit()
        neg_res = requests.post(f"{API_URL}/videos/{unapproved_video.id}/publishing-config", json={"settings": []})
        assert neg_res.status_code == 400, "Should reject publishing config on unapproved video"
        print("   [OK] Unapproved video correctly rejected from publishing configuration.")

        # 3. Negative Test B: Constraint failure (e.g. YouTube title > 100 chars)
        bad_config_payload = {
            "settings": [
                {
                    "platform": "youtube",
                    "account_id": yt_acc.id,
                    "platform_metadata": {
                        "title": "A" * 120,  # Invalid: > 100 chars
                        "privacy": "public"
                    }
                }
            ]
        }
        requests.post(f"{API_URL}/videos/{vid}/publishing-config", json=bad_config_payload)
        val_res = requests.post(f"{API_URL}/videos/{vid}/publishing-config/validate")
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert val_data["is_valid"] is False
        assert "youtube" in val_data["errors"]
        print("   [OK] Constraint violations correctly flagged with structured platform errors.")

        # 4. Negative Test C: Missing connected account
        missing_acc_payload = {
            "settings": [
                {
                    "platform": "youtube",
                    "account_id": 999999,  # Nonexistent account
                    "platform_metadata": {"title": "Valid Title", "privacy": "public"}
                }
            ]
        }
        requests.post(f"{API_URL}/videos/{vid}/publishing-config", json=missing_acc_payload)
        val_res2 = requests.post(f"{API_URL}/videos/{vid}/publishing-config/validate")
        assert val_res2.status_code == 200
        val_data2 = val_res2.json()
        assert val_data2["is_valid"] is False
        assert any("connected account" in e.lower() for e in val_data2["errors"]["youtube"])
        print("   [OK] Missing or invalid account correctly caught during validation.")

        # 5. Positive Flow: Valid configurations across YouTube, Instagram, and TikTok
        good_payload = {
            "settings": [
                {
                    "platform": "youtube",
                    "account_id": yt_acc.id,
                    "platform_metadata": {
                        "title": "5 Micro-Habits That Save 2 Hours Daily",
                        "description": "5 Micro-habits that save 2 hours daily.\n\n#productivity #lifehacks",
                        "privacy": "public",
                        "tags": ["productivity", "lifehacks"]
                    }
                },
                {
                    "platform": "instagram",
                    "account_id": ig_acc.id,
                    "platform_metadata": {
                        "caption": "Transform your daily workflow with these 5 simple habits! #productivity #lifehacks",
                        "hashtags": ["#productivity", "#lifehacks"],
                        "share_to_feed": True
                    }
                },
                {
                    "platform": "tiktok",
                    "account_id": tt_acc.id,
                    "platform_metadata": {
                        "caption": "5 Micro-Habits That Save 2 Hours Daily #productivity #lifehacks",
                        "privacy": "PUBLIC_TO_EVERYONE",
                        "allow_comments": True,
                        "allow_duet": True,
                        "allow_stitch": True
                    }
                }
            ]
        }
        save_res = requests.post(f"{API_URL}/videos/{vid}/publishing-config", json=good_payload)
        assert save_res.status_code == 200, f"Saving config failed: {save_res.text}"

        # Run Validation
        validate_res = requests.post(f"{API_URL}/videos/{vid}/publishing-config/validate")
        assert validate_res.status_code == 200, f"Validation endpoint failed: {validate_res.text}"
        res_data = validate_res.json()
        assert res_data["is_valid"] is True, f"Expected validation to pass, got: {res_data}"
        assert res_data["status"] == "READY_TO_SCHEDULE"

        # Verify DB video status updated to READY_TO_SCHEDULE
        db.refresh(video)
        assert video.status == models.VideoStatus.READY_TO_SCHEDULE, f"Expected READY_TO_SCHEDULE, got {video.status}"

        # Verify via GET API endpoint
        v_check = requests.get(f"{API_URL}/videos/{vid}").json()
        assert v_check["status"] == "READY_TO_SCHEDULE"

        print("   [OK] All platforms validated successfully! Video transitioned to READY_TO_SCHEDULE!")

    finally:
        db.close()


def run_all_tests():
    print("==================================================================")
    print("[START] RUNNING PHASE 5 SOCIAL & PLATFORM SELECTION TESTS")
    print("==================================================================")
    test_crypto_token_security()
    test_platform_capabilities_and_zero_cost()
    test_platform_validation_rules()
    test_social_account_management_and_encryption_in_db()
    test_publishing_configuration_and_milestone()
    print("==================================================================")
    print("[SUCCESS] ALL PHASE 5 TESTS PASSED SUCCESSFULLY!")
    print("==================================================================")


if __name__ == "__main__":
    run_all_tests()

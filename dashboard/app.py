import os
import json
from datetime import datetime
import requests
import streamlit as st

st.set_page_config(page_title="AI Video Studio - Admin & Review", page_icon="🎬", layout="wide")
def get_api_url():
    if "API_URL" in os.environ:
        return os.environ["API_URL"]
    for port in [8000, 8001]:
        try:
            r = requests.get(f"http://127.0.0.1:{port}/health", timeout=0.5)
            if r.status_code == 200:
                return f"http://127.0.0.1:{port}"
        except Exception:
            pass
    return "http://127.0.0.1:8000"

API_URL = get_api_url()

# Custom styling for a modern, sleek dashboard
st.markdown("""
<style>
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }
    .badge-draft { background-color: #4a5568; color: #edf2f7; }
    .badge-generating { background-color: #2b6cb0; color: #ebf8ff; }
    .badge-generated { background-color: #319795; color: #e6fffa; }
    .badge-qa_pending { background-color: #d69e2e; color: #fffff0; }
    .badge-pending_approval { background-color: #dd6b20; color: #fffaf0; }
    .badge-approved { background-color: #38a169; color: #f0fff4; }
    .badge-ready_to_schedule { background-color: #3182ce; color: #ebf8ff; }
    .badge-rejected { background-color: #e53e3e; color: #fff5f5; }
    .badge-scheduled { background-color: #805ad5; color: #faf5ff; }
    .badge-published { background-color: #2c5282; color: #ebf8ff; }
    .badge-failed { background-color: #c53030; color: #fff5f5; }
    .qa-box {
        background-color: #1a202c;
        border-left: 4px solid #38a169;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------- #
# Sidebar: Navigation & Admin Authorization
# ---------------------------------------------------------------------- #
st.sidebar.title("🎬 Video Studio")
st.sidebar.markdown("**Phase 5: Social Connections & Platform Selection**")

# Authorization Control
st.sidebar.subheader("🔐 Access Control")
is_admin = st.sidebar.toggle("Admin Role", value=True, help="Toggle to switch between Admin and Viewer role.")
admin_role = "admin" if is_admin else "viewer"
admin_headers = {"X-Admin-Role": admin_role}

if is_admin:
    st.sidebar.success("Logged in as: **Authorized Admin**")
else:
    st.sidebar.warning("Role: **Viewer (Read-Only)**")

# Navigation
st.sidebar.subheader("Navigation")
nav_selection = st.sidebar.radio(
    "Go to",
    ["Overview", "Pending Approval", "My Videos / Projects", "Create Video", "Social Accounts", "Settings"],
    index=1
)

# API Health Check
def check_api_health():
    global API_URL
    API_URL = get_api_url()
    try:
        res = requests.get(f"{API_URL}/health", timeout=2)
        if res.status_code == 200:
            st.sidebar.caption(f"🟢 API Connected: `{API_URL}`")
        else:
            st.sidebar.caption(f"🔴 API Error on `{API_URL}`")
    except Exception:
        st.sidebar.caption(f"🔴 API Offline ({API_URL})")

check_api_health()

# Stable app state to avoid top-level session_state churn during reruns.
def get_app_state():
    if "app_state" not in st.session_state:
        st.session_state["app_state"] = {
            "created_video": None,
            "gen_started_for": None,
        }
    return st.session_state["app_state"]

# Helper to render status badge
def render_status_badge(status_str: str) -> str:
    status_clean = (status_str or "DRAFT").upper()
    badge_cls = f"badge-{status_clean.lower()}"
    return f"<span class='status-badge {badge_cls}'>{status_clean}</span>"

def render_audit_log(vid: int):
    try:
        res = requests.get(f"{API_URL}/videos/{vid}/audit_log", timeout=3)
        if res.status_code == 200:
            data = res.json()
            approvals = data.get("approvals", [])
            attempts = data.get("generation_attempts", [])
            
            with st.expander(f"📜 Audit Log & Version History (Attempts: {len(attempts)}, Reviews: {len(approvals)})"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 🛡️ Admin Review History")
                    if approvals:
                        for app in approvals:
                            st.write(f"- **{app['action']}** by Admin (`user_id={app.get('reviewer_id')}`) at `{app['reviewed_at']}`")
                            if app.get("rejection_reason"):
                                st.write(f"  *Reason:* `{app['rejection_reason']}`")
                            if app.get("comments"):
                                st.write(f"  *Notes:* {app['comments']}")
                    else:
                        st.caption("No admin review records yet.")
                with c2:
                    st.markdown("##### 🔄 Generation & Version History")
                    if attempts:
                        for att in attempts:
                            st.write(f"- **Attempt #{att['attempt_number']}**: {att['status']} (Stage: `{att['stage']}`) at `{att['started_at']}`")
                            if att.get('error_message'):
                                st.error(f"  Error: {att['error_message']}")
                    else:
                        st.caption("No generation attempts logged.")
    except Exception:
        pass


def _status_icon(status: str) -> str:
    status = (status or "pending").lower()
    return {
        "completed": "OK",
        "generating": "...",
        "failed": "FAIL",
        "pending": "WAIT",
    }.get(status, status.upper())


def render_visual_generation_status(video):
    status = video.get("visual_generation_status") or {}
    scenes = status.get("scenes") or {}
    provider = video.get("visual_provider") or status.get("provider") or "not selected"
    total = status.get("total_scenes") or len(scenes)
    current = status.get("current_scene") or 0

    st.markdown("#### Visual Generation")
    st.caption(f"Provider: `{provider}` | Visual style: `{video.get('visual_style') or 'realistic'}`")
    if total:
        if current:
            st.write(f"Generating Scene {current}/{total}" if video.get("generation_stage") == "VISUALS" else f"{total} scene visual(s)")
        cols = st.columns(min(max(total, 1), 5))
        for idx, key in enumerate(sorted(scenes, key=lambda k: int(k) if str(k).isdigit() else 999)):
            scene_status = scenes[key].get("status", "pending")
            cols[idx % len(cols)].metric(f"Scene {key}", _status_icon(scene_status))
    else:
        st.caption("Scene visuals have not started yet.")

    if status.get("fallback_used"):
        st.warning(f"Local visual generation fell back to the development mock provider: {status.get('fallback_reason')}")


def render_scene_visual_previews(video, key_prefix: str = ""):
    vid = video["id"]
    plan = video.get("plan") or {}
    scenes = plan.get("scenes", [])
    if not scenes:
        return

    render_visual_generation_status(video)
    st.markdown("#### Scene Visual Previews")
    try:
        res = requests.get(f"{API_URL}/videos/{vid}/scenes", timeout=3)
        assets = res.json() if res.status_code == 200 else []
    except Exception:
        assets = []
    assets_by_scene = {a.get("scene_number"): a for a in assets}

    prefix_str = f"{key_prefix}_" if key_prefix else ""
    for scene in scenes:
        scene_num = scene.get("scene_number")
        asset = assets_by_scene.get(scene_num, {})
        image_path = scene.get("image_path") or asset.get("image_path")
        status = scene.get("visual_status") or asset.get("status") or "pending"

        with st.expander(f"Scene {scene_num} - {_status_icon(status)}", expanded=bool(image_path)):
            c_img, c_meta = st.columns([1, 2])
            with c_img:
                if image_path and os.path.exists(image_path):
                    st.image(image_path, width="stretch")
                    if scene.get("is_mock_visual") or asset.get("is_mock"):
                        st.warning("Development mock visual. Configure the local provider for real AI images.")
                else:
                    st.info("No visual generated yet.")
            with c_meta:
                st.write(f"**Narration:** {scene.get('narration', '')}")
                st.write(f"**Visual prompt:** {scene.get('visual_prompt') or scene.get('visual_description', '')}")
                st.caption(f"Environment: {scene.get('environment', '')}")
                st.caption(f"Characters: {scene.get('characters', '')}")
                st.caption(f"Objects: {scene.get('objects', '')}")
                if st.button("Regenerate Scene", key=f"regen_scene_{prefix_str}{vid}_{scene_num}", disabled=not is_admin):
                    regen = requests.post(
                        f"{API_URL}/videos/{vid}/scenes/{scene_num}/regenerate",
                        headers=admin_headers,
                    )
                    if regen.status_code == 200:
                        st.success(f"Scene {scene_num} regeneration started.")
                        st.rerun()
                    else:
                        st.error(f"Could not regenerate scene {scene_num}: {regen.text}")


# ---------------------------------------------------------------------- #
# Phase 5: Publishing Settings & Platform Selection Widget
# ---------------------------------------------------------------------- #
def render_publishing_settings_widget(video, key_prefix: str = ""):
    vid = video["id"]
    prefix_str = f"{key_prefix}_" if key_prefix else ""
    with st.expander("🚀 Publish Settings & Platform Selection", expanded=(video.get("status") in ["APPROVED", "READY_TO_SCHEDULE"])):
        st.markdown("##### 📱 Select Social Media Platforms & Configure Metadata")
        st.caption("Official platform OAuth, $0-cost development, and strict platform compliance validation.")

        # 1. Fetch available connected accounts
        try:
            acc_res = requests.get(f"{API_URL}/social/accounts", timeout=3)
            accounts = acc_res.json() if acc_res.status_code == 200 else []
        except Exception:
            accounts = []

        # Group accounts by platform
        accounts_by_platform = {"youtube": [], "instagram": [], "tiktok": []}
        for acc in accounts:
            p = acc.get("platform", "").lower()
            if p in accounts_by_platform:
                accounts_by_platform[p].append(acc)

        # 2. Fetch existing publishing config if any
        try:
            conf_res = requests.get(f"{API_URL}/videos/{vid}/publishing-config", timeout=3)
            existing_config = conf_res.json() if conf_res.status_code == 200 else None
        except Exception:
            existing_config = None

        existing_settings = {}
        if existing_config and existing_config.get("settings"):
            for s in existing_config["settings"]:
                existing_settings[s["platform"].lower()] = s

        if existing_config and existing_config.get("status") == "READY_TO_SCHEDULE":
            st.success("🎉 **Publishing Configuration Validated! This video is READY TO SCHEDULE.**")

        # Platform Checkboxes
        st.markdown("**Select Platforms to Target:**")
        col_cb1, col_cb2, col_cb3 = st.columns(3)
        with col_cb1:
            use_yt = st.checkbox("📺 YouTube Shorts", value=("youtube" in existing_settings), key=f"cb_yt_{prefix_str}{vid}")
        with col_cb2:
            use_ig = st.checkbox("📸 Instagram Reels", value=("instagram" in existing_settings), key=f"cb_ig_{prefix_str}{vid}")
        with col_cb3:
            use_tt = st.checkbox("🎵 TikTok", value=("tiktok" in existing_settings), key=f"cb_tt_{prefix_str}{vid}")

        plan = video.get("plan") or {}
        base_title = video.get("title") or plan.get("title") or f"Video #{vid}"
        base_caption = video.get("caption") or plan.get("caption") or ""
        base_narration = video.get("script") or plan.get("complete_narration") or ""
        base_tags = video.get("hashtags") or plan.get("hashtags") or []
        tags_str = " ".join(base_tags) if isinstance(base_tags, list) else str(base_tags)

        selected_platforms_payload = []
        has_missing_account = False

        # --- YouTube Form ---
        if use_yt:
            st.markdown("---")
            st.markdown("##### 📺 YouTube Shorts Settings")
            yt_accounts = accounts_by_platform.get("youtube", [])
            if not yt_accounts:
                st.error("❌ **No connected YouTube account found!** Please connect an account on the **Social Accounts** page.")
                has_missing_account = True
            else:
                acc_options = {acc["id"]: f"{acc.get('account_name', 'YouTube Channel')} ({acc.get('account_handle', '')}) {'[Sandbox]' if acc.get('is_mock') else ''}" for acc in yt_accounts}
                yt_acc_id = st.selectbox("YouTube Channel", options=list(acc_options.keys()), format_func=lambda x: acc_options[x], key=f"yt_acc_{prefix_str}{vid}")

                yt_prev = (existing_settings.get("youtube") or {}).get("platform_metadata") or {}
                yt_title = st.text_input("Title (max 100 chars)", value=yt_prev.get("title", base_title)[:100], max_chars=100, key=f"yt_title_{prefix_str}{vid}")
                st.caption(f"Length: {len(yt_title)}/100 characters")

                default_desc = f"{base_caption}\n\n{tags_str}\n\n{base_narration}"
                yt_desc = st.text_area("Description (max 5000 chars)", value=yt_prev.get("description", default_desc)[:5000], height=90, key=f"yt_desc_{prefix_str}{vid}")

                priv_opts = ["public", "unlisted", "private"]
                default_priv = yt_prev.get("privacy", "public")
                yt_priv = st.selectbox("Privacy Status", priv_opts, index=priv_opts.index(default_priv) if default_priv in priv_opts else 0, key=f"yt_priv_{prefix_str}{vid}")

                selected_platforms_payload.append({
                    "platform": "youtube",
                    "account_id": yt_acc_id,
                    "platform_metadata": {
                        "title": yt_title,
                        "description": yt_desc,
                        "privacy": yt_priv,
                        "tags": [t.strip("#") for t in tags_str.split()]
                    }
                })

        # --- Instagram Form ---
        if use_ig:
            st.markdown("---")
            st.markdown("##### 📸 Instagram Reels Settings")
            ig_accounts = accounts_by_platform.get("instagram", [])
            if not ig_accounts:
                st.error("❌ **No connected Instagram account found!** Please connect a Professional Instagram account on the **Social Accounts** page.")
                has_missing_account = True
            else:
                acc_options = {acc["id"]: f"{acc.get('account_name', 'Instagram Account')} ({acc.get('account_handle', '')}) {'[Sandbox]' if acc.get('is_mock') else ''}" for acc in ig_accounts}
                ig_acc_id = st.selectbox("Instagram Account", options=list(acc_options.keys()), format_func=lambda x: acc_options[x], key=f"ig_acc_{prefix_str}{vid}")

                ig_prev = (existing_settings.get("instagram") or {}).get("platform_metadata") or {}
                default_ig_cap = f"{base_caption}\n\n{tags_str}".strip()
                ig_caption = st.text_area("Caption (max 2200 chars)", value=ig_prev.get("caption", default_ig_cap)[:2200], max_chars=2200, height=90, key=f"ig_cap_{prefix_str}{vid}")
                st.caption(f"Length: {len(ig_caption)}/2200 characters")

                ig_feed = st.checkbox("Share to Instagram Feed", value=ig_prev.get("share_to_feed", True), key=f"ig_feed_{prefix_str}{vid}")

                selected_platforms_payload.append({
                    "platform": "instagram",
                    "account_id": ig_acc_id,
                    "platform_metadata": {
                        "caption": ig_caption,
                        "hashtags": [t for t in tags_str.split() if t.startswith("#")],
                        "share_to_feed": ig_feed
                    }
                })

        # --- TikTok Form ---
        if use_tt:
            st.markdown("---")
            st.markdown("##### 🎵 TikTok Settings")
            tt_accounts = accounts_by_platform.get("tiktok", [])
            if not tt_accounts:
                st.error("❌ **No connected TikTok account found!** Please connect a TikTok account on the **Social Accounts** page.")
                has_missing_account = True
            else:
                acc_options = {acc["id"]: f"{acc.get('account_name', 'TikTok Account')} ({acc.get('account_handle', '')}) {'[Sandbox]' if acc.get('is_mock') else ''}" for acc in tt_accounts}
                tt_acc_id = st.selectbox("TikTok Account", options=list(acc_options.keys()), format_func=lambda x: acc_options[x], key=f"tt_acc_{prefix_str}{vid}")

                tt_prev = (existing_settings.get("tiktok") or {}).get("platform_metadata") or {}
                default_tt_cap = f"{base_caption} {tags_str}".strip()
                tt_caption = st.text_area("Post Caption (max 2200 chars)", value=tt_prev.get("caption", default_tt_cap)[:2200], max_chars=2200, height=80, key=f"tt_cap_{prefix_str}{vid}")
                st.caption(f"Length: {len(tt_caption)}/2200 characters")

                tt_priv_opts = ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"]
                cur_tt_priv = tt_prev.get("privacy", "PUBLIC_TO_EVERYONE")
                tt_priv = st.selectbox("Privacy Level", tt_priv_opts, index=tt_priv_opts.index(cur_tt_priv) if cur_tt_priv in tt_priv_opts else 0, key=f"tt_priv_{prefix_str}{vid}")

                tc1, tc2, tc3 = st.columns(3)
                with tc1:
                    tt_comments = st.checkbox("Allow Comments", value=tt_prev.get("allow_comments", True), key=f"tt_comm_{prefix_str}{vid}")
                with tc2:
                    tt_duet = st.checkbox("Allow Duet", value=tt_prev.get("allow_duet", True), key=f"tt_duet_{prefix_str}{vid}")
                with tc3:
                    tt_stitch = st.checkbox("Allow Stitch", value=tt_prev.get("allow_stitch", True), key=f"tt_stitch_{prefix_str}{vid}")

                selected_platforms_payload.append({
                    "platform": "tiktok",
                    "account_id": tt_acc_id,
                    "platform_metadata": {
                        "caption": tt_caption,
                        "privacy": tt_priv,
                        "allow_comments": tt_comments,
                        "allow_duet": tt_duet,
                        "allow_stitch": tt_stitch
                    }
                })

        st.markdown("")
        if use_yt or use_ig or use_tt:
            if st.button("💾 Save & Validate Configuration", key=f"btn_save_val_{prefix_str}{vid}", type="primary", width="stretch"):
                if has_missing_account:
                    st.error("Cannot validate: One or more selected platforms are missing a connected account.")
                else:
                    with st.spinner("Validating platform configurations and verifying account states..."):
                        save_payload = {"settings": selected_platforms_payload}
                        save_res = requests.post(f"{API_URL}/videos/{vid}/publishing-config", json=save_payload)
                        if save_res.status_code == 200:
                            val_res = requests.post(f"{API_URL}/videos/{vid}/publishing-config/validate")
                            if val_res.status_code == 200:
                                val_data = val_res.json()
                                if val_data.get("is_valid"):
                                    st.success(f"🎉 {val_data.get('message')}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Validation Failed: {val_data.get('message')}")
                                    err_dict = val_data.get("errors", {})
                                    for p_k, p_v in err_dict.items():
                                        for err in p_v:
                                            st.error(f"• **{p_k.upper()}**: {err}")
                            else:
                                st.error(f"Validation request failed: {val_res.text}")
                        else:
                            st.error(f"Failed to save configuration: {save_res.text}")
        else:
            st.info("Check one or more platforms above to configure publishing.")


# ---------------------------------------------------------------------- #
# Phase 5: Approve & Publish Widget (shown in Pending Approval)
# ---------------------------------------------------------------------- #
_PLATFORM_ICONS = {"youtube": "📺", "instagram": "📸", "tiktok": "🎵"}
_PLATFORM_LABELS = {"youtube": "YouTube Shorts", "instagram": "Instagram Reels", "tiktok": "TikTok"}


def render_publication_results(vid: int):
    """Show per-platform publication status with retry buttons for FAILED platforms."""
    try:
        res = requests.get(f"{API_URL}/videos/{vid}/publications", timeout=4)
        if res.status_code != 200:
            return
        pubs = res.json()
        if not pubs:
            return
    except Exception:
        return

    st.markdown("#### 📊 Publishing Results")
    status_icons = {
        "PUBLISHED":    "🟢",
        "FAILED":       "🔴",
        "NOT_SELECTED": "⚪",
        "QUEUED":       "🕐",
        "PUBLISHING":   "🔄",
    }

    cols = st.columns(len(pubs))
    for i, pub in enumerate(pubs):
        plat = pub.get("platform", "?")
        status = pub.get("status", "UNKNOWN")
        icon = status_icons.get(status, "❓")
        label = _PLATFORM_LABELS.get(plat, plat.capitalize())
        plat_icon = _PLATFORM_ICONS.get(plat, "🌐")
        with cols[i]:
            st.markdown(f"**{plat_icon} {label}**")
            st.markdown(f"{icon} **{status}**")
            if pub.get("post_url"):
                st.markdown(f"[View Post]({pub['post_url']})")
            if pub.get("platform_post_id"):
                st.caption(f"Post ID: `{pub['platform_post_id']}`")
            if pub.get("error_message") and status == "FAILED":
                st.caption(f"Error: {pub['error_message'][:120]}")
            # Retry button only for FAILED platforms
            if status == "FAILED":
                if st.button(f"🔁 Retry {label}", key=f"retry_{vid}_{plat}", type="secondary"):
                    with st.spinner(f"Retrying {label}..."):
                        retry_res = requests.post(
                            f"{API_URL}/videos/{vid}/publications/{plat}/retry",
                            headers=admin_headers,
                            params={"use_sandbox": "false"}
                        )
                        if retry_res.status_code == 200:
                            result = retry_res.json()
                            new_status = result.get("status", "UNKNOWN")
                            if new_status == "PUBLISHED":
                                st.success(f"✅ {label} published successfully!")
                            else:
                                st.error(f"Retry failed: {result.get('error_message', 'Unknown error')}")
                        else:
                            st.error(f"Retry request failed: {retry_res.text[:200]}")
                    st.rerun()
            if pub.get("attempt_count", 0) > 0:
                st.caption(f"Attempts: {pub['attempt_count']}")


def render_approve_and_publish_widget(video: dict, key_prefix: str = ""):
    """
    Shown in Pending Approval. Lets the user:
    1. Select which platforms to publish to (only connected accounts are selectable).
    2. Configure YouTube privacy and TikTok privacy.
    3. Click 'Approve & Publish' — approves the video and publishes to selected platforms.
    4. Shows per-platform result (Published / Failed / Not Selected) with retry buttons.
    """
    vid = video["id"]
    prefix_str = f"{key_prefix}_" if key_prefix else ""

    # Fetch connected accounts
    try:
        acc_res = requests.get(f"{API_URL}/social/accounts", timeout=3)
        accounts = acc_res.json() if acc_res.status_code == 200 else []
    except Exception:
        accounts = []

    accounts_by_platform: dict = {"youtube": [], "instagram": [], "tiktok": []}
    for acc in accounts:
        p = acc.get("platform", "").lower()
        if p in accounts_by_platform:
            accounts_by_platform[p].append(acc)

    # Check if publications already exist (i.e. already approved & published)
    try:
        pub_res = requests.get(f"{API_URL}/videos/{vid}/publications", timeout=3)
        existing_pubs = pub_res.json() if pub_res.status_code == 200 else []
    except Exception:
        existing_pubs = []

    if existing_pubs:
        # Already published — show results and retry buttons
        render_publication_results(vid)
        return

    st.markdown("---")
    st.markdown("### 🚀 Approve & Publish")
    st.caption("Select the platforms to publish this video to, then click **Approve & Publish**.")

    # Platform selection UI
    st.markdown("#### Publishing Platforms")
    plat_cols = st.columns(3)
    platform_selections = {}
    has_missing_account = False

    for i, platform in enumerate(["instagram", "tiktok", "youtube"]):
        with plat_cols[i]:
            icon = _PLATFORM_ICONS[platform]
            label = _PLATFORM_LABELS[platform]
            connected = accounts_by_platform.get(platform, [])

            if connected:
                acc_names = ", ".join(
                    acc.get("account_handle") or acc.get("account_name") or "Account"
                    for acc in connected[:1]
                )
                st.markdown(f"**{icon} {label}**")
                st.caption(f"🟢 Connected: `{acc_names}`")
                selected = st.checkbox(f"Publish to {label}", key=f"chk_{prefix_str}{platform}_{vid}", value=False)
                platform_selections[platform] = selected
            else:
                st.markdown(f"**{icon} {label}**")
                st.warning("⚠️ Not connected")
                st.caption("Go to **Social Accounts** to connect.")
                st.checkbox(f"Publish to {label}", key=f"chk_{prefix_str}{platform}_{vid}", value=False, disabled=True)
                platform_selections[platform] = False

    selected_platforms = [p for p, v in platform_selections.items() if v]

    # Advanced options (collapsed)
    with st.expander("⚙️ Advanced Privacy Options"):
        yt_priv_opts = ["public", "unlisted", "private"]
        yt_privacy = st.selectbox("YouTube Visibility", yt_priv_opts, index=0, key=f"yt_priv_ap_{prefix_str}{vid}")
        tt_priv_opts = ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"]
        tt_privacy = st.selectbox("TikTok Privacy", tt_priv_opts, index=0, key=f"tt_priv_ap_{prefix_str}{vid}")
        use_sandbox = st.checkbox(
            "🧪 Safe Test Mode (Sandbox)",
            value=False,
            key=f"sandbox_ap_{prefix_str}{vid}",
            help="Uses mock provider — no real publishing. Safe for testing the full workflow without credentials."
        )

    # Approve & Publish button
    st.markdown("")
    can_approve = is_admin and len(selected_platforms) > 0
    btn_label = "✅ Approve & Publish" if selected_platforms else "✅ Approve & Publish (select a platform above)"

    if st.button(
        btn_label,
        key=f"btn_approve_publish_{prefix_str}{vid}",
        type="primary",
        disabled=not can_approve,
    ):
        if not is_admin:
            st.error("Action denied: Admin authorization required.")
        elif not selected_platforms:
            st.warning("Please select at least one platform to publish to.")
        else:
            with st.spinner(f"Approving and publishing to {', '.join(selected_platforms)}..."):
                payload = {
                    "selected_platforms": selected_platforms,
                    "youtube_privacy": yt_privacy,
                    "tiktok_privacy": tt_privacy,
                    "use_sandbox": use_sandbox,
                }
                try:
                    resp = requests.post(
                        f"{API_URL}/videos/{vid}/approve-and-publish",
                        json=payload,
                        headers=admin_headers,
                        timeout=120
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        summary = result.get("summary", {})
                        published_count = sum(1 for s in summary.values() if s == "PUBLISHED")
                        failed_count = sum(1 for p in selected_platforms if summary.get(p) == "FAILED")

                        if published_count > 0:
                            st.success(f"🎉 Video approved! {result.get('message', '')}")
                        else:
                            st.warning(f"⚠️ Video approved but publishing failed: {result.get('message', '')}")

                        if failed_count > 0:
                            st.error(f"❌ {failed_count} platform(s) failed to publish. Use Retry below.")
                        st.rerun()
                    else:
                        try:
                            err = resp.json().get("detail", resp.text)
                        except Exception:
                            err = resp.text
                        st.error(f"Approve & Publish failed: {err}")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    if not is_admin:
        st.info("ℹ️ Admin authorization required to approve and publish.")


# ---------------------------------------------------------------------- #
# PAGE 1: Overview
# ---------------------------------------------------------------------- #
if nav_selection == "Overview":
    st.title("📊 Studio Overview")
    st.markdown("Real-time summary of videos across all lifecycle stages.")

    try:
        res = requests.get(f"{API_URL}/videos/")
        if res.status_code == 200:
            videos = res.json()
            
            # Count statuses
            counts = {
                "DRAFT": 0, "GENERATING": 0, "GENERATED": 0, "QA_PENDING": 0,
                "PENDING_APPROVAL": 0, "APPROVED": 0, "READY_TO_SCHEDULE": 0,
                "REJECTED": 0, "SCHEDULED": 0, "PUBLISHED": 0, "FAILED": 0
            }
            for v in videos:
                s = v.get("status", "DRAFT").upper()
                counts[s] = counts.get(s, 0) + 1

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Pending Approval", counts["PENDING_APPROVAL"])
            c2.metric("Approved", counts["APPROVED"])
            c3.metric("Ready to Schedule", counts["READY_TO_SCHEDULE"])
            c4.metric("Generating", counts["GENERATING"] + counts["QA_PENDING"])
            c5.metric("Total Projects", len(videos))

            st.divider()
            st.subheader("Lifecycle Breakdown")
            cols = st.columns(5)
            cols[0].metric("Drafts", counts["DRAFT"])
            cols[1].metric("Generated", counts["GENERATED"])
            cols[2].metric("Rejected", counts["REJECTED"])
            cols[3].metric("Scheduled", counts["SCHEDULED"])
            cols[4].metric("Failed", counts["FAILED"])
            
            st.info("💡 Go to **Pending Approval** to review videos, or configure publishing on **Approved** videos.")
        else:
            st.error("Failed to fetch videos from server.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ---------------------------------------------------------------------- #
# PAGE 2: Pending Approval (Core Phase 4 Milestone)
# ---------------------------------------------------------------------- #
elif nav_selection == "Pending Approval":
    st.title("🔍 Admin Review & Approvals")
    st.markdown("Review AI-generated videos, inspect QA validation, edit metadata, and **Approve**, **Reject**, or **Regenerate**.")

    try:
        res = requests.get(f"{API_URL}/videos/?status=PENDING_APPROVAL")
        if res.status_code == 200:
            pending_videos = res.json()
            if not pending_videos:
                st.success("🎉 No videos currently pending approval! All caught up.")
                st.info("To create and generate a new video, go to **Create Video** or browse **My Videos / Projects**.")
            else:
                st.write(f"Showing **{len(pending_videos)}** video(s) requiring admin action:")
                
                for video in pending_videos:
                    vid = video["id"]
                    plan = video.get("plan") or {}
                    title = video.get("title") or plan.get("title", f"Video #{vid}")
                    
                    with st.container():
                        st.markdown(f"### 🎬 {title} (ID: `{vid}`)")
                        st.markdown(render_status_badge(video.get("status")), unsafe_allow_html=True)
                        st.write("")

                        col_video, col_meta = st.columns([1, 1])

                        # Left Column: Video Preview & Technical Specs
                        with col_video:
                            st.subheader("Video Preview")
                            video_path = video.get("video_path")
                            if video_path and os.path.exists(video_path):
                                st.video(video_path)
                                st.caption(f"📁 Path: `{video_path}`")
                            else:
                                st.warning("⚠️ Video file is not yet available or in rendering.")

                            # QA / Validation Information Box
                            st.subheader("QA & Validation Report")
                            qa_report = video.get("qa_report")
                            if qa_report:
                                checks = qa_report.get("checks", {})
                                passed = qa_report.get("passed", False)
                                
                                if passed:
                                    st.success(f"✅ QA Status: PASSED\n\n{qa_report.get('summary', 'All validation checks passed.')}")
                                else:
                                    st.error(f"❌ QA Status: FAILED - {qa_report.get('error', 'Validation error')}")

                                with st.expander("Detailed QA Checks"):
                                    st.json(checks)
                            else:
                                st.info("No QA report available.")

                            # Technical Specifications
                            st.subheader("Technical Specifications")
                            q1, q2, q3 = st.columns(3)
                            q1.metric("Resolution", video.get("resolution", "1080x1920"))
                            q2.metric("Target Platform", video.get("target_platform", "TikTok"))
                            q3.metric("Duration Spec", video.get("duration", "30-60s"))

                        # Right Column: Content Metadata & Scene Breakdown
                        with col_meta:
                            st.subheader("Content & Metadata")
                            st.write(f"**Short Description:** {plan.get('short_description', 'N/A')}")
                            st.write(f"**Caption:** {video.get('caption') or plan.get('caption', 'N/A')}")
                            
                            tags = video.get("hashtags") or plan.get("hashtags", [])
                            if isinstance(tags, list):
                                st.write(f"**Hashtags:** {' '.join(tags)}")
                            else:
                                st.write(f"**Hashtags:** {tags}")
                                
                            st.write(f"**Suggested Music:** {plan.get('suggested_background_music', 'N/A')}")
                            
                            st.markdown("#### Script & Full Narration")
                            narration_text = video.get("script") or plan.get("complete_narration", "")
                            st.text_area("Full Narration", value=narration_text, height=100, disabled=True, key=f"narr_{vid}")

                            st.markdown("#### Scene Breakdown")
                            scenes = plan.get("scenes", [])
                            if scenes:
                                for s in scenes:
                                    with st.expander(f"Scene {s.get('scene_number', '?')} ({s.get('scene_duration', '')})"):
                                        st.write(f"**Visual:** {s.get('visual_prompt') or s.get('visual_description', '')}")
                                        st.caption(f"Environment: {s.get('environment', '')}")
                                        st.caption(f"Characters: {s.get('characters', '')}")
                                        st.caption(f"Objects: {s.get('objects', '')}")
                                        st.write(f"**Narration:** {s.get('narration', '')}")
                            else:
                                st.caption("No scene breakdown details.")

                            render_scene_visual_previews(video, key_prefix="pending")

                        st.divider()

                        # ---------------------------------------------------------------------- #
                        # Admin Actions: APPROVE, REJECT, REGENERATE, EDIT CONTENT
                        # ---------------------------------------------------------------------- #
                        st.subheader("⚡ Review Actions")
                        
                        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 1.2])

                        # Action 1: APPROVE
                        with btn_col1:
                            if st.button("✅ APPROVE", key=f"btn_app_{vid}", type="primary", width="stretch"):
                                if not is_admin:
                                    st.error("Action denied: Admin authorization required.")
                                else:
                                    with st.spinner("Validating and approving video..."):
                                        app_res = requests.post(f"{API_URL}/videos/{vid}/approve", headers=admin_headers)
                                        if app_res.status_code == 200:
                                            st.success("🎉 Video APPROVED successfully! (Not published)")
                                            st.rerun()
                                        else:
                                            err = app_res.json().get("detail", app_res.text)
                                            st.error(f"Approval failed: {err}")

                        # Action 2: REJECT (with optional reason)
                        with btn_col2:
                            with st.popover("❌ REJECT", width="stretch"):
                                st.markdown("### Reject Video")
                                reject_reason = st.text_input("Rejection Reason (Optional)", placeholder="e.g. Visual pacing too fast, audio volume low", key=f"rej_input_{vid}")
                                if st.button("Confirm Rejection", key=f"confirm_rej_{vid}", type="secondary"):
                                    if not is_admin:
                                        st.error("Action denied: Admin authorization required.")
                                    else:
                                        with st.spinner("Recording rejection..."):
                                            rej_res = requests.post(
                                                f"{API_URL}/videos/{vid}/reject",
                                                headers=admin_headers,
                                                json={"action": "REJECT", "rejection_reason": reject_reason}
                                            )
                                            if rej_res.status_code == 200:
                                                st.warning(f"Video #{vid} marked as REJECTED.")
                                                st.rerun()
                                            else:
                                                err = rej_res.json().get("detail", rej_res.text)
                                                st.error(f"Rejection failed: {err}")

                        # Action 3: REGENERATE
                        with btn_col3:
                            if st.button("🔄 REGENERATE", key=f"btn_regen_{vid}", width="stretch"):
                                with st.spinner("Starting regeneration pipeline..."):
                                    regen_res = requests.post(f"{API_URL}/videos/{vid}/regenerate", headers=admin_headers)
                                    if regen_res.status_code == 200:
                                        st.info("Regeneration started in background!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to start regeneration.")

                        # Action 4: EDIT CONTENT
                        with btn_col4:
                            edit_expander = st.popover("✏️ EDIT CONTENT", width="stretch")
                            with edit_expander:
                                st.markdown("### Edit Video Content")
                                st.caption("Edits update the working plan while keeping the original AI generation preserved.")
                                
                                edit_title = st.text_input("Title", value=title, key=f"edit_title_{vid}")
                                edit_desc = st.text_input("Short Description", value=plan.get("short_description", ""), key=f"edit_desc_{vid}")
                                edit_narr = st.text_area("Narration / Script", value=narration_text, height=120, key=f"edit_narr_{vid}")
                                edit_caption = st.text_area("Caption", value=video.get("caption") or plan.get("caption", ""), height=80, key=f"edit_cap_{vid}")
                                
                                existing_tags_str = " ".join(tags) if isinstance(tags, list) else str(tags)
                                edit_tags_input = st.text_input("Hashtags (space separated)", value=existing_tags_str, key=f"edit_tags_{vid}")

                                if st.button("Save Changes", key=f"save_edit_{vid}", type="primary"):
                                    with st.spinner("Saving edits..."):
                                        new_tags_list = [t for t in edit_tags_input.split() if t.startswith("#") or len(t) > 0]
                                        # Format hashtags nicely
                                        new_tags_list = [t if t.startswith("#") else f"#{t}" for t in new_tags_list]
                                        
                                        edit_payload = {
                                            "title": edit_title,
                                            "short_description": edit_desc,
                                            "complete_narration": edit_narr,
                                            "caption": edit_caption,
                                            "hashtags": new_tags_list
                                        }
                                        save_res = requests.put(
                                            f"{API_URL}/videos/{vid}/content",
                                            headers=admin_headers,
                                            json=edit_payload
                                        )
                                        if save_res.status_code == 200:
                                            st.success("Changes saved successfully!")
                                            st.rerun()
                                        else:
                                            err = save_res.json().get("detail", save_res.text)
                                            st.error(f"Failed to save changes: {err}")

                        # ---------------------------------------------------------------- #
                        # Phase 5: Approve & Publish — Platform Selection + Publishing
                        # ---------------------------------------------------------------- #
                        render_approve_and_publish_widget(video, key_prefix=f"pending_{vid}")

                        # Render Audit Log & Version History
                        render_audit_log(vid)
                        st.write("---")
        else:
            st.error("Failed to load pending videos.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ---------------------------------------------------------------------- #
# PAGE 3: My Videos / Projects (All Lifecycle Statuses)
# ---------------------------------------------------------------------- #
elif nav_selection == "My Videos / Projects":
    st.title("📁 My Videos & Projects")
    st.markdown("Filter and inspect projects across every pipeline and review state.")

    tabs = st.tabs([
        "All", "Drafts", "Generating", "Pending Approval",
        "Rejected", "Approved", "Ready to Schedule", "Scheduled", "Published", "Failed"
    ])

    status_filter_map = {
        0: None,
        1: "DRAFT",
        2: "GENERATING",
        3: "PENDING_APPROVAL",
        4: "REJECTED",
        5: "APPROVED",
        6: "READY_TO_SCHEDULE",
        7: "SCHEDULED",
        8: "PUBLISHED",
        9: "FAILED"
    }

    try:
        for tab_idx, tab in enumerate(tabs):
            with tab:
                status_to_query = status_filter_map[tab_idx]
                url = f"{API_URL}/videos/"
                if status_to_query:
                    url += f"?status={status_to_query}"

                res = requests.get(url)
                if res.status_code == 200:
                    vids = res.json()
                    if not vids:
                        st.info("No projects found in this category.")
                    else:
                        for v in vids:
                            vid = v["id"]
                            v_status = v.get("status", "DRAFT").upper()
                            v_title = v.get("title") or (v.get("plan") or {}).get("title", f"Video #{vid}")
                            
                            with st.expander(f"{v_title} — Status: {v_status} (ID: #{vid})", expanded=(v_status in ["PENDING_APPROVAL", "REJECTED", "APPROVED", "READY_TO_SCHEDULE"])):
                                st.markdown(render_status_badge(v_status), unsafe_allow_html=True)
                                st.write("")

                                c_left, c_right = st.columns([1, 1])
                                with c_left:
                                    st.write(f"**Prompt:** {v.get('prompt')}")
                                    st.write(f"**Language:** {v.get('language')} | **Style:** {v.get('style')}")
                                    st.write(f"**Created:** {v.get('created_at')}")
                                    if v.get("updated_at"):
                                        st.write(f"**Last Updated:** {v.get('updated_at')}")

                                    if v.get("rejection_reason"):
                                        st.error(f"🛑 **Rejection Reason:** {v.get('rejection_reason')}")

                                    if v.get("error_message"):
                                        st.error(f"⚠️ **Error:** {v.get('error_message')}")

                                with c_right:
                                    video_path = v.get("video_path")
                                    if video_path and os.path.exists(video_path):
                                        st.video(video_path)
                                    else:
                                        st.caption("No video file generated yet.")

                                render_scene_visual_previews(v, key_prefix=f"tab_{tab_idx}")

                                # Phase 5: Publishing Settings on Approved and Ready to Schedule videos
                                if v_status in ["APPROVED", "READY_TO_SCHEDULE"]:
                                    render_publishing_settings_widget(v, key_prefix=f"tab_{tab_idx}")

                                # Contextual Quick Actions per status
                                st.markdown("##### Quick Actions")
                                qcol1, qcol2, qcol3 = st.columns(3)
                                
                                if v_status in ["DRAFT", "REJECTED", "FAILED"]:
                                    if qcol1.button(f"Generate Video #{vid}", key=f"tab_gen_{tab_idx}_{vid}"):
                                        requests.post(f"{API_URL}/videos/{vid}/generate")
                                        st.rerun()

                                if v_status == "PENDING_APPROVAL":
                                    if qcol1.button(f"Approve #{vid}", key=f"tab_app_{tab_idx}_{vid}", type="primary"):
                                        if is_admin:
                                            requests.post(f"{API_URL}/videos/{vid}/approve", headers=admin_headers)
                                            st.rerun()
                                        else:
                                            st.error("Admin privilege required.")

                                if v_status in ["APPROVED", "READY_TO_SCHEDULE", "PUBLISHED"]:
                                    if video_path and os.path.exists(video_path):
                                        with open(video_path, "rb") as file_handle:
                                            qcol1.download_button(
                                                label="Download MP4",
                                                data=file_handle,
                                                file_name=f"video_{vid}.mp4",
                                                mime="video/mp4",
                                                key=f"dl_{tab_idx}_{vid}"
                                            )

                                # Render Audit Log & Version History
                                render_audit_log(vid)
    except Exception as e:
        st.error(f"Failed to fetch videos: {e}")


# ---------------------------------------------------------------------- #
# PAGE 4: Create Video
# ---------------------------------------------------------------------- #
elif nav_selection == "Create Video":
    st.title("💡 Create New Video Plan")
    st.markdown("Input your video concept. The system creates the initial script and scenes in **DRAFT** status.")

    with st.form("create_video_form"):
        prompt = st.text_area(
            "Video Topic / Script Prompt",
            placeholder="e.g. 3 surprising habits of ultra-productive software engineers",
            height=100
        )
        c1, c2 = st.columns(2)
        with c1:
            duration = st.selectbox("Duration", ["15 seconds", "30-60 seconds", "1-3 minutes"], index=1)
            target_platform = st.selectbox("Target Platform", ["TikTok", "Instagram Reels", "YouTube Shorts"], index=0)
        with c2:
            language = st.selectbox("Language", ["English", "Spanish", "French", "German"], index=0)
            style = st.selectbox("Style/Tone", ["Educational", "Dramatic", "Humorous", "Corporate"], index=0)
            visual_style = st.selectbox("Visual Style", ["realistic", "cinematic", "3d", "illustration", "anime", "minimal"], index=0)

        submitted = st.form_submit_button("Generate Plan & Script", type="primary")

    app_state = get_app_state()

    if submitted:
        if not prompt.strip():
            st.warning("Please enter a video topic or prompt.")
        else:
            with st.spinner("Generating AI Script and Scene Plan..."):
                try:
                    payload = {
                        "prompt": prompt,
                        "duration": duration,
                        "language": language,
                        "style": style,
                        "target_platform": target_platform,
                        "visual_style": visual_style,
                    }
                    res = requests.post(f"{API_URL}/videos/", json=payload)
                    if res.status_code == 200:
                        app_state["created_video"] = res.json()
                        app_state["gen_started_for"] = None
                        st.rerun()
                    else:
                        st.error(f"Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection failed to {API_URL}: {e}")

    # Render created video plan and Start Generation button OUTSIDE the submitted block
    if app_state.get("created_video"):
        data = app_state["created_video"]
        vid = data["id"]
        plan = data.get("plan") or {}

        st.divider()
        st.success(f"✅ Video plan created in **DRAFT** status! (Project ID: `#{vid}`)")

        c_plan, c_actions = st.columns([2, 1])
        with c_plan:
            st.subheader(plan.get("title", f"Video #{vid}"))
            st.write(f"**Short Description:** {plan.get('short_description', 'N/A')}")
            st.write(f"**Complete Narration:** {plan.get('complete_narration', '')}")
            st.write(f"**Caption:** {plan.get('caption', '')}")
            tags = plan.get("hashtags", [])
            st.write(f"**Hashtags:** {' '.join(tags) if isinstance(tags, list) else tags}")

            scenes = plan.get("scenes", [])
            if scenes:
                with st.expander(f"🎬 Scene Breakdown ({len(scenes)} scenes)"):
                    for s in scenes:
                        st.markdown(f"**Scene {s.get('scene_number', '?')}** ({s.get('scene_duration', '')}s):")
                        st.caption(f"Visual: {s.get('visual_prompt') or s.get('visual_description', '')}")
                        st.caption(f"Narration: {s.get('narration', '')}")

        with c_actions:
            st.markdown("### Next Steps")
            
            if app_state.get("gen_started_for") == vid:
                st.info(f"⏳ **Video #{vid} is generating in the background!**\n\nThe pipeline is creating the TTS audio, generating subtitles, compiling visuals, and burning captions.")
                st.success("👉 Go to **Pending Approval** in the sidebar to review the video once rendering completes.")
            else:
                if st.button("🚀 Start Video Generation Now", key=f"start_gen_{vid}", type="primary", width="stretch"):
                    with st.spinner("Initiating rendering pipeline..."):
                        try:
                            gen_res = requests.post(f"{API_URL}/videos/{vid}/generate")
                            if gen_res.status_code == 200:
                                app_state["gen_started_for"] = vid
                                st.rerun()
                            else:
                                st.error(f"Failed to start generation: {gen_res.text}")
                        except Exception as e:
                            st.error(f"Error calling backend at {API_URL}: {e}")

            st.write("")
            if st.button("Create Another Video", key="btn_create_another_vid", type="secondary", width="stretch"):
                app_state["created_video"] = None
                app_state["gen_started_for"] = None
                st.rerun()


# ---------------------------------------------------------------------- #
# PAGE 5: Social Media Accounts (Phase 5)
# ---------------------------------------------------------------------- #
elif nav_selection == "Social Accounts":
    st.title("🌐 Connected Social Accounts & Platform Management")
    st.markdown("Connect, manage, and verify official social media accounts for multi-platform video publishing. **$0-cost, official OAuth only, encrypted token storage.**")

    # 1. Platform Status & Developer Requirements
    st.subheader("Official Platform Status & Capabilities")
    try:
        plat_res = requests.get(f"{API_URL}/social/platforms", timeout=3)
        platforms_info = plat_res.json() if plat_res.status_code == 200 else []
    except Exception:
        platforms_info = []

    p_cols = st.columns(3)
    platform_icons = {"youtube": "📺", "instagram": "📸", "tiktok": "🎵"}
    for idx, p_data in enumerate(platforms_info):
        p_name = p_data.get("platform", "")
        with p_cols[idx % 3]:
            icon = platform_icons.get(p_name, "🌐")
            cfg_status = "🟢 Configured" if p_data.get("is_configured") else "🟡 Requires App Registration"
            st.markdown(f"#### {icon} {p_data.get('display_name')}")
            st.caption(f"**Official API:** {p_data.get('official_api_name')}")
            st.write(f"**Status:** {cfg_status}")
            st.write(f"**Cost:** $0 Free Developer Quota")
            st.write(f"**Max Length:** {p_data.get('max_title_length') or p_data.get('max_caption_length')} chars")
            
            with st.expander("Platform Notes & Quotas"):
                if p_data.get("required_env_vars"):
                    st.write(f"**Required Env Keys:** `{', '.join(p_data['required_env_vars'])}`")
                for lim in p_data.get("limitations", []):
                    st.caption(f"• {lim}")

    st.divider()

    # 2. Currently Connected Accounts
    st.subheader("Connected Accounts")
    try:
        acc_res = requests.get(f"{API_URL}/social/accounts", timeout=3)
        connected_accounts = acc_res.json() if acc_res.status_code == 200 else []
    except Exception:
        connected_accounts = []

    if not connected_accounts:
        st.info("ℹ️ No social media accounts connected yet. Use the connection options below to connect accounts.")
    else:
        for acc in connected_accounts:
            acc_id = acc["id"]
            p_clean = acc.get("platform", "").lower()
            p_icon = platform_icons.get(p_clean, "🌐")
            acc_name = acc.get("account_name") or "Unnamed Account"
            acc_handle = acc.get("account_handle") or ""
            is_mock = acc.get("is_mock", False)
            badge_mode = "[Sandbox / Dev Account]" if is_mock else "[Official OAuth]"

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"**{p_icon} {p_clean.upper()} — {acc_name}** (`{acc_handle}`)")
                st.caption(f"Mode: `{badge_mode}` | Status: **{acc.get('status')}** | Linked: `{acc.get('created_at', '')[:19]}`")
            with col_btn:
                if st.button("Disconnect", key=f"btn_disc_{acc_id}", type="secondary"):
                    del_res = requests.delete(f"{API_URL}/social/accounts/{acc_id}")
                    if del_res.status_code == 200:
                        st.success(f"Disconnected {acc_name}.")
                        st.rerun()
                    else:
                        st.error(f"Failed to disconnect: {del_res.text}")
            st.write("---")

    st.divider()

    # 3. Connect a Social Account
    st.subheader("Connect a New Account")
    conn_tabs = st.tabs(["🚀 Quick Sandbox Connect (Zero-Config Test)", "🔐 Official OAuth Connect"])

    with conn_tabs[0]:
        st.markdown("**Test the entire publishing integration without waiting for external developer portal approvals.**")
        st.caption("Creates an isolated sandbox connection. Strictly enforces genuine platform validation rules (title length, caption limit, hashtags, privacy levels) and cryptographically encrypts credentials.")

        with st.form("sandbox_connect_form"):
            sb_platform = st.selectbox("Select Platform", ["youtube", "instagram", "tiktok"], format_func=lambda x: f"{platform_icons.get(x, '')} {x.capitalize()}")
            default_names = {
                "youtube": ("TechStudio Shorts", "@techstudio_shorts"),
                "instagram": ("Creative Reels Hub", "@creativereels.hub"),
                "tiktok": ("Viral Clips Studio", "@viralclips_studio")
            }
            d_name, d_handle = default_names.get(sb_platform, ("Test Account", "@test_account"))
            sb_name = st.text_input("Account / Channel Name", value=d_name)
            sb_handle = st.text_input("Handle / Username", value=d_handle)
            sb_submit = st.form_submit_button("Connect Sandbox Account", type="primary")

        if sb_submit:
            with st.spinner("Connecting sandbox account and encrypting credentials..."):
                payload = {
                    "platform": sb_platform,
                    "account_name": sb_name,
                    "account_handle": sb_handle
                }
                res = requests.post(f"{API_URL}/social/accounts/sandbox", json=payload)
                if res.status_code == 200:
                    st.success(f"🎉 Successfully connected sandbox account for {sb_platform.capitalize()}!")
                    st.rerun()
                else:
                    st.error(f"Connection failed: {res.text}")

    with conn_tabs[1]:
        st.markdown("**Connect with your live, official social media accounts using OAuth2.**")
        st.caption("Requires registered developer credentials in your `.env` file. Only official platform APIs are used; credentials are never stored in plain text.")

        oauth_plat = st.selectbox("Platform to Authorize", ["youtube", "instagram", "tiktok"], key="oauth_plat_select", format_func=lambda x: f"{platform_icons.get(x, '')} {x.capitalize()}")
        redirect_uri = "http://localhost:8000/social/oauth/callback/" + oauth_plat

        if st.button("Generate Official OAuth Link", key="btn_gen_oauth"):
            try:
                auth_res = requests.get(f"{API_URL}/social/oauth/authorize/{oauth_plat}?redirect_uri={redirect_uri}")
                if auth_res.status_code == 200:
                    auth_data = auth_res.json()
                    auth_url = auth_data.get("authorization_url")
                    st.markdown(f"👉 [**Click here to authorize on {oauth_plat.capitalize()}**]({auth_url})")
                    st.info(f"Authorization URL: `{auth_url}`")
                else:
                    st.error(f"Cannot generate OAuth link: {auth_res.text}")
            except Exception as e:
                st.error(f"Error: {e}")

        st.markdown("##### Manual Authorization Code Exchange")
        st.caption("If redirected to localhost callback, paste the authorization code below:")
        auth_code_input = st.text_input("OAuth Code (from provider callback URL)", key="oauth_code_input")
        if st.button("Exchange Code & Link Account", key="btn_exchange_code"):
            if not auth_code_input.strip():
                st.warning("Please paste an authorization code.")
            else:
                try:
                    cb_res = requests.get(
                        f"{API_URL}/social/oauth/callback/{oauth_plat}",
                        params={"code": auth_code_input.strip(), "redirect_uri": redirect_uri}
                    )
                    if cb_res.status_code == 200:
                        st.success("🎉 Official account connected and credentials encrypted successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to exchange code: {cb_res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")


# ---------------------------------------------------------------------- #
# PAGE 6: Settings & API Keys
# ---------------------------------------------------------------------- #
elif nav_selection == "Settings":
    st.title("⚙️ Studio Settings")
    st.markdown("Configure LLM Providers, Social Media OAuth Credentials, and Encryption Keys.")

    st.subheader("LLM Providers")
    st.info("""
    **Multi-Provider Waterfall Strategy:**
    1. **Groq API** (`GROQ_API_KEY`): Fast inference with generous free tier (Llama 3.3 70B).
    2. **Gemini API** (`GEMINI_API_KEY`): Google GenAI (Flash 3.6).
    3. **Intelligent Fallback Generator**: Automatically used when API keys are unconfigured or rate-limited.
    """)

    st.subheader("Visual Generation Provider")
    try:
        visual_res = requests.get(f"{API_URL}/visual/provider-status", timeout=3)
        if visual_res.status_code == 200:
            visual = visual_res.json()
            st.write(f"**Active provider:** `{visual.get('provider')}`")
            st.write(f"**Selected model:** `{visual.get('model')}`")
            st.write(f"**Status:** {visual.get('message')}")
            st.caption(
                f"GPU required: {visual.get('requires_gpu')} | "
                f"Recommended VRAM: {visual.get('recommended_vram_gb')} GB | "
                f"Recommended RAM: {visual.get('recommended_ram_gb')} GB"
            )
        else:
            st.warning(f"Visual provider status unavailable: {visual_res.text}")
    except Exception as exc:
        st.warning(f"Visual provider status unavailable: {exc}")

    st.markdown("""
    ```bash
    # Real local AI images, free/open-source
    VISUAL_PROVIDER=local
    VISUAL_MODEL=stabilityai/sd-turbo

    # Development fallback only; visibly watermarked as not AI-generated
    VISUAL_PROVIDER=mock
    ```
    """)

    st.subheader("Official Social Media OAuth Credentials ($0-Cost)")
    st.markdown("""
    To configure official social media accounts, register free developer apps and add their client credentials to `.env`:

    ```bash
    # YouTube (Google Cloud Console -> Enable YouTube Data API v3 -> OAuth 2.0 Web Client)
    YOUTUBE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
    YOUTUBE_CLIENT_SECRET=GOCSPX-...

    # Instagram (Meta for Developers -> App Type Business -> Instagram Graph API)
    META_APP_ID=your-meta-app-id
    META_APP_SECRET=your-meta-app-secret

    # TikTok (TikTok for Developers -> Create App -> Content Posting API)
    TIKTOK_CLIENT_KEY=your-tiktok-client-key
    TIKTOK_CLIENT_SECRET=your-tiktok-client-secret

    # Credential Encryption Key (Optional - 32 URL-safe base64 bytes; auto-generated if omitted)
    ENCRYPTION_KEY=your-fernet-encryption-key
    ```
    """)

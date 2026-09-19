import streamlit as st
import requests

st.set_page_config(page_title="AI Video Dashboard", page_icon="🎥", layout="wide")

API_URL = "http://127.0.0.1:8000"

st.title("🎥 AI Video Automation Dashboard")
st.markdown("Welcome to the Admin Dashboard. Manage video generation, approvals, and scheduling.")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Create Video", "Approvals", "Scheduled Posts"])

def check_api_health():
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            st.sidebar.success("API Status: Online")
        else:
            st.sidebar.error("API Status: Error")
    except requests.exceptions.ConnectionError:
        st.sidebar.error("API Status: Offline (Start the FastAPI server)")

check_api_health()

if page == "Dashboard":
    st.header("Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Videos", value="0")
    with col2:
        st.metric(label="Pending Approvals", value="0")
    with col3:
        st.metric(label="Scheduled Posts", value="0")

elif page == "Create Video":
    st.header("Generate New Video Plan")
    
    with st.form("video_form"):
        prompt = st.text_area("Video Topic / Prompt", placeholder="A 30-second TikTok about space exploration with a dramatic voiceover")
        
        col1, col2 = st.columns(2)
        with col1:
            duration = st.selectbox("Duration", ["15 seconds", "30-60 seconds", "1-3 minutes", "3+ minutes"], index=1)
            target_platform = st.selectbox("Target Platform", ["TikTok", "Instagram Reels", "YouTube Shorts", "YouTube Standard", "Any"], index=0)
        with col2:
            language = st.selectbox("Language", ["English", "Spanish", "French", "German", "Other"], index=0)
            style = st.selectbox("Style/Tone", ["Standard", "Dramatic", "Humorous", "Educational", "Corporate"], index=0)
            
        submitted = st.form_submit_button("Generate Plan")
        
    if submitted:
        if prompt:
            with st.spinner("Generating video plan using LLM... This may take a few seconds."):
                try:
                    payload = {
                        "prompt": prompt,
                        "duration": duration,
                        "language": language,
                        "style": style,
                        "target_platform": target_platform
                    }
                    response = requests.post(f"{API_URL}/videos/", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("Video plan generated successfully!")
                        
                        plan = data.get("plan", {})
                        if plan:
                            st.subheader(plan.get("title", "Untitled"))
                            st.write(f"**Description:** {plan.get('short_description', '')}")
                            st.write(f"**Music:** {plan.get('suggested_background_music', '')}")
                            st.write(f"**Caption:** {plan.get('caption', '')}")
                            st.write(f"**Hashtags:** {' '.join(plan.get('hashtags', []))}")
                            
                            st.markdown("### Script & Narration")
                            st.info(plan.get("complete_narration", ""))
                            
                            st.markdown("### Scene Breakdown")
                            for scene in plan.get("scenes", []):
                                with st.expander(f"Scene {scene.get('scene_number')} ({scene.get('scene_duration')})"):
                                    st.write(f"**Visual:** {scene.get('visual_description')}")
                                    st.write(f"**Narration:** {scene.get('narration')}")
                    else:
                        error_detail = response.json().get('detail', response.text) if 'application/json' in response.headers.get('content-type', '') else response.text
                        st.error(f"Failed to generate: {error_detail}")
                except Exception as e:
                    st.error(f"Error connecting to API: {e}")
        else:
            st.warning("Please enter a prompt.")

elif page == "Approvals":
    st.header("Video Approvals & Generation")
    
    try:
        response = requests.get(f"{API_URL}/videos/")
        if response.status_code == 200:
            videos = response.json()
            if not videos:
                st.info("No videos currently in the system.")
            else:
                for video in videos:
                    # Sort videos by newest first (descending id) if we want, but list order is fine
                    with st.expander(f"Video {video['id']} - Status: {video['status'].upper()}", expanded=True):
                        plan = video.get("plan", {})
                        if plan:
                            st.write(f"**Title:** {plan.get('title', 'Untitled')}")
                            st.write(f"**Prompt:** {video.get('prompt', '')}")
                        
                        if video['status'] == 'needs_review':
                            if st.button("Approve & Generate Video", key=f"gen_{video['id']}"):
                                gen_res = requests.post(f"{API_URL}/videos/{video['id']}/generate")
                                if gen_res.status_code == 200:
                                    st.success("Generation started!")
                                    st.rerun()
                                else:
                                    st.error("Failed to start generation")
                                    
                        elif video['status'] == 'generating':
                            stage = video.get('generation_stage', 'NOT_STARTED')
                            st.info(f"Video is currently being generated. Stage: **{stage}**... This may take a few minutes.")
                            if st.button("Refresh Status", key=f"ref_{video['id']}"):
                                st.rerun()
                                
                        elif video['status'] == 'approved' or video['status'] == 'published':
                            st.success("Video generated successfully!")
                            video_path = video.get('video_path')
                            if video_path:
                                video_url = f"{API_URL}/{video_path}"
                                st.video(video_url)
                                st.markdown(f"[Download Video]({video_url})")
                                
                        elif video['status'] == 'error':
                            failed_stage = video.get('generation_stage', 'NOT_STARTED')
                            st.error(f"Generation failed at stage **{failed_stage}**: {video.get('error_message')}")
                            if st.button("Regenerate / Resume", key=f"regen_{video['id']}"):
                                gen_res = requests.post(f"{API_URL}/videos/{video['id']}/generate")
                                if gen_res.status_code == 200:
                                    st.success("Regeneration started!")
                                    st.rerun()
                                else:
                                    st.error("Failed to start regeneration")
        else:
            st.error("Failed to fetch videos from the backend.")
    except Exception as e:
        st.error(f"Error connecting to API: {e}")

elif page == "Scheduled Posts":
    st.header("Scheduled Posts")
    st.info("No scheduled posts.")

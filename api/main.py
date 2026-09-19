from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import json
import os
from . import models, schemas, database
from services.llm.agent import generate_video_plan
from services.tts.generator import generate_voiceover
from services.visuals.mock_generator import generate_mock_scene_image
from services.subtitles.transcriber import generate_subtitles
from services.video_processing.composer import compose_video

# Create the database tables on startup
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="AI Video Automation API")

# Serve assets folder
os.makedirs("assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/")
def read_root():
    return {"message": "Welcome to the AI Social Media Video Automation API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running smoothly!"}

# Example CRUD for videos
@app.post("/videos/", response_model=schemas.VideoResponse)
def create_video(video: schemas.VideoCreate, db: Session = Depends(database.get_db)):
    # 1. Create initial pending video record
    try:
        db_video = models.Video(
            prompt=video.prompt, 
            duration=video.duration,
            language=video.language,
            style=video.style,
            target_platform=video.target_platform,
            owner_id=1,
            status=models.VideoStatus.GENERATING
        ) 
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error during video creation: {str(e)}")
    
    # 2. Call LLM Service (Synchronous for now to return immediately in response)
    try:
        plan = generate_video_plan(
            prompt=video.prompt,
            duration=video.duration,
            language=video.language,
            style=video.style,
            target_platform=video.target_platform
        )
        
        # 3. Save structured plan to DB
        db_video.plan = plan.model_dump()
        db_video.script = plan.complete_narration
        db_video.status = models.VideoStatus.NEEDS_REVIEW
        db.commit()
        db.refresh(db_video)
        
    except ValueError as e:
        # e.g., missing API key
        db_video.status = models.VideoStatus.ERROR
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        db_video.status = models.VideoStatus.ERROR
        db.commit()
        raise HTTPException(status_code=500, detail=f"LLM Generation failed: {str(e)}")
    
    return db_video

def run_video_pipeline(video_id: int):
    db = database.SessionLocal()
    try:
        video = db.query(models.Video).filter(models.Video.id == video_id).first()
        if not video or not video.plan:
            return
            
        try:
            video.status = models.VideoStatus.GENERATING
            db.commit()
            
            plan = video.plan
            base_dir = f"assets/video_{video_id}"
            
            # Helper to check if a stage needs to run
            def should_run(stage_name: str) -> bool:
                stages = ["NOT_STARTED", "VOICEOVER", "SUBTITLES", "VISUALS", "COMPOSING", "DONE"]
                try:
                    current_idx = stages.index(video.generation_stage)
                    target_idx = stages.index(stage_name)
                    return current_idx <= target_idx
                except ValueError:
                    return True

            # 1. Voiceover
            if should_run("VOICEOVER"):
                video.generation_stage = "VOICEOVER"
                db.commit()
                audio_path = os.path.join(base_dir, "voiceover.mp3")
                generate_voiceover(plan.get("complete_narration", ""), audio_path)
                video.audio_path = audio_path
                db.commit()
            
            # 2. Subtitles
            if should_run("SUBTITLES"):
                video.generation_stage = "SUBTITLES"
                db.commit()
                # Use existing audio path
                audio_path = video.audio_path or os.path.join(base_dir, "voiceover.mp3")
                srt_path = generate_subtitles(audio_path, base_dir, "voiceover")
                video.subtitles_path = srt_path
                db.commit()
            
            # 3. Visuals
            if should_run("VISUALS"):
                video.generation_stage = "VISUALS"
                db.commit()
                image_paths = []
                durations = []
                for i, scene in enumerate(plan.get("scenes", [])):
                    img_path = os.path.join(base_dir, f"scene_{i}.jpg")
                    generate_mock_scene_image(scene.get("visual_description", ""), img_path)
                    image_paths.append(img_path)
                    durations.append(scene.get("scene_duration", "3"))
                
                # Store paths in DB or just infer them in the next step
                # For simplicity, we can infer them from the plan in the next step
                
            # 4. Compose
            if should_run("COMPOSING"):
                video.generation_stage = "COMPOSING"
                db.commit()
                # Rebuild paths if resuming
                image_paths = [os.path.join(base_dir, f"scene_{i}.jpg") for i in range(len(plan.get("scenes", [])))]
                durations = [scene.get("scene_duration", "3") for scene in plan.get("scenes", [])]
                audio_path = video.audio_path or os.path.join(base_dir, "voiceover.mp3")
                srt_path = video.subtitles_path or os.path.join(base_dir, "voiceover.srt")
                
                final_mp4 = os.path.join(base_dir, "final.mp4")
                compose_video(image_paths, durations, audio_path, srt_path, final_mp4)
                video.video_path = final_mp4
                
                video.generation_stage = "DONE"
                video.status = models.VideoStatus.APPROVED
                video.error_message = None
                db.commit()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            video.status = models.VideoStatus.ERROR
            video.error_message = str(e)
            db.commit()
    finally:
        db.close()

@app.post("/videos/{video_id}/generate")
def start_generation(video_id: int, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
        
    background_tasks.add_task(run_video_pipeline, video_id)
    return {"status": "started"}

@app.get("/videos/", response_model=List[schemas.VideoResponse])
def get_videos(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    videos = db.query(models.Video).offset(skip).limit(limit).all()
    return videos

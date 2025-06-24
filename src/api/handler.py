from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import subprocess, sys
from src.bootstrap.logger import get_logger
from src.bootstrap.settings import settings

app = FastAPI()
logger = get_logger("api")

class IngestRequest(BaseModel):
    videos: list[str] | None = None
    twitter: list[str] | None = None
    ig: list[str] | None = None

@app.post("/ingest")
def ingest(req: IngestRequest, bg: BackgroundTasks):
    logger.info(f"Received ingest request: {req}")
    cmd = [sys.executable, "-m", "src.worker.ingest_worker"]
    if req.videos:
        cmd += ["--videos"] + req.videos
    if req.twitter:
        cmd += ["--twitter"] + req.twitter
    if req.ig:
        cmd += ["--ig"] + req.ig
    logger.info(f"Queuing background task: {cmd}")
    bg.add_task(subprocess.run, cmd)
    return {"status": "queued", "cmd": cmd}

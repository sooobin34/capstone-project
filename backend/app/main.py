from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from pathlib import Path

from app.api.alerts import router as alerts_router
from app.api.daily_summaries import router as daily_summaries_router
from app.api.dashboard import router as dashboard_router
from app.api.mrv_reports import router as mrv_reports_router
from app.api.nodes import router as nodes_router
from app.api.sensor_logs import router as sensor_logs_router
from app.api.fields import router as fields_router
from app.api.lora_webhook import router as lora_webhook_router
from app.api import validations
from app.core.database import engine


# 모델 import
from app.models.alert import Alert
from app.models.awd_daily_summary import AwdDailySummary
from app.models.iot_node import IotNode
from app.models.mrv_report import MrvReport
from app.models.sensor_log import SensorLog
from app.models.validation_record import ValidationRecord

app = FastAPI(title="AWD Backend Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://jeonbuk-mrv.vercel.app",
        "https://capstone-project-theta-amber.vercel.app",
    
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(nodes_router)
app.include_router(sensor_logs_router)
app.include_router(alerts_router)
app.include_router(daily_summaries_router)
app.include_router(mrv_reports_router)
app.include_router(dashboard_router)
app.include_router(fields_router)
app.include_router(validations.router)
app.include_router(lora_webhook_router)

# =========================
# Starter 버전 (유료 + Disk 사용)
# 나중에 Starter + Persistent Disk(/var/data) 다시 쓸 때 이걸 사용
# =========================
# UPLOAD_ROOT = Path("/var/data/uploads")

# =========================
# Free 버전 (디스크 없이 임시 uploads 폴더 사용)
# 현재 Free 플랜으로 내리기 위해 이걸 사용
# =========================
UPLOAD_ROOT = Path("uploads")

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploads")

@app.get("/")
def root():
    return {"message": "AWD Backend Server Running"}


@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "message": "DB 연결 성공",
        "result": value
    }


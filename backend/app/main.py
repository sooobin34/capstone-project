from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.alerts import router as alerts_router
from app.api.daily_summaries import router as daily_summaries_router
from app.api.dashboard import router as dashboard_router
from app.api.mrv_reports import router as mrv_reports_router
from app.api.nodes import router as nodes_router
from app.api.sensor_logs import router as sensor_logs_router
from app.api.fields import router as fields_router
from app.core.database import engine

# 모델 import는 유지해도 되고, 안 써도 됨
from app.models.alert import Alert
from app.models.awd_daily_summary import AwdDailySummary
from app.models.iot_node import IotNode
from app.models.mrv_report import MrvReport
from app.models.sensor_log import SensorLog

app = FastAPI(title="AWD Backend Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # 나중에 프론트 배포 주소 생기면 여기에 추가
        # "https://프론트주소.onrender.com",
    ],
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
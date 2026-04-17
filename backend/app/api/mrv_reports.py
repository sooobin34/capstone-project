from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.api.deps import get_db
from app.models.awd_daily_summary import AwdDailySummary
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.mrv_report import MrvReport
from app.schemas.mrv_report import (
    MrvReportCreate,
    MrvReportStatusUpdate,
)
from app.utils.response import success_response

router = APIRouter(prefix="/mrv-reports", tags=["MRV Reports"])

ALLOWED_MRV_STATUSES = {"IN_PROGRESS", "COMPLETED"}


def get_month_range(report_month: str) -> tuple[date, date]:
    year, month = map(int, report_month.split("-"))

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return start_date, end_date


def get_validation_data(report: MrvReport) -> dict:
    return {
        "validation_method": report.validation_method or "미입력",
        "validation_sample_count": report.validation_sample_count or 0,
        "validation_match_count": report.validation_match_count or 0,
        "validation_accuracy": float(report.validation_accuracy) if report.validation_accuracy is not None else 0,
        "validation_note": report.validation_note or "검증 정보 미입력"
    }


@router.post("")
def create_mrv_report(payload: MrvReportCreate, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    existing_report = (
        db.query(MrvReport)
        .filter(
            MrvReport.field_id == payload.field_id,
            MrvReport.report_month == payload.report_month
        )
        .first()
    )
    if existing_report:
        raise HTTPException(status_code=400, detail="해당 논의 해당 월 MRV 리포트가 이미 존재합니다.")

    start_date, end_date = get_month_range(payload.report_month)

    summaries = (
        db.query(AwdDailySummary)
        .join(IotNode, IotNode.id == AwdDailySummary.node_id)
        .filter(
            IotNode.field_id == payload.field_id,
            AwdDailySummary.record_date >= start_date,
            AwdDailySummary.record_date < end_date
        )
        .all()
    )

    if not summaries:
        raise HTTPException(status_code=404, detail="해당 논의 해당 월 일일 요약 데이터가 없습니다.")

    total_awd_cycles = sum(1 for summary in summaries if summary.daily_status == "DRY")
    flood_days = sum(1 for summary in summaries if summary.daily_status == "FLOODED")

    carbon_reduction = (
        Decimal(total_awd_cycles) * Decimal("15.25")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    report = MrvReport(
        field_id=payload.field_id,
        report_month=payload.report_month,
        total_awd_cycles=total_awd_cycles,
        flood_days=flood_days,
        status="IN_PROGRESS",
        carbon_reduction=carbon_reduction,
        validation_method=payload.validation_method,
        validation_sample_count=payload.validation_sample_count or 0,
        validation_match_count=payload.validation_match_count or 0,
        validation_accuracy=payload.validation_accuracy,
        validation_note=payload.validation_note
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return success_response(report, "MRV 보고서 생성 성공")


@router.get("")
def get_mrv_reports(
    field_id: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(MrvReport, Field.field_name).join(Field, Field.id == MrvReport.field_id)

    if field_id is not None:
        query = query.filter(MrvReport.field_id == field_id)

    rows = query.order_by(MrvReport.created_at.desc()).all()

    reports = []
    for report, field_name in rows:
        reports.append({
            "id": report.id,
            "field_id": report.field_id,
            "field_name": field_name,
            "report_month": report.report_month,
            "total_awd_cycles": report.total_awd_cycles,
            "flood_days": report.flood_days,
            "status": report.status,
            "carbon_reduction": report.carbon_reduction,
            "validation_method": report.validation_method,
            "validation_sample_count": report.validation_sample_count,
            "validation_match_count": report.validation_match_count,
            "validation_accuracy": report.validation_accuracy,
            "validation_note": report.validation_note,
            "created_at": report.created_at,
        })

    return success_response(reports, "MRV 보고서 조회 성공")


@router.patch("/{report_id}/status")
def update_mrv_report_status(
    report_id: int,
    payload: MrvReportStatusUpdate,
    db: Session = Depends(get_db)
):
    if payload.status not in ALLOWED_MRV_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="status는 IN_PROGRESS 또는 COMPLETED만 가능합니다."
        )

    report = db.query(MrvReport).filter(MrvReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="해당 report_id가 존재하지 않습니다.")

    report.status = payload.status

    db.commit()
    db.refresh(report)

    return success_response(report, "MRV 보고서 상태 변경 성공")


@router.get("/{report_id}/download/pdf")
def download_mrv_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.query(MrvReport).filter(MrvReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="해당 report_id가 존재하지 않습니다.")

    field = db.query(Field).filter(Field.id == report.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 보고서의 논 정보가 존재하지 않습니다.")

    validation = get_validation_data(report)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    line_gap = 24

    pdf.setTitle(f"mrv_report_{report.id}")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "MRV Report")
    y -= 40

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Field Name: {field.field_name}")
    y -= line_gap
    pdf.drawString(50, y, f"Report Month: {report.report_month}")
    y -= line_gap
    pdf.drawString(50, y, f"AWD Cycles: {report.total_awd_cycles}")
    y -= line_gap
    pdf.drawString(50, y, f"Flood Days: {report.flood_days}")
    y -= line_gap
    pdf.drawString(50, y, f"Carbon Reduction: {report.carbon_reduction}")
    y -= line_gap
    pdf.drawString(50, y, f"Status: {report.status}")
    y -= line_gap
    pdf.drawString(50, y, f"Created At: {report.created_at}")
    y -= 36

    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(50, y, "Validation (V)")
    y -= 28

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Validation Method: {validation['validation_method']}")
    y -= line_gap
    pdf.drawString(50, y, f"Validation Sample Count: {validation['validation_sample_count']}")
    y -= line_gap
    pdf.drawString(50, y, f"Validation Match Count: {validation['validation_match_count']}")
    y -= line_gap
    pdf.drawString(50, y, f"Validation Accuracy: {validation['validation_accuracy']}")
    y -= line_gap
    pdf.drawString(50, y, f"Validation Note: {validation['validation_note']}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    filename = f"mrv_report_{report.id}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{report_id}/download/excel")
def download_mrv_report_excel(report_id: int, db: Session = Depends(get_db)):
    report = db.query(MrvReport).filter(MrvReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="해당 report_id가 존재하지 않습니다.")

    field = db.query(Field).filter(Field.id == report.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 보고서의 논 정보가 존재하지 않습니다.")

    validation = get_validation_data(report)

    workbook = Workbook()

    summary_sheet = workbook.active
    summary_sheet.title = "MRV Summary"
    summary_sheet.append([
        "field_name",
        "report_month",
        "total_awd_cycles",
        "flood_days",
        "carbon_reduction",
        "status",
        "created_at"
    ])
    summary_sheet.append([
        field.field_name,
        report.report_month,
        report.total_awd_cycles,
        report.flood_days,
        float(report.carbon_reduction) if report.carbon_reduction is not None else None,
        report.status,
        str(report.created_at)
    ])

    validation_sheet = workbook.create_sheet(title="Validation")
    validation_sheet.append([
        "validation_method",
        "validation_sample_count",
        "validation_match_count",
        "validation_accuracy",
        "validation_note"
    ])
    validation_sheet.append([
        validation["validation_method"],
        validation["validation_sample_count"],
        validation["validation_match_count"],
        validation["validation_accuracy"],
        validation["validation_note"]
    ])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    filename = f"mrv_report_{report.id}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
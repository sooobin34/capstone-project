import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
from collections import Counter, defaultdict
from math import ceil

router = APIRouter(prefix="/mrv-reports", tags=["MRV Reports"])

ALLOWED_MRV_STATUSES = {"IN_PROGRESS", "COMPLETED"}

def register_korean_font():
    """
    Windows 우선: 맑은 고딕 사용
    없으면 프로젝트 내 fonts/NanumGothic.ttf 사용
    """
    candidate_paths = [
        r"C:\Windows\Fonts\malgun.ttf",
        os.path.join(os.path.dirname(__file__), "..", "..", "fonts", "NanumGothic.ttf"),
    ]

    for path in candidate_paths:
        normalized = os.path.abspath(path)
        if os.path.exists(normalized):
            pdfmetrics.registerFont(TTFont("KoreanFont", normalized))
            return "KoreanFont"

    raise RuntimeError("사용 가능한 한글 폰트를 찾지 못했습니다. malgun.ttf 또는 NanumGothic.ttf 경로를 확인하세요.")


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

def summarize_status_counts(summaries: list[AwdDailySummary]) -> dict:
    counter = Counter(summary.daily_status for summary in summaries)
    return {
        "OVERFLOODED": counter.get("OVERFLOODED", 0),
        "FLOODED": counter.get("FLOODED", 0),
        "DRYING": counter.get("DRYING", 0),
        "DRY": counter.get("DRY", 0),
    }


def group_summaries_by_week(summaries: list[AwdDailySummary]) -> list[tuple[int, list[AwdDailySummary]]]:
    summaries = sorted(summaries, key=lambda x: x.record_date)
    grouped: dict[int, list[AwdDailySummary]] = defaultdict(list)

    for summary in summaries:
        week_no = ceil(summary.record_date.day / 7)
        grouped[week_no].append(summary)

    return sorted(grouped.items(), key=lambda x: x[0])


def make_weekly_summary_text(week_no: int, summaries: list[AwdDailySummary]) -> str:
    if not summaries:
        return f"{week_no}주차 데이터가 없습니다."

    counter = Counter(summary.daily_status for summary in summaries)
    dominant_status = counter.most_common(1)[0][0]

    avg_values = [float(summary.avg_inner_level) for summary in summaries if summary.avg_inner_level is not None]
    avg_level = round(sum(avg_values) / len(avg_values), 2) if avg_values else None

    status_desc_map = {
        "OVERFLOODED": "과다 담수 상태가 주로 관측되었다.",
        "FLOODED": "담수 상태가 주로 유지되었다.",
        "DRYING": "건조 전환 상태가 주로 관측되었다.",
        "DRY": "건조 상태가 주로 관측되었으며 재관개 필요 구간이 포함되었을 가능성이 있다.",
    }

    avg_text = f"주간 평균 내부 수위는 {avg_level}cm였다. " if avg_level is not None else ""
    desc_text = status_desc_map.get(dominant_status, "수위 변화가 관측되었다.")

    return f"{week_no}주차에는 {avg_text}{desc_text}"


def extract_representative_images(summaries: list[AwdDailySummary], max_images: int = 3) -> list[str]:
    images = []
    seen = set()

    for summary in summaries:
        url = summary.verification_image_url
        if url and url not in seen:
            seen.add(url)
            images.append(url)
        if len(images) >= max_images:
            break

    return images


def draw_wrapped_text(pdf, text: str, x: int, y: int, max_width: int, font_name: str, font_size: int = 11, line_height: int = 18):
    words = text.split()
    line = ""

    for word in words:
        test_line = f"{line} {word}".strip()
        if pdf.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            pdf.drawString(x, y, line)
            y -= line_height
            line = word

    if line:
        pdf.drawString(x, y, line)
        y -= line_height

    return y

@router.post("")
def create_mrv_report(payload: MrvReportCreate, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    # 중복 체크
    existing_report = (
        db.query(MrvReport)
        .filter(
            MrvReport.field_id == payload.field_id,
            MrvReport.report_month == payload.report_month
        )
        .first()
    )
    if existing_report:
        raise HTTPException(status_code=400, detail="해당 월의 MRV 보고서가 이미 존재합니다.")

    # 해당 월 범위 계산
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
        raise HTTPException(status_code=404, detail="해당 월의 일일 요약 데이터가 없습니다.")

    # AWD cycle 계산 (DRY 상태 개수 기준)
    total_awd_cycles = sum(
        1 for summary in summaries
        if summary.daily_status == "DRY"
    )

    # 수정된 부분 (OVERFLOODED 포함)
    flood_days = sum(
        1 for summary in summaries
        if summary.daily_status in ("FLOODED", "OVERFLOODED")
    )

    # 탄소 감축량 계산
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
        validation_note=payload.validation_note,
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

    start_date, end_date = get_month_range(report.report_month)

    summaries = (
        db.query(AwdDailySummary)
        .join(IotNode, IotNode.id == AwdDailySummary.node_id)
        .filter(
            IotNode.field_id == report.field_id,
            AwdDailySummary.record_date >= start_date,
            AwdDailySummary.record_date < end_date
        )
        .order_by(AwdDailySummary.record_date.asc(), AwdDailySummary.id.asc())
        .all()
    )

    nodes = (
        db.query(IotNode)
        .filter(IotNode.field_id == report.field_id)
        .order_by(IotNode.id.asc())
        .all()
    )

    status_counts = summarize_status_counts(summaries)
    weekly_groups = group_summaries_by_week(summaries)
    representative_images = extract_representative_images(summaries, max_images=3)
    
    font_name = register_korean_font()
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left_x = 50
    right_x = width - 50
    max_text_width = int(right_x - left_x)
    y = height - 50

    def ensure_space(current_y: int, needed: int = 80):
        nonlocal pdf
        if current_y < needed:
            pdf.showPage()
            pdf.setFont(font_name, 11)
            return height - 50
        return current_y

    pdf.setTitle(f"mrv_report_{report.id}")

    # 1. 제목
    pdf.setFont(font_name, 16)
    pdf.drawString(left_x, y, "AWD Water Management MRV Report")
    y -= 30

    pdf.setFont(font_name, 11)
    y = draw_wrapped_text(
        pdf,
        f"본 보고서는 {field.field_name}의 {report.report_month} 기간 AWD 물관리 수행 이력을 정리한 MRV 보고서이다. "
        f"본 시스템은 IoT 센서를 통해 수위 데이터를 자동 수집하고, 이를 기반으로 논 상태 변화를 기록·관리하도록 설계되었다.",
        left_x, y, max_text_width, font_name=font_name
    )

    y -= 10

    # 2. 보고서 개요
    y = ensure_space(y)
    pdf.setFont(font_name, 13)
    pdf.drawString(left_x, y, "1. 보고서 개요")
    y -= 24

    pdf.setFont(font_name, 11)
    overview_lines = [
        f"대상 논: {field.field_name}",
        f"보고 기간: {report.report_month}",
        f"생성일: {report.created_at}",
        f"노드 수: {len(nodes)}",
        f"보고서 상태: {report.status}",
    ]
    for line in overview_lines:
        pdf.drawString(left_x, y, line)
        y -= 18

    y -= 10

    # 3. 월간 운영 요약
    y = ensure_space(y)
    pdf.setFont(font_name, 13)
    pdf.drawString(left_x, y, "2. 월간 운영 요약")
    y -= 24

    pdf.setFont(font_name, 11)
    summary_lines = [
        f"AWD 수행 횟수: {report.total_awd_cycles}회",
        f"담수 유지 일수: {report.flood_days}일",
        f"탄소감축 추정량: {report.carbon_reduction} kgCO2-eq",
        f"상태 분포 - OVERFLOODED: {status_counts['OVERFLOODED']}일, "
        f"FLOODED: {status_counts['FLOODED']}일, "
        f"DRYING: {status_counts['DRYING']}일, "
        f"DRY: {status_counts['DRY']}일",
    ]
    for line in summary_lines:
        y = draw_wrapped_text(pdf, line, left_x, y, max_text_width, font_name=font_name)
    y -= 4

    y = draw_wrapped_text(
        pdf,
        f"보고 기간 동안 AWD 수행 횟수는 {report.total_awd_cycles}회로 집계되었으며, "
        f"담수 상태는 {report.flood_days}일 유지되었다. 수위 데이터는 일일 요약 기준으로 분석되었고, "
        f"논 상태는 OVERFLOODED, FLOODED, DRYING, DRY의 4단계로 구분하였다.",
        left_x, y, max_text_width, font_name=font_name
    )
    y -= 10

    # 4. 주차별 수위 변화 요약
    y = ensure_space(y)
    pdf.setFont(font_name, 13)
    pdf.drawString(left_x, y, "3. 주차별 수위 변화 요약")
    y -= 24

    pdf.setFont(font_name, 11)
    if weekly_groups:
        for week_no, week_summaries in weekly_groups:
            y = ensure_space(y)
            week_text = make_weekly_summary_text(week_no, week_summaries)
            y = draw_wrapped_text(pdf, f"- {week_text}", left_x, y, max_text_width, font_name=font_name)
            y -= 4
    else:
        pdf.drawString(left_x, y, "주차별 요약 데이터가 없습니다.")
        y -= 20

    y -= 10

    # 5. 검증 결과
    y = ensure_space(y)
    pdf.setFont(font_name, 13)
    pdf.drawString(left_x, y, "4. 현장 검증 결과")
    y -= 24

    pdf.setFont(font_name, 11)
    validation_lines = [
        f"검증 방법: {validation['validation_method']}",
        f"샘플 수: {validation['validation_sample_count']}",
        f"일치 수: {validation['validation_match_count']}",
        f"정확도: {validation['validation_accuracy']}%",
        f"비고: {validation['validation_note']}",
    ]
    for line in validation_lines:
        y = draw_wrapped_text(pdf, line, left_x, y, max_text_width, font_name=font_name)

    y -= 4
    y = draw_wrapped_text(
        pdf,
        f"검증은 현장 촬영 사진과 센서 기반 상태 판정 결과를 비교하는 방식으로 수행하였다. "
        f"총 {validation['validation_sample_count']}건 중 {validation['validation_match_count']}건이 일치하여 "
        f"정확도는 {validation['validation_accuracy']}%로 나타났다.",
        left_x, y, max_text_width, font_name=font_name
    )
    y -= 10

    # 6. 대표 사진 URL
    y = ensure_space(y)
    pdf.setFont(font_name, 13)
    pdf.drawString(left_x, y, "5. 대표 검증 이미지")
    y -= 24

    pdf.setFont(font_name, 11)
    if representative_images:
        y = draw_wrapped_text(
            pdf,
            "아래 URL은 해당 월의 일일 요약 데이터에 연결된 대표 검증 이미지이다.",
            left_x, y, max_text_width, font_name=font_name
        )
        y -= 4

        for idx, img_url in enumerate(representative_images, start=1):
            y = ensure_space(y)
            y = draw_wrapped_text(pdf, f"[이미지 {idx}] {img_url}", left_x, y, max_text_width, font_name=font_name)
            y -= 4
    else:
        pdf.drawString(left_x, y, "연결된 검증 이미지가 없습니다.")
        y -= 20

    y -= 10

    # 7. 탄소감축 추정 결과
    y = ensure_space(y)
    pdf.setFont(font_name, 13)
    pdf.drawString(left_x, y, "6. 탄소감축 추정 결과")
    y -= 24

    pdf.setFont(font_name, 11)
    y = draw_wrapped_text(
        pdf,
        f"AWD 수행 횟수를 기반으로 산출한 탄소감축 추정치는 {report.carbon_reduction} kgCO2-eq이다. "
        f"본 수치는 현장에서 직접 측정된 값이 아니라, AWD 수행 이력과 기존 계수식을 기반으로 계산된 추정치이다.",
        left_x, y, max_text_width, font_name=font_name
    )
    y -= 10

    # 8. 결론
    y = ensure_space(y)
    pdf.setFont(font_name, 13)
    pdf.drawString(left_x, y, "7. 결론")
    y -= 24

    pdf.setFont(font_name, 11)
    y = draw_wrapped_text(
        pdf,
        f"본 시스템은 AWD 농법 수행 과정에서 발생하는 수위 데이터를 자동으로 수집·기록하고, "
        f"이를 일일 요약 및 월별 MRV 보고서 형태로 정리할 수 있음을 확인하였다. "
        f"또한 현장 사진 기반 검증을 통해 센서 데이터의 신뢰성을 보완할 수 있었으며, "
        f"AWD 물관리의 디지털 기록 및 MRV 자동화 가능성을 확인하였다.",
        left_x, y, max_text_width, font_name=font_name
    )

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

    start_date, end_date = get_month_range(report.report_month)

    summaries = (
        db.query(AwdDailySummary)
        .join(IotNode, IotNode.id == AwdDailySummary.node_id)
        .filter(
            IotNode.field_id == report.field_id,
            AwdDailySummary.record_date >= start_date,
            AwdDailySummary.record_date < end_date
        )
        .order_by(AwdDailySummary.record_date.asc(), AwdDailySummary.id.asc())
        .all()
    )

    status_counts = summarize_status_counts(summaries)
    representative_images = extract_representative_images(summaries, max_images=3)

    workbook = Workbook()

    # 1. 요약 시트
    summary_sheet = workbook.active
    summary_sheet.title = "MRV Summary"
    summary_sheet.append([
        "field_name",
        "report_month",
        "total_awd_cycles",
        "flood_days",
        "overflooded_days",
        "flooded_days",
        "drying_days",
        "dry_days",
        "carbon_reduction_kgco2eq",
        "status",
        "created_at"
    ])
    summary_sheet.append([
        field.field_name,
        report.report_month,
        report.total_awd_cycles,
        report.flood_days,
        status_counts["OVERFLOODED"],
        status_counts["FLOODED"],
        status_counts["DRYING"],
        status_counts["DRY"],
        float(report.carbon_reduction) if report.carbon_reduction is not None else None,
        report.status,
        str(report.created_at)
    ])

    # 2. 검증 시트
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

    # 3. 대표 이미지 시트
    image_sheet = workbook.create_sheet(title="Validation Images")
    image_sheet.append(["image_no", "image_url"])

    if representative_images:
        for idx, img_url in enumerate(representative_images, start=1):
            image_sheet.append([idx, img_url])
    else:
        image_sheet.append([1, "이미지 없음"])

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    filename = f"mrv_report_{report.id}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
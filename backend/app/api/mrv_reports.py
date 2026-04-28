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
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import requests

from app.api.deps import get_db
from app.models.awd_daily_summary import AwdDailySummary
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.mrv_report import MrvReport
from app.models.validation_record import ValidationRecord

from app.schemas.mrv_report import (
    MrvReportCreate,
    MrvReportStatusUpdate,
)
from app.utils.response import success_response
from collections import Counter, defaultdict
from math import ceil
from reportlab.pdfbase.cidfonts import UnicodeCIDFont


router = APIRouter(prefix="/mrv-reports", tags=["MRV Reports"])

ALLOWED_MRV_STATUSES = {"IN_PROGRESS", "COMPLETED"}

def register_korean_font():
    """
    PDF용 한글 폰트를 등록합니다.
    - 로컬 Windows: 맑은 고딕 우선
    - 배포 서버: backend/fonts 폴더의 폰트 우선
    - fallback: ReportLab 내장 CID 폰트
    """
    font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "fonts"))
    candidate_paths = [
        r"C:\Windows\Fonts\malgun.ttf",
        os.path.join(font_dir, "malgun.ttf"),
        os.path.join(font_dir, "Malgun.ttf"),
        os.path.join(font_dir, "NanumMyeongjo.ttf"),
        os.path.join(font_dir, "NanumGothic.ttf"),
    ]

    for path in candidate_paths:
        normalized = os.path.abspath(path)
        if os.path.exists(normalized):
            pdfmetrics.registerFont(TTFont("KoreanFont", normalized))
            return "KoreanFont"

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        return "HYSMyeongJo-Medium"
    except Exception:
        raise RuntimeError(
            "사용 가능한 한글 폰트를 찾지 못했습니다. "
            "backend/fonts 폴더에 malgun.ttf, NanumMyeongjo.ttf 또는 NanumGothic.ttf를 추가하세요."
        )
    

def get_month_range(report_month: str) -> tuple[date, date]:
    year, month = map(int, report_month.split("-"))

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return start_date, end_date

def select_representative_images(rows):
    if not rows:
        return []

    # 날짜 기준 정렬
    rows = sorted(rows, key=lambda x: x.record_date)

    n = len(rows)

    indices = [
        0,
        n // 2,
        n - 1
    ]

    images = []
    for i in indices:
        if rows[i].image_url:
            images.append(rows[i].image_url)

    return list(dict.fromkeys(images))  # 중복 제거


def select_representative_validation_records(rows):
    """월 초/중/후를 대표하는 validation record를 최대 3개 선택합니다."""
    if not rows:
        return []

    rows = sorted(rows, key=lambda x: (x.record_date, x.id))
    n = len(rows)
    selected_indexes = [0, n // 2, n - 1]

    selected = []
    seen_urls = set()
    for idx in selected_indexes:
        row = rows[idx]
        if row.image_url and row.image_url not in seen_urls:
            selected.append(row)
            seen_urls.add(row.image_url)

    return selected


def format_report_month(report_month: str) -> str:
    year, month = map(int, report_month.split("-"))
    return f"{year}년 {month}월"

def get_validation_summary(field_id: int, start_date: date, end_date: date, db: Session) -> dict:
    rows = (
        db.query(ValidationRecord)
        .filter(
            ValidationRecord.field_id == field_id,
            ValidationRecord.record_date >= start_date,
            ValidationRecord.record_date < end_date
        )
        .order_by(ValidationRecord.record_date.asc(), ValidationRecord.id.asc())
        .all()
    )

    sample_count = len(rows)
    match_count = sum(1 for row in rows if row.is_match is True)
    accuracy = round((match_count / sample_count) * 100, 2) if sample_count > 0 else 0

    notes = [row.note for row in rows if row.note]
    note = notes[-1] if notes else "별도 비고 없음"

    images = []
    seen = set()
    for row in rows:
        if row.image_url and row.image_url not in seen:
            seen.add(row.image_url)
            images.append(row.image_url)

    return {
        "validation_method": "현장 사진 비교" if sample_count > 0 else "검증 데이터 없음",
        "validation_sample_count": sample_count,
        "validation_match_count": match_count,
        "validation_accuracy": accuracy,
        "validation_note": note,
        "representative_images": select_representative_images(rows),
    }

def summarize_status_counts(summaries: list[AwdDailySummary]) -> dict:
    counter = Counter(summary.daily_status for summary in summaries)
    return {
        "OVERFLOODED": counter.get("OVERFLOODED", 0),
        "FLOODED": counter.get("FLOODED", 0),
        "DRYING": counter.get("DRYING", 0),
        "DRY": counter.get("DRY", 0),
    }

def aggregate_daily_summaries(summaries: list[AwdDailySummary]) -> list[AwdDailySummary]:
    """
    node별 daily_summary → 날짜별 대표 daily_summary로 변환
    """

    grouped = defaultdict(list)

    for s in summaries:
        grouped[s.record_date].append(s)

    aggregated = []

    for record_date, items in grouped.items():
        avg_values = [
            float(i.avg_inner_level)
            for i in items
            if i.avg_inner_level is not None
        ]

        if not avg_values:
            continue

        avg_level = sum(avg_values) / len(avg_values)

        # 평균 기준으로 상태 재판정
        if avg_level >= 5:
            status = "OVERFLOODED"
        elif avg_level >= 0:
            status = "FLOODED"
        elif avg_level > -15:
            status = "DRYING"
        else:
            status = "DRY"

        aggregated.append(
            AwdDailySummary(
                record_date=record_date,
                avg_inner_level=avg_level,
                daily_status=status
            )
        )

    return sorted(aggregated, key=lambda x: x.record_date)
    
def group_summaries_by_week(summaries: list[AwdDailySummary]) -> list[tuple[int, list[AwdDailySummary]]]:
    summaries = sorted(summaries, key=lambda x: x.record_date)
    grouped: dict[int, list[AwdDailySummary]] = defaultdict(list)

    for summary in summaries:
        week_no = ceil(summary.record_date.day / 7)
        grouped[week_no].append(summary)

    return sorted(grouped.items(), key=lambda x: x[0])

def get_status_flow(summaries: list[AwdDailySummary]) -> str:
    statuses = [s.daily_status for s in summaries if s.daily_status]
    return " → ".join(statuses) if statuses else "데이터 없음"

def count_awd_cycles(summaries: list[AwdDailySummary]) -> int:
    ordered = sorted(summaries, key=lambda x: x.record_date)
    statuses = [s.daily_status for s in ordered if s.daily_status]

    count = 0
    for prev_status, current_status in zip(statuses, statuses[1:]):
        if prev_status == "DRY" and current_status == "FLOODED":
            count += 1

    return count

def make_weekly_summary_text(week_no: int, summaries: list[AwdDailySummary]) -> list[str]:
    if not summaries:
        return [
            f"■ {week_no}주차",
            "",
            "해당 주차에는 수집된 데이터가 없어 수위 변화 분석이 제한됩니다."
        ]

    ordered = sorted(summaries, key=lambda x: x.record_date)

    statuses = [s.daily_status for s in ordered if s.daily_status]
    avg_values = [
        float(s.avg_inner_level)
        for s in ordered
        if s.avg_inner_level is not None
    ]

    if not statuses or not avg_values:
        return [
            f"■ {week_no}주차",
            "",
            "해당 주차에는 상태 또는 평균 수위 데이터가 부족하여 수위 변화 분석이 제한됩니다."
        ]

    start_avg = avg_values[0]
    min_avg = min(avg_values)
    max_avg = max(avg_values)
    end_avg = avg_values[-1]
    status_flow = get_status_flow(ordered)

    start_status = statuses[0]
    end_status = statuses[-1]
    dominant_status = Counter(statuses).most_common(1)[0][0]

    lines = [
        f"■ {week_no}주차",
        "",
        f"시작 평균 수위: {start_avg:.2f}cm",
        f"최저 평균 수위: {min_avg:.2f}cm",
        f"최고 평균 수위: {max_avg:.2f}cm",
        f"마지막 평균 수위: {end_avg:.2f}cm",
        f"상태 변화: {status_flow}",
        "",
    ]

    # 1. 수위 변화 방향 설명
    if end_avg > start_avg:
        lines.append(
            f"{week_no}주차에는 평균 내부 수위가 {start_avg:.2f}cm에서 {end_avg:.2f}cm로 상승하는 흐름을 보였습니다."
        )
    elif end_avg < start_avg:
        lines.append(
            f"{week_no}주차에는 평균 내부 수위가 {start_avg:.2f}cm에서 {end_avg:.2f}cm로 감소하는 흐름을 보였습니다."
        )
    else:
        lines.append(
            f"{week_no}주차에는 평균 내부 수위가 {start_avg:.2f}cm 수준에서 큰 변화 없이 유지되었습니다."
        )

    # 2. 상태 흐름 해석
    weekly_awd_cycles = 0

    for prev_status, current_status in zip(statuses, statuses[1:]):
        if prev_status == "DRY" and current_status == "FLOODED":
            weekly_awd_cycles += 1

    if weekly_awd_cycles > 0:
        lines.append(
            f"DRY 상태 이후 담수 상태로 전환된 흐름이 {weekly_awd_cycles}회 관측되어 AWD 수행 흐름이 확인됩니다."
        )

    if "DRY" in statuses and "OVERFLOODED" in statuses:
        dry_index = statuses.index("DRY")
        after_dry = statuses[dry_index + 1:]

        if "OVERFLOODED" in after_dry:
            lines.append(
                "DRY 상태 이후 수위가 급격히 상승하여 OVERFLOODED 상태가 관측되었습니다. 이는 재관개 과정에서 과다 담수가 발생했을 가능성을 의미합니다."
            )

    if "OVERFLOODED" in statuses:
        if "FLOODED" in statuses and statuses.index("OVERFLOODED") < statuses.index("FLOODED"):
            lines.append(
                "이후 수위가 조정되어 과다 담수 상태에서 적정 담수 상태로 회복된 흐름이 확인됩니다."
            )
        else:
            lines.append(
                "일부 구간에서 과다 담수 상태가 관측되어 수위 조정이 필요한 상태로 판단됩니다."
            )

    if "DRYING" in statuses and "DRY" not in statuses:
        lines.append(
            "DRYING 상태가 관측되었으나 DRY 상태에는 도달하지 않아, 완전 건조 전 단계로 해석됩니다."
        )

    if statuses.count(dominant_status) == len(statuses):
        lines.append(
            f"해당 주차는 전반적으로 {dominant_status} 상태가 지속된 것으로 나타납니다."
        )
    else:
        lines.append(
            f"해당 주차는 {start_status} 상태에서 시작하여 {end_status} 상태로 마무리되었습니다."
        )

    return lines


def get_month_avg_inner_level(summaries: list[AwdDailySummary]) -> float | None:
    values = [
        float(summary.avg_inner_level)
        for summary in summaries
        if summary.avg_inner_level is not None
    ]

    if not values:
        return None

    return round(sum(values) / len(values), 2)


def get_dominant_status(status_counts: dict) -> str:
    if not status_counts:
        return "데이터 없음"

    return max(status_counts.items(), key=lambda x: x[1])[0]


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

    daily_summaries = aggregate_daily_summaries(summaries)

    total_awd_cycles = count_awd_cycles(daily_summaries)

    flood_days = sum(
        1 for s in daily_summaries
        if s.daily_status in ("FLOODED", "OVERFLOODED")
    )

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
        start_date, end_date = get_month_range(report.report_month)
        validation = get_validation_summary(report.field_id, start_date, end_date, db)

        reports.append({
            "id": report.id,
            "field_id": report.field_id,
            "field_name": field_name,
            "report_month": report.report_month,
            "total_awd_cycles": report.total_awd_cycles,
            "flood_days": report.flood_days,
            "status": report.status,
            "carbon_reduction": report.carbon_reduction,
            "validation_method": validation["validation_method"],
            "validation_sample_count": validation["validation_sample_count"],
            "validation_match_count": validation["validation_match_count"],
            "validation_accuracy": validation["validation_accuracy"],
            "validation_note": validation["validation_note"],
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

    start_date, end_date = get_month_range(report.report_month)
    report_month_text = format_report_month(report.report_month)

    validation = get_validation_summary(report.field_id, start_date, end_date, db)
    validation_rows = (
        db.query(ValidationRecord)
        .filter(
            ValidationRecord.field_id == report.field_id,
            ValidationRecord.record_date >= start_date,
            ValidationRecord.record_date < end_date
        )
        .order_by(ValidationRecord.record_date.asc(), ValidationRecord.id.asc())
        .all()
    )
    representative_records = select_representative_validation_records(validation_rows)

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

    daily_summaries = aggregate_daily_summaries(summaries)
    status_counts = summarize_status_counts(daily_summaries)
    weekly_groups = group_summaries_by_week(daily_summaries)
    weekly_dict = {week_no: week_summaries for week_no, week_summaries in weekly_groups}
    month_avg = get_month_avg_inner_level(daily_summaries)
    dominant_status = get_dominant_status(status_counts)

    font_name = register_korean_font()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # HWP 기준 스타일
    COVER_TITLE = 20
    COVER_SUBTITLE = 15
    COVER_BODY = 10
    TOC_TITLE = 15
    TOC_BODY = 11
    SECTION_TITLE = 12
    SUB_TITLE = 11
    BODY = 10

    left_x = 55
    right_x = width - 55
    top_y = height - 60
    bottom_y = 60
    max_text_width = int(right_x - left_x)

    def new_page():
        pdf.showPage()
        pdf.setFont(font_name, BODY)
        return top_y

    def ensure_space(y, needed=80):
        if y < bottom_y + needed:
            return new_page()
        return y

    def draw_text(text: str, x: int, y: int, font_size: int = BODY, line_height: int = 15, max_width: int | None = None):
        max_width = max_width or max_text_width
        pdf.setFont(font_name, font_size)
        return draw_wrapped_text(
            pdf,
            text,
            x,
            y,
            max_width,
            font_name=font_name,
            font_size=font_size,
            line_height=line_height
        )

    def draw_section_title(title: str, y: int):
        y = ensure_space(y, 50)
        pdf.setFont(font_name, SECTION_TITLE)
        pdf.drawString(left_x, y, title)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(0.6)
        pdf.line(left_x, y - 5, right_x, y - 5)
        return y - 24

    def draw_sub_title(title: str, y: int):
        y = ensure_space(y, 40)
        pdf.setFont(font_name, SUB_TITLE)
        pdf.drawString(left_x, y, title)
        return y - 18

    def draw_lines(lines: list[str], y: int, font_size: int = BODY, line_height: int = 15):
        pdf.setFont(font_name, font_size)
        for line in lines:
            y = ensure_space(y, 40)
            if line == "":
                y -= 8
            else:
                y = draw_text(line, left_x, y, font_size=font_size, line_height=line_height)
        return y

    def draw_simple_table(headers: list[str], rows: list[list[str]], x: int, y: int, col_widths: list[int]):
        row_height = 22
        table_width = sum(col_widths)
        total_height = row_height * (len(rows) + 1)
        y = ensure_space(y, total_height + 25)

        # header background
        pdf.setFillColor(colors.HexColor("#E9EEF5"))
        pdf.rect(x, y - row_height + 5, table_width, row_height, fill=1, stroke=0)

        pdf.setFillColor(colors.black)
        pdf.setStrokeColor(colors.HexColor("#666666"))
        pdf.setLineWidth(0.5)

        current_x = x
        pdf.setFont(font_name, BODY)
        for idx, header in enumerate(headers):
            pdf.drawString(current_x + 6, y - 10, str(header))
            current_x += col_widths[idx]

        # grid header line
        pdf.line(x, y + 5, x + table_width, y + 5)
        pdf.line(x, y - row_height + 5, x + table_width, y - row_height + 5)

        y -= row_height

        for row in rows:
            current_x = x
            pdf.setFillColor(colors.black)
            for idx, value in enumerate(row):
                pdf.drawString(current_x + 6, y - 10, str(value))
                current_x += col_widths[idx]
            pdf.setStrokeColor(colors.HexColor("#B0B0B0"))
            pdf.line(x, y - row_height + 5, x + table_width, y - row_height + 5)
            y -= row_height

        # vertical lines
        top_line = y + row_height * (len(rows) + 1) + 5
        bottom_line = y + 5
        current_x = x
        pdf.setStrokeColor(colors.HexColor("#B0B0B0"))
        pdf.line(current_x, top_line, current_x, bottom_line)
        for w in col_widths:
            current_x += w
            pdf.line(current_x, top_line, current_x, bottom_line)

        return y - 12

    def draw_box_title(title: str, y: int):
        y = ensure_space(y, 45)
        pdf.setFillColor(colors.HexColor("#F2F4F7"))
        pdf.rect(left_x, y - 18, max_text_width, 22, fill=1, stroke=0)
        pdf.setFillColor(colors.black)
        pdf.setFont(font_name, SUB_TITLE)
        pdf.drawString(left_x + 8, y - 11, title)
        return y - 30

    def image_reader_from_url_or_path(image_url: str):
        try:
            if image_url.startswith("http://") or image_url.startswith("https://"):
                response = requests.get(image_url, timeout=5)
                response.raise_for_status()
                return ImageReader(BytesIO(response.content))
            if os.path.exists(image_url):
                return ImageReader(image_url)
        except Exception:
            return None
        return None

    def validation_record_description(row):
        sensor = row.sensor_predicted_status or "센서 상태 미입력"
        observed = row.observed_surface_status or "관찰 상태 미입력"

        if row.is_match is True:
            result = "센서 기반 상태와 사진 기반 관찰 결과가 일치하였다."
        elif row.is_match is False:
            result = "센서 기반 상태와 사진 기반 관찰 결과가 일치하지 않았다."
        else:
            result = "관찰 결과가 UNKNOWN이거나 입력값이 부족하여 일치 여부를 판별하기 어렵다."

        return f"촬영일: {row.record_date} / 센서 상태: {sensor} / 관찰 상태: {observed}. {result}"

    pdf.setTitle(f"mrv_report_{report.id}")

    # 표지
    y = height - 210
    pdf.setFont(font_name, COVER_TITLE)
    pdf.drawCentredString(width / 2, y, "AWD Water Management MRV Report")
    y -= 20
    pdf.setLineWidth(0.8)
    pdf.line(90, y, width - 90, y)

    y -= 70
    pdf.setFont(font_name, COVER_SUBTITLE)
    pdf.drawCentredString(width / 2, y, f"{field.field_name}")
    y -= 28
    pdf.drawCentredString(width / 2, y, f"{report_month_text} MRV 보고서")

    y -= 70
    pdf.setFont(font_name, COVER_BODY)
    pdf.drawCentredString(width / 2, y, f"작성일: {report.created_at.date() if report.created_at else '-'}")
    y -= 20
    pdf.drawCentredString(width / 2, y, "팀명: 강안장인")

    # 목차
    y = new_page()
    pdf.setFont(font_name, TOC_TITLE)
    pdf.drawString(left_x, y, "목차")
    y -= 35

    toc_items = [
        "1. 개요 (배경)",
        "2. 분석 대상 및 기간",
        "3. 결과 요약",
        "4. 결과 분석",
        "   4.1 주차별 수위 변화 분석",
        "   4.2 월간 수위 상태 분석",
        "5. AWD 수행 및 탄소 감축 분석",
        "6. 검증 결과",
        "   6.1 현장 검증 결과",
        "   6.2 대표 검증 이미지 출력",
        "7. 향후 계획",
        "8. 결론",
    ]
    pdf.setFont(font_name, TOC_BODY)
    for item in toc_items:
        pdf.drawString(left_x, y, item)
        y -= 20

    # Page 1: 1~3
    y = new_page()
    y = draw_section_title("1. 개요 (배경)", y)
    y = draw_lines([
        f"본 보고서는 {field.field_name} 논을 대상으로 {report_month_text} 동안 수행된 AWD(Alternate Wetting and Drying) 물관리 이력을 분석한 MRV 보고서이다.",
        "본 시스템은 IoT 센서를 활용하여 논의 수위 데이터를 자동으로 수집하고, 이를 기반으로 일 단위 상태를 분석하여 물관리 수행 여부를 기록하도록 설계되었다.",
        "수위 상태는 내부 수위를 기준으로 다음과 같이 구분된다.",
        "⦁ OVERFLOODED: 과다 담수 상태",
        "⦁ FLOODED: 적정 담수 상태",
        "⦁ DRYING: 건조 진행 상태",
        "⦁ DRY: 재관개 필요 상태",
        "각 날짜별 상태는 하루 동안 수집된 센서 데이터의 평균 수위를 기준으로 대표 상태로 정의된다.",
    ], y)

    y -= 8
    y = draw_section_title("2. 분석 대상 및 기간", y)
    y = draw_simple_table(
        ["항목", "내용"],
        [
            ["대상 논", field.field_name],
            ["분석 기간", report_month_text],
            ["사용 노드 수", f"{len(nodes)}개"],
            ["보고서 생성일", str(report.created_at.date() if report.created_at else "-")],
        ],
        left_x,
        y,
        [140, 300]
    )

    y = draw_section_title("3. 결과 요약", y)
    y = draw_lines(["분석 기간 동안의 일일 상태를 집계한 결과는 다음과 같다."], y)
    y = draw_simple_table(
        ["상태", "일수"],
        [
            ["OVERFLOODED", f"{status_counts['OVERFLOODED']}일"],
            ["FLOODED", f"{status_counts['FLOODED']}일"],
            ["DRYING", f"{status_counts['DRYING']}일"],
            ["DRY", f"{status_counts['DRY']}일"],
        ],
        left_x,
        y,
        [180, 120]
    )
    y = draw_lines([
        f"전체적으로 {dominant_status} 상태가 가장 많이 관측되었으며, 논의 수위는 해당 상태를 중심으로 변화하였다.",
        f"AWD 수행 기준은 DRY 상태 이후 FLOODED 상태로 전환되는 경우를 1회로 정의하며, 해당 기간 동안 AWD 수행 횟수는 {report.total_awd_cycles}회로 나타났다.",
    ], y)

    # Page 2: 4
    y = new_page()
    y = draw_section_title("4. 결과 분석", y)
    y = draw_sub_title("4.1 주차별 수위 변화 분석", y)

    for week_no in range(1, 5):
        week_lines = make_weekly_summary_text(week_no, weekly_dict.get(week_no, []))
        y = ensure_space(y, 130)
        for line in week_lines:
            if line.startswith("■"):
                pdf.setFont(font_name, SUB_TITLE)
                pdf.drawString(left_x, y, line)
                y -= 18
            elif line == "":
                y -= 5
            else:
                y = draw_text(line, left_x, y, BODY, 14)
        y -= 7

    y = draw_sub_title("4.2 월간 수위 상태 분석", y)
    if month_avg is not None:
        y = draw_lines([
            f"분석 기간 동안 평균 내부 수위는 {month_avg:.2f}cm로 나타났다. 이는 전체적인 수위 변화 흐름을 요약한 값이며, 주요 상태는 {dominant_status}으로 확인된다.",
            "전체적으로 건조 진행 상태가 지속되었으며, 일부 구간에서는 과다 담수 상태가 발생하는 등 수위 변동이 존재하였다.",
            "그러나 건조 이후 재관개가 충분히 이루어지지 않아 AWD 사이클은 발생하지 않았다.",
        ], y)
    else:
        y = draw_lines(["분석 기간 동안 평균 내부 수위 데이터가 없어 월간 수위 상태 분석이 제한된다."], y)

    # Page 3: 5
    y = new_page()
    y = draw_section_title("5. AWD 수행 및 탄소 감축 분석", y)

    y = draw_box_title("[AWD 수행 횟수 기준]", y)
    y = draw_lines([
        "논이 DRY 상태 이후 FLOODED 상태로 전환되는 경우를 1회로 정의한다.",
        f"⦁ {report_month_text} AWD 수행 횟수: {report.total_awd_cycles}회",
    ], y)

    y = draw_box_title("[탄소 감축량 계산]", y)
    y = draw_lines([
        f"이에 따라 {report_month_text} 탄소 감축량은 AWD 수행 횟수를 기준으로 다음과 같이 산출된다.",
        "⦁ 탄소 감축량 = AWD 수행 횟수 × 15.25 (kgCO2-eq)",
        f"⦁ 결과: {report.carbon_reduction} kgCO2-eq",
        "(본 결과는 센서 기반 수위 데이터 분석에 따른 추정값임)",
    ], y)

    y = draw_box_title("[시사점]", y)
    if report.total_awd_cycles == 0:
        insight_lines = [
            "건조 단계 이후 재관개가 이루어지지 않아 AWD 사이클이 형성되지 않았다.",
            "이는 물관리 전략이 건조 단계 중심으로 운영되었음을 의미한다.",
            "향후 AWD 수행을 위해서는 DRY 상태 이후 적절한 시점에서의 계획적 재관개가 필요하다.",
        ]
    else:
        insight_lines = [
            f"분석 기간 동안 AWD 사이클이 {report.total_awd_cycles}회 형성되었다.",
            "이는 건조 이후 재관개 흐름이 일부 확인되었음을 의미한다.",
            "향후에는 재관개 시점과 담수 유지 기간을 안정적으로 관리하여 AWD 수행 효과를 높일 필요가 있다.",
        ]
    y = draw_lines(insight_lines, y)

    # Page 4+: 6
    y = new_page()
    y = draw_section_title("6. 검증 결과", y)
    y = draw_sub_title("6.1 현장 검증 결과", y)

    if validation["validation_sample_count"] > 0:
        mismatch_count = validation["validation_sample_count"] - validation["validation_match_count"]
        y = draw_lines([
            f"분석 기간 동안 수집된 현장 검증 데이터는 총 {validation['validation_sample_count']}건이다.",
            "센서 기반 상태와 실제 관찰 결과를 비교한 결과는 다음과 같다.",
        ], y)
        y = draw_simple_table(
            ["항목", "값"],
            [
                ["검증 방법", validation["validation_method"]],
                ["검증 샘플 수", f"{validation['validation_sample_count']}건"],
                ["일치 수", f"{validation['validation_match_count']}건"],
                ["불일치 수", f"{mismatch_count}건"],
                ["검증 정확도", f"{validation['validation_accuracy']}%"],
                ["비고", validation["validation_note"]],
            ],
            left_x,
            y,
            [150, 300]
        )
        y = draw_lines([
            "검증 결과를 통해 센서 기반 상태 판정 결과와 현장 관찰 결과를 비교할 수 있다.",
            "일부 불일치 사례는 센서 측정 시점과 촬영 시점 간 차이 또는 수위 경계 구간에서의 판단 차이에 의해 발생했을 가능성이 있다.",
        ], y)
    else:
        y = draw_lines([
            "해당 기간 동안 등록된 현장 검증 데이터가 없어 검증 결과 분석이 제한된다.",
            "향후 검증 데이터가 추가될 경우, 센서 기반 상태와 실제 관찰 결과 간의 일치 여부를 통해 정확도 분석이 가능하다.",
        ], y)

    y -= 6
    y = draw_sub_title("6.2 대표 검증 이미지 출력", y)

    if representative_records:
        y = draw_lines([
            "본 보고서에서는 월별 대표 검증 이미지를 통해 논의 상태를 시각적으로 확인한다.",
            "대표 이미지는 분석 기간을 기준으로 초반, 중반, 후반 시점을 대표하는 이미지로 구성하였다.",
        ], y)

        labels = ["월 초", "월 중", "월 후"]
        for idx, row in enumerate(representative_records):
            y = ensure_space(y, 210)
            label = labels[idx] if idx < len(labels) else f"대표 이미지 {idx + 1}"

            pdf.setFont(font_name, SUB_TITLE)
            pdf.drawString(left_x, y, f"[{label}]")
            y -= 18

            image_reader = image_reader_from_url_or_path(row.image_url)
            if image_reader:
                img_w, img_h = 220, 125
                pdf.drawImage(image_reader, left_x, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, mask="auto")
                y -= img_h + 10
            else:
                y = draw_text(f"이미지 URL: {row.image_url}", left_x, y, BODY, 14)

            y = draw_text(validation_record_description(row), left_x, y, BODY, 14)
            y -= 12
    else:
        y = draw_lines([
            "해당 기간에 등록된 대표 검증 이미지가 존재하지 않는다.",
            "향후 검증 이미지가 확보될 경우, 월간 대표 이미지를 통해 상태 검증 근거를 시각적으로 제공할 수 있다.",
        ], y)

    # 7~8은 6번이 몇 페이지에서 끝나든 새 페이지에서 시작
    y = new_page()
    y = draw_section_title("7. 향후 계획", y)
    y = draw_lines([
        "⦁ AWD 사이클 확보를 위한 계획적 재관개 전략 수립",
        "⦁ IoT 센서 기반 자동 관개 시스템 도입 검토",
        "⦁ 현장 검증 데이터(이미지) 수집 및 검증 체계 강화",
        "⦁ MRV 보고서 자동화 및 시각화 기능 개선",
    ], y)

    y -= 10
    y = draw_section_title("8. 결론", y)
    if report.total_awd_cycles == 0:
        y = draw_lines([
            f"본 분석 기간 동안 논은 전반적으로 {dominant_status} 상태를 중심으로 변화하였으며, AWD 수행은 발생하지 않았다.",
            "이는 건조 이후 재관개가 이루어지지 않았기 때문으로 판단된다.",
            "본 시스템을 통해 IoT 기반 수위 데이터 수집, 상태 분석, MRV 보고서 생성까지의 자동화 가능성을 확인할 수 있었다.",
            "향후 물관리 전략 개선 및 검증 데이터 확보를 통해 보다 정교한 MRV 시스템 구축이 가능할 것으로 기대된다.",
        ], y)
    else:
        y = draw_lines([
            f"본 분석 기간 동안 논은 {dominant_status} 상태를 중심으로 변화하였으며, AWD 수행은 {report.total_awd_cycles}회 관측되었다.",
            "이는 센서 기반 수위 데이터가 AWD 물관리 수행 이력을 정량적으로 기록할 수 있음을 보여준다.",
            "향후 검증 데이터 확보와 재관개 전략 고도화를 통해 보다 신뢰성 높은 MRV 시스템 구축이 가능할 것으로 기대된다.",
        ], y)

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

    start_date, end_date = get_month_range(report.report_month)
    validation = get_validation_summary(report.field_id, start_date, end_date, db)

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

    daily_summaries = aggregate_daily_summaries(summaries)
    status_counts = summarize_status_counts(daily_summaries)
    representative_images = validation["representative_images"]

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


@router.delete("")
def delete_mrv_report(
    field_id: int,
    report_month: str,
    db: Session = Depends(get_db)
):
    report = db.query(MrvReport).filter(
        MrvReport.field_id == field_id,
        MrvReport.report_month == report_month
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="보고서 없음")

    db.delete(report)
    db.commit()

    return success_response(None, "MRV 보고서 삭제 성공")
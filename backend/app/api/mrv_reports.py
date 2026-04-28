import os
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.api.deps import get_db
from app.models.awd_daily_summary import AwdDailySummary
from app.models.field import Field
from app.models.iot_node import IotNode
from app.models.mrv_report import MrvReport
from app.models.validation_record import ValidationRecord
from app.schemas.mrv_report import MrvReportCreate, MrvReportStatusUpdate
from app.utils.response import success_response

router = APIRouter(prefix="/mrv-reports", tags=["MRV Reports"])

ALLOWED_MRV_STATUSES = {"IN_PROGRESS", "COMPLETED"}

# PDF 스타일 상수
COVER_TITLE_SIZE = 20
COVER_SUBTITLE_SIZE = 15
COVER_INFO_SIZE = 10
TOC_TITLE_SIZE = 15
TOC_BODY_SIZE = 11
SECTION_TITLE_SIZE = 12
SUB_TITLE_SIZE = 11
BODY_SIZE = 10
BODY_LINE_HEIGHT = 15
PARAGRAPH_GAP = 9
SECTION_GAP = 18
LEFT_X = 45
RIGHT_MARGIN = 45
TOP_Y = 805
BOTTOM_Y = 55


def _font_path(filename: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts", filename))


def register_korean_fonts() -> tuple[str, str]:
    """
    일반 본문 폰트와 Bold 폰트를 함께 등록한다.
    Render 서버에서는 Windows 폰트가 없으므로 app/fonts 폴더의 Nanum 폰트를 우선 사용한다.
    """
    regular_candidates = [
        _font_path("NanumGothic.ttf"),
        _font_path("NanumMyeongjo.ttf"),
        r"C:\Windows\Fonts\malgun.ttf",
    ]
    bold_candidates = [
        _font_path("NanumMyeongjoBold.ttf"),
        _font_path("NanumGothicBold.ttf"),
        r"C:\Windows\Fonts\malgunbd.ttf",
    ]

    regular_font = None
    bold_font = None

    for path in regular_candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("KoreanRegular", path))
            regular_font = "KoreanRegular"
            break

    for path in bold_candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("KoreanBold", path))
            bold_font = "KoreanBold"
            break

    if regular_font and not bold_font:
        bold_font = regular_font

    if regular_font and bold_font:
        return regular_font, bold_font

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        return "HYSMyeongJo-Medium", "HYSMyeongJo-Medium"
    except Exception:
        raise RuntimeError(
            "사용 가능한 한글 폰트를 찾지 못했습니다. "
            "backend/app/fonts 폴더에 NanumGothic.ttf, NanumMyeongjo.ttf, NanumMyeongjoBold.ttf를 추가하세요."
        )


def get_month_range(report_month: str) -> tuple[date, date]:
    year, month = map(int, report_month.split("-"))
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return start_date, end_date


def format_report_month(report_month: str) -> str:
    year, month = map(int, report_month.split("-"))
    return f"{year}년 {month}월"


def select_representative_validation_rows(rows: list[ValidationRecord]) -> list[tuple[str, ValidationRecord]]:
    """월 초/중/후 대표 검증 row를 반환한다."""
    valid_rows = [row for row in rows if row.image_url]
    if not valid_rows:
        return []

    valid_rows = sorted(valid_rows, key=lambda x: (x.record_date, x.id))
    n = len(valid_rows)
    labels = ["월 초", "월 중", "월 후"]
    raw_indices = [0, n // 2, n - 1]

    selected = []
    seen_urls = set()
    for label, idx in zip(labels, raw_indices):
        row = valid_rows[idx]
        if row.image_url not in seen_urls:
            selected.append((label, row))
            seen_urls.add(row.image_url)

    return selected


def get_validation_rows(field_id: int, start_date: date, end_date: date, db: Session) -> list[ValidationRecord]:
    return (
        db.query(ValidationRecord)
        .filter(
            ValidationRecord.field_id == field_id,
            ValidationRecord.record_date >= start_date,
            ValidationRecord.record_date < end_date,
        )
        .order_by(ValidationRecord.record_date.asc(), ValidationRecord.id.asc())
        .all()
    )


def get_validation_summary(field_id: int, start_date: date, end_date: date, db: Session) -> dict:
    rows = get_validation_rows(field_id, start_date, end_date, db)

    sample_count = len(rows)
    match_count = sum(1 for row in rows if row.is_match is True)
    mismatch_count = sum(1 for row in rows if row.is_match is False)
    unknown_count = sum(1 for row in rows if row.is_match is None)
    accuracy = round((match_count / sample_count) * 100, 2) if sample_count > 0 else 0

    notes = [row.note for row in rows if row.note]
    note = notes[-1] if notes else "별도 비고 없음"

    representative_rows = select_representative_validation_rows(rows)

    return {
        "validation_method": "현장 사진 비교" if sample_count > 0 else "검증 데이터 없음",
        "validation_sample_count": sample_count,
        "validation_match_count": match_count,
        "validation_mismatch_count": mismatch_count,
        "validation_unknown_count": unknown_count,
        "validation_accuracy": accuracy,
        "validation_note": note,
        "representative_rows": representative_rows,
        "representative_images": [row.image_url for _, row in representative_rows],
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
    grouped = defaultdict(list)
    for s in summaries:
        grouped[s.record_date].append(s)

    aggregated = []
    for record_date, items in grouped.items():
        avg_values = [float(i.avg_inner_level) for i in items if i.avg_inner_level is not None]
        if not avg_values:
            continue

        avg_level = sum(avg_values) / len(avg_values)
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
                daily_status=status,
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


def get_month_avg_inner_level(summaries: list[AwdDailySummary]) -> float | None:
    values = [float(summary.avg_inner_level) for summary in summaries if summary.avg_inner_level is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def get_dominant_status(status_counts: dict) -> str:
    if not status_counts:
        return "데이터 없음"
    return max(status_counts.items(), key=lambda x: x[1])[0]


def make_weekly_summary_text(week_no: int, summaries: list[AwdDailySummary]) -> list[str]:
    if not summaries:
        return [
            f"■ {week_no}주차",
            "해당 주차에는 수집된 데이터가 없어 수위 변화 분석이 제한됩니다.",
        ]

    ordered = sorted(summaries, key=lambda x: x.record_date)
    statuses = [s.daily_status for s in ordered if s.daily_status]
    avg_values = [float(s.avg_inner_level) for s in ordered if s.avg_inner_level is not None]

    if not statuses or not avg_values:
        return [
            f"■ {week_no}주차",
            "해당 주차에는 상태 또는 평균 수위 데이터가 부족하여 수위 변화 분석이 제한됩니다.",
        ]

    start_avg = avg_values[0]
    end_avg = avg_values[-1]
    min_avg = min(avg_values)
    max_avg = max(avg_values)
    start_status = statuses[0]
    end_status = statuses[-1]

    lines = [
        f"■ {week_no}주차",
        f"시작 평균 수위: {start_avg:.2f}cm / 최저: {min_avg:.2f}cm / 최고: {max_avg:.2f}cm / 마지막: {end_avg:.2f}cm",
        f"상태 변화: {get_status_flow(ordered)}",
    ]

    if end_avg > start_avg:
        lines.append(f"{week_no}주차에는 평균 내부 수위가 {start_avg:.2f}cm에서 {end_avg:.2f}cm로 상승하였다.")
    elif end_avg < start_avg:
        lines.append(f"{week_no}주차에는 평균 내부 수위가 {start_avg:.2f}cm에서 {end_avg:.2f}cm로 감소하였다.")
    else:
        lines.append(f"{week_no}주차에는 평균 내부 수위가 {start_avg:.2f}cm 수준에서 큰 변화 없이 유지되었다.")

    if "OVERFLOODED" in statuses:
        lines.append("일부 구간에서 OVERFLOODED 상태가 발생하여 과다 담수 상태가 확인되었다.")
    elif "DRY" in statuses:
        lines.append("DRY 상태가 관측되어 완전 건조 상태에 도달한 구간이 확인되었다.")
    elif "DRYING" in statuses:
        lines.append("DRYING 상태가 관측되었으며, 건조 진행 단계로 해석된다.")

    lines.append(f"해당 주차는 {start_status} 상태에서 시작하여 {end_status} 상태로 마무리되었다.")
    return lines


# ---------------------------
# PDF 그리기 유틸
# ---------------------------

def draw_page_frame(pdf, width, height):
    pdf.setStrokeColor(colors.lightgrey)
    pdf.setLineWidth(0.3)
    # HWP 느낌의 모서리 표시
    pdf.line(35, height - 35, 55, height - 35)
    pdf.line(35, height - 35, 35, height - 55)
    pdf.line(width - 35, height - 35, width - 55, height - 35)
    pdf.line(width - 35, height - 35, width - 35, height - 55)


def wrap_text(pdf, text: str, max_width: int, font_name: str, font_size: int) -> list[str]:
    if text is None:
        return []
    paragraphs = str(text).split("\n")
    wrapped = []
    for paragraph in paragraphs:
        if paragraph == "":
            wrapped.append("")
            continue
        words = paragraph.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if pdf.stringWidth(test_line, font_name, font_size) <= max_width:
                line = test_line
            else:
                if line:
                    wrapped.append(line)
                line = word
        if line:
            wrapped.append(line)
    return wrapped


def draw_text(pdf, text: str, x: int, y: int, max_width: int, font_name: str, font_size: int = BODY_SIZE,
              line_height: int = BODY_LINE_HEIGHT, paragraph_gap: int = 0) -> int:
    pdf.setFont(font_name, font_size)
    lines = wrap_text(pdf, text, max_width, font_name, font_size)
    for line in lines:
        if line == "":
            y -= paragraph_gap or line_height
        else:
            pdf.drawString(x, y, line)
            y -= line_height
    return y


def draw_bullets(pdf, lines: list[str], x: int, y: int, max_width: int, font_name: str, font_size: int = BODY_SIZE) -> int:
    pdf.setFont(font_name, font_size)
    for line in lines:
        y = draw_text(pdf, f"• {line}", x, y, max_width, font_name, font_size, BODY_LINE_HEIGHT)
    return y


def draw_section_title(pdf, title: str, y: int, regular_font: str, bold_font: str) -> int:
    pdf.setFont(bold_font, SECTION_TITLE_SIZE)
    pdf.setFillColor(colors.black)
    pdf.drawString(LEFT_X, y, title)
    y -= 24
    return y


def draw_sub_title(pdf, title: str, y: int, bold_font: str) -> int:
    pdf.setFont(bold_font, SUB_TITLE_SIZE)
    pdf.drawString(LEFT_X, y, title)
    y -= 20
    return y


def draw_divider(pdf, y: int, width: int) -> int:
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(0.8)
    pdf.line(LEFT_X, y, width - RIGHT_MARGIN, y)
    return y - 26


def draw_simple_table(pdf, x: int, y: int, headers: list[str], rows: list[list[str]], col_widths: list[int],
                      regular_font: str, bold_font: str) -> int:
    row_height = 22
    table_width = sum(col_widths)

    # header background
    pdf.setFillColor(colors.HexColor("#E9EEF4"))
    pdf.rect(x, y - row_height + 5, table_width, row_height, fill=True, stroke=False)
    pdf.setFillColor(colors.black)

    pdf.setStrokeColor(colors.grey)
    pdf.setLineWidth(0.4)

    current_x = x
    pdf.setFont(bold_font, BODY_SIZE)
    for i, header in enumerate(headers):
        pdf.drawString(current_x + 6, y - 10, header)
        current_x += col_widths[i]

    pdf.rect(x, y - row_height + 5, table_width, row_height, fill=False, stroke=True)
    current_x = x
    for w in col_widths[:-1]:
        current_x += w
        pdf.line(current_x, y + 5, current_x, y - row_height + 5)

    y -= row_height

    pdf.setFont(regular_font, BODY_SIZE)
    for row in rows:
        current_x = x
        for i, value in enumerate(row):
            pdf.drawString(current_x + 6, y - 10, str(value))
            current_x += col_widths[i]
        pdf.rect(x, y - row_height + 5, table_width, row_height, fill=False, stroke=True)
        current_x = x
        for w in col_widths[:-1]:
            current_x += w
            pdf.line(current_x, y + 5, current_x, y - row_height + 5)
        y -= row_height

    return y - 12


def ensure_space_for_validation(pdf, y: int, needed: int, width: int, height: int, regular_font: str) -> int:
    if y < needed:
        pdf.showPage()
        draw_page_frame(pdf, width, height)
        pdf.setFont(regular_font, BODY_SIZE)
        return TOP_Y
    return y


def load_image_reader(url_or_path: str) -> ImageReader | None:
    if not url_or_path:
        return None
    try:
        if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
            with urllib.request.urlopen(url_or_path, timeout=8) as response:
                data = response.read()
            return ImageReader(BytesIO(data))
        if os.path.exists(url_or_path):
            return ImageReader(url_or_path)
    except Exception:
        return None
    return None


def validation_status_text(row: ValidationRecord) -> str:
    if row.is_match is True:
        result = "일치"
    elif row.is_match is False:
        result = "불일치"
    else:
        result = "판별 불가"

    sensor = row.sensor_predicted_status or "센서 상태 없음"
    observed = row.observed_surface_status or "관찰 상태 없음"
    return f"촬영일: {row.record_date} / 센서 상태: {sensor} / 관찰 상태: {observed} / 검증 결과: {result}"


# ---------------------------
# API
# ---------------------------

@router.post("")
def create_mrv_report(payload: MrvReportCreate, db: Session = Depends(get_db)):
    field = db.query(Field).filter(Field.id == payload.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="해당 field_id가 존재하지 않습니다.")

    existing_report = (
        db.query(MrvReport)
        .filter(
            MrvReport.field_id == payload.field_id,
            MrvReport.report_month == payload.report_month,
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
            AwdDailySummary.record_date < end_date,
        )
        .all()
    )

    if not summaries:
        raise HTTPException(status_code=404, detail="해당 월의 일일 요약 데이터가 없습니다.")

    daily_summaries = aggregate_daily_summaries(summaries)
    total_awd_cycles = count_awd_cycles(daily_summaries)
    flood_days = sum(1 for s in daily_summaries if s.daily_status in ("FLOODED", "OVERFLOODED"))
    carbon_reduction = (Decimal(total_awd_cycles) * Decimal("15.25")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

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
def get_mrv_reports(field_id: int | None = Query(default=None), db: Session = Depends(get_db)):
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
def update_mrv_report_status(report_id: int, payload: MrvReportStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in ALLOWED_MRV_STATUSES:
        raise HTTPException(status_code=400, detail="status는 IN_PROGRESS 또는 COMPLETED만 가능합니다.")

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
    validation = get_validation_summary(report.field_id, start_date, end_date, db)

    summaries = (
        db.query(AwdDailySummary)
        .join(IotNode, IotNode.id == AwdDailySummary.node_id)
        .filter(
            IotNode.field_id == report.field_id,
            AwdDailySummary.record_date >= start_date,
            AwdDailySummary.record_date < end_date,
        )
        .order_by(AwdDailySummary.record_date.asc(), AwdDailySummary.id.asc())
        .all()
    )

    nodes = db.query(IotNode).filter(IotNode.field_id == report.field_id).order_by(IotNode.id.asc()).all()
    daily_summaries = aggregate_daily_summaries(summaries)
    status_counts = summarize_status_counts(daily_summaries)
    weekly_groups = group_summaries_by_week(daily_summaries)
    weekly_dict = {week_no: week_summaries for week_no, week_summaries in weekly_groups}
    month_avg = get_month_avg_inner_level(daily_summaries)
    dominant_status = get_dominant_status(status_counts)
    report_month_kor = format_report_month(report.report_month)

    regular_font, bold_font = register_korean_fonts()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    max_text_width = int(width - LEFT_X - RIGHT_MARGIN)
    pdf.setTitle(f"mrv_report_{report.id}")

    # 표지
    draw_page_frame(pdf, width, height)
    pdf.setFont(bold_font, COVER_TITLE_SIZE)
    pdf.drawCentredString(width / 2, height - 110, "AWD Water Management MRV Report")
    pdf.setLineWidth(1.0)
    pdf.setStrokeColor(colors.black)
    pdf.line(75, height - 135, width - 75, height - 135)

    pdf.setFont(bold_font, COVER_SUBTITLE_SIZE)
    pdf.drawCentredString(width / 2, height - 245, field.field_name)
    pdf.drawCentredString(width / 2, height - 280, f"{report_month_kor} MRV 보고서")

    pdf.setFont(regular_font, COVER_INFO_SIZE)
    created_text = str(report.created_at.date()) if report.created_at else "-"
    pdf.drawCentredString(width / 2, height - 385, f"작성일: {created_text}")
    pdf.drawCentredString(width / 2, height - 410, "팀명: 강안장인")
    pdf.showPage()

    # 목차
    draw_page_frame(pdf, width, height)
    pdf.setFont(bold_font, TOC_TITLE_SIZE)
    pdf.drawCentredString(width / 2, height - 55, "목차")

    toc_items = [
        ("1. 개요 (배경)", "3", 0),
        ("2. 분석 대상 및 기간", "3", 0),
        ("3. 결과 요약", "3", 0),
        ("4. 결과 분석", "4", 0),
        ("4.1 주차별 수위 변화 분석", "4", 1),
        ("4.2 월간 수위 상태 분석", "4", 1),
        ("5. AWD 수행 및 탄소 감축 분석", "5", 0),
        ("6. 검증 결과", "6", 0),
        ("6.1 현장 검증 결과", "6", 1),
        ("6.2 대표 검증 이미지 출력", "6", 1),
        ("7. 향후 계획", "-", 0),
        ("8. 결론", "-", 0),
    ]

    y = height - 125
    pdf.setFont(regular_font, TOC_BODY_SIZE)
    for title, page_no, indent in toc_items:
        x = LEFT_X + indent * 18
        pdf.drawString(x, y, title)
        text_width = pdf.stringWidth(title, regular_font, TOC_BODY_SIZE)
        page_width = pdf.stringWidth(page_no, regular_font, TOC_BODY_SIZE)
        dot_start = x + text_width + 8
        dot_end = width - RIGHT_MARGIN - page_width - 8
        pdf.setDash(1, 2)
        pdf.line(dot_start, y + 2, dot_end, y + 2)
        pdf.setDash()
        pdf.drawRightString(width - RIGHT_MARGIN, y, page_no)
        y -= 25
    pdf.showPage()

    # Page 1: 1~3
    draw_page_frame(pdf, width, height)
    y = TOP_Y

    y = draw_section_title(pdf, "1. 개요 (배경)", y, regular_font, bold_font)
    y = draw_text(
        pdf,
        f"본 보고서는 {field.field_name} 논을 대상으로 {report_month_kor} 동안 수행된 AWD(Alternate Wetting and Drying) 물관리 이력을 분석한 MRV 보고서이다.\n"
        "본 시스템은 IoT 센서를 활용하여 논의 수위 데이터를 자동으로 수집하고, 이를 기반으로 일 단위 상태를 분석하여 물관리 수행 여부를 기록하도록 설계되었다.",
        LEFT_X, y, max_text_width, regular_font, BODY_SIZE, BODY_LINE_HEIGHT,
    )
    y -= PARAGRAPH_GAP
    y = draw_text(pdf, "수위 상태는 내부 수위를 기준으로 다음과 같이 구분된다.", LEFT_X, y, max_text_width, regular_font)
    y = draw_bullets(
        pdf,
        [
            "OVERFLOODED: 과다 담수 상태",
            "FLOODED: 적정 담수 상태",
            "DRYING: 건조 진행 상태",
            "DRY: 재관개 필요 상태",
        ],
        LEFT_X + 8, y, max_text_width - 8, regular_font,
    )
    y -= PARAGRAPH_GAP
    y = draw_text(pdf, "각 날짜별 상태는 하루 동안 수집된 센서 데이터의 평균 수위를 기준으로 대표 상태로 정의된다.", LEFT_X, y, max_text_width, regular_font)

    y = draw_divider(pdf, y - 4, width)

    y = draw_section_title(pdf, "2. 분석 대상 및 기간", y, regular_font, bold_font)
    y = draw_simple_table(
        pdf, LEFT_X, y,
        ["항목", "내용"],
        [
            ["대상 논", field.field_name],
            ["분석 기간", report_month_kor],
            ["사용 노드 수", f"{len(nodes)}개"],
            ["보고서 생성일", created_text],
        ],
        [150, 300], regular_font, bold_font,
    )

    y = draw_divider(pdf, y + 2, width)

    y = draw_section_title(pdf, "3. 결과 요약", y, regular_font, bold_font)
    y = draw_text(pdf, "분석 기간 동안의 일일 상태를 집계한 결과는 다음과 같다.", LEFT_X, y, max_text_width, regular_font)
    y -= 4
    y = draw_simple_table(
        pdf, LEFT_X, y,
        ["상태", "일수"],
        [
            ["OVERFLOODED", f"{status_counts['OVERFLOODED']}일"],
            ["FLOODED", f"{status_counts['FLOODED']}일"],
            ["DRYING", f"{status_counts['DRYING']}일"],
            ["DRY", f"{status_counts['DRY']}일"],
        ],
        [200, 150], regular_font, bold_font,
    )
    y = draw_text(
        pdf,
        f"전체적으로 {dominant_status} 상태가 가장 많이 관측되었으며, 논의 수위는 해당 상태를 중심으로 변화하였다. "
        f"AWD 수행 기준은 DRY 상태 이후 FLOODED 상태로 전환되는 경우를 1회로 정의하며, 해당 기간 동안 AWD 수행 횟수는 {report.total_awd_cycles}회로 나타났다.",
        LEFT_X, y, max_text_width, regular_font,
    )
    pdf.showPage()

    # Page 2: 4
    draw_page_frame(pdf, width, height)
    y = TOP_Y
    y = draw_section_title(pdf, "4. 결과 분석", y, regular_font, bold_font)
    y = draw_sub_title(pdf, "4.1 주차별 수위 변화 분석", y, bold_font)

    for week_no in range(1, 5):
        week_lines = make_weekly_summary_text(week_no, weekly_dict.get(week_no, []))
        for idx, line in enumerate(week_lines):
            if idx == 0:
                pdf.setFont(bold_font, BODY_SIZE)
                pdf.drawString(LEFT_X, y, line)
                y -= BODY_LINE_HEIGHT
            else:
                y = draw_text(pdf, line, LEFT_X + 8, y, max_text_width - 8, regular_font, BODY_SIZE, BODY_LINE_HEIGHT)
        y -= 8

    y = draw_sub_title(pdf, "4.2 월간 수위 상태 분석", y, bold_font)
    if month_avg is not None:
        monthly_text = (
            f"분석 기간 동안 평균 내부 수위는 {month_avg:.2f}cm로 나타났다. "
            f"이는 전체적으로 수위가 변화하는 경향을 의미하며, 주요 상태는 {dominant_status}으로 확인된다. "
            "전체적으로 건조 진행 상태와 담수 상태가 교차하며 나타났고, 일부 구간에서는 과다 담수 상태가 발생하는 등 수위 변동이 존재하였다. "
            "그러나 건조 이후 재관개가 충분히 이루어지지 않은 경우에는 AWD 사이클이 제한적으로 형성될 수 있다."
        )
    else:
        monthly_text = "분석 기간 동안 평균 내부 수위 데이터가 없어 월간 수위 상태 분석이 제한된다."
    y = draw_text(pdf, monthly_text, LEFT_X, y, max_text_width, regular_font, BODY_SIZE, BODY_LINE_HEIGHT)
    pdf.showPage()

    # Page 3: 5
    draw_page_frame(pdf, width, height)
    y = TOP_Y
    y = draw_section_title(pdf, "5. AWD 수행 및 탄소 감축 분석", y, regular_font, bold_font)

    y = draw_sub_title(pdf, "[AWD 수행 횟수 기준]", y, bold_font)
    y = draw_text(pdf, "논이 DRY 상태 이후 FLOODED 상태로 전환되는 경우를 1회로 정의한다.", LEFT_X, y, max_text_width, regular_font)
    y = draw_bullets(pdf, [f"{report_month_kor} AWD 수행 횟수: {report.total_awd_cycles}회"], LEFT_X + 8, y - 4, max_text_width, regular_font)
    y -= 14

    y = draw_sub_title(pdf, "[탄소 감축량 계산]", y, bold_font)
    y = draw_text(pdf, f"이에 따라 {report_month_kor} 탄소 감축량은 AWD 수행 횟수를 기준으로 다음과 같이 산출된다.", LEFT_X, y, max_text_width, regular_font)
    y = draw_bullets(
        pdf,
        [
            "탄소 감축량 = AWD 수행 횟수 × 15.25 (kgCO2-eq)",
            f"결과: {report.carbon_reduction} kgCO2-eq",
        ],
        LEFT_X + 8, y - 4, max_text_width, regular_font,
    )
    y = draw_text(pdf, "(본 결과는 센서 기반 수위 데이터 분석에 따른 추정값임)", LEFT_X, y - 4, max_text_width, regular_font)
    y -= 14

    y = draw_sub_title(pdf, "[시사점]", y, bold_font)
    if report.total_awd_cycles == 0:
        insight_text = (
            "건조 단계 이후 재관개가 이루어지지 않아 AWD 사이클이 형성되지 않았다.\n"
            "이는 물관리 전략이 건조 단계 중심으로 운영되었음을 의미한다.\n"
            "향후 AWD 수행을 위해서는 DRY 상태 이후 적절한 시점에서의 계획적 재관개가 필요하다."
        )
    else:
        insight_text = (
            f"분석 기간 동안 AWD 사이클이 {report.total_awd_cycles}회 확인되었다.\n"
            "이는 건조 이후 재관개가 수행되어 AWD 물관리 흐름이 일부 형성되었음을 의미한다.\n"
            "향후에는 주기적인 검증 데이터 확보를 통해 AWD 수행 결과의 신뢰성을 높일 필요가 있다."
        )
    y = draw_text(pdf, insight_text, LEFT_X, y, max_text_width, regular_font)
    pdf.showPage()

    # Page 4+: 6 검증 결과. 사진이 길면 자동 페이지 넘김.
    draw_page_frame(pdf, width, height)
    y = TOP_Y
    y = draw_section_title(pdf, "6. 검증 결과", y, regular_font, bold_font)
    y = draw_sub_title(pdf, "6.1 현장 검증 결과", y, bold_font)

    if validation["validation_sample_count"] > 0:
        y = draw_text(
            pdf,
            "분석 기간 동안 수집된 현장 검증 데이터와 센서 기반 상태를 비교하여 검증 결과를 산정하였다.",
            LEFT_X, y, max_text_width, regular_font,
        )
        y -= 4
        y = draw_simple_table(
            pdf, LEFT_X, y,
            ["항목", "값"],
            [
                ["검증 방법", validation["validation_method"]],
                ["검증 샘플 수", f"{validation['validation_sample_count']}건"],
                ["일치 수", f"{validation['validation_match_count']}건"],
                ["불일치 수", f"{validation['validation_mismatch_count']}건"],
                ["판별 불가", f"{validation['validation_unknown_count']}건"],
                ["검증 정확도", f"{validation['validation_accuracy']}%"],
            ],
            [160, 260], regular_font, bold_font,
        )
        y = draw_text(
            pdf,
            "검증 결과는 센서 기반 상태 판정의 신뢰성을 확인하기 위한 보조 자료로 활용된다. "
            "일부 불일치 사례는 촬영 시점과 센서 측정 시점 간 차이 또는 수위 경계 구간에서의 판단 차이에 의해 발생할 수 있다.",
            LEFT_X, y, max_text_width, regular_font,
        )
    else:
        y = draw_text(
            pdf,
            "해당 기간 동안 등록된 현장 검증 데이터가 없어 검증 결과 분석이 제한된다.\n"
            "향후 검증 데이터가 추가될 경우, 센서 기반 상태와 실제 관찰 결과 간의 일치 여부를 통해 정확도 분석이 가능하다.",
            LEFT_X, y, max_text_width, regular_font,
        )

    y -= 18
    y = ensure_space_for_validation(pdf, y, 190, width, height, regular_font)
    y = draw_sub_title(pdf, "6.2 대표 검증 이미지 출력", y, bold_font)

    representative_rows = validation["representative_rows"]
    if representative_rows:
        y = draw_text(
            pdf,
            "본 보고서에서는 분석 기간을 기준으로 월 초, 월 중, 월 후 시점을 대표하는 이미지를 제시한다.",
            LEFT_X, y, max_text_width, regular_font,
        )
        y -= 10
        for label, row in representative_rows:
            y = ensure_space_for_validation(pdf, y, 250, width, height, regular_font)
            pdf.setFont(bold_font, SUB_TITLE_SIZE)
            pdf.drawString(LEFT_X, y, f"[{label}] {row.image_title or '대표 검증 이미지'}")
            y -= 18

            img = load_image_reader(row.image_url)
            if img:
                image_width = 230
                image_height = 130
                pdf.drawImage(img, LEFT_X, y - image_height, width=image_width, height=image_height, preserveAspectRatio=True, mask='auto')
                y -= image_height + 12
            else:
                y = draw_text(pdf, f"이미지 URL: {row.image_url}", LEFT_X, y, max_text_width, regular_font)
                y -= 6

            y = draw_text(pdf, validation_status_text(row), LEFT_X, y, max_text_width, regular_font)
            if row.note:
                y = draw_text(pdf, f"비고: {row.note}", LEFT_X, y, max_text_width, regular_font)
            y -= 12
    else:
        y = draw_text(
            pdf,
            "해당 기간에 등록된 대표 검증 이미지가 존재하지 않는다.\n"
            "향후 검증 이미지가 확보될 경우, 월간 대표 이미지를 통해 상태 검증 근거를 시각적으로 제공할 수 있다.",
            LEFT_X, y, max_text_width, regular_font,
        )

    # 7~8은 검증 결과가 몇 페이지에서 끝나든 항상 새 페이지에서 시작
    pdf.showPage()
    draw_page_frame(pdf, width, height)
    y = TOP_Y
    y = draw_section_title(pdf, "7. 향후 계획", y, regular_font, bold_font)
    y = draw_bullets(
        pdf,
        [
            "AWD 사이클 확보를 위한 계획적 재관개 전략 수립",
            "IoT 센서 기반 자동 관개 시스템 도입 검토",
            "현장 검증 데이터(이미지) 수집 및 검증 체계 강화",
            "MRV 보고서 자동화 및 시각화 기능 개선",
        ],
        LEFT_X + 8, y, max_text_width, regular_font,
    )

    y -= 28
    y = draw_section_title(pdf, "8. 결론", y, regular_font, bold_font)
    if report.total_awd_cycles == 0:
        conclusion = (
            f"본 분석 기간 동안 논은 전반적으로 {dominant_status} 상태를 중심으로 변화하였으며, AWD 수행은 발생하지 않았다. "
            "이는 건조 이후 재관개가 이루어지지 않았기 때문으로 판단된다.\n"
            "본 시스템을 통해 IoT 기반 수위 데이터 수집, 상태 분석, MRV 보고서 생성까지의 자동화 가능성을 확인할 수 있었으며, "
            "향후 물관리 전략 개선 및 검증 데이터 확보를 통해 보다 정교한 MRV 시스템 구축이 가능할 것으로 기대된다."
        )
    else:
        conclusion = (
            f"본 분석 기간 동안 AWD 수행은 {report.total_awd_cycles}회 관측되었으며, 탄소 감축 추정량은 {report.carbon_reduction} kgCO2-eq로 산정되었다.\n"
            "본 시스템은 IoT 센서 기반 수위 데이터 수집과 MRV 보고서 생성을 자동화할 수 있음을 확인하였으며, "
            "향후 검증 데이터 확대를 통해 보고서 신뢰도를 높일 수 있다."
        )
    y = draw_text(pdf, conclusion, LEFT_X, y, max_text_width, regular_font)

    pdf.save()
    buffer.seek(0)

    filename = f"mrv_report_{report.id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
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
            AwdDailySummary.record_date < end_date,
        )
        .order_by(AwdDailySummary.record_date.asc(), AwdDailySummary.id.asc())
        .all()
    )

    daily_summaries = aggregate_daily_summaries(summaries)
    status_counts = summarize_status_counts(daily_summaries)
    representative_images = validation["representative_images"]

    workbook = Workbook()

    summary_sheet = workbook.active
    summary_sheet.title = "MRV Summary"
    summary_sheet.append(["항목", "값"])
    summary_sheet.append(["field_name", field.field_name])
    summary_sheet.append(["report_month", report.report_month])
    summary_sheet.append(["total_awd_cycles", report.total_awd_cycles])
    summary_sheet.append(["flood_days", report.flood_days])
    summary_sheet.append(["overflooded_days", status_counts["OVERFLOODED"]])
    summary_sheet.append(["flooded_days", status_counts["FLOODED"]])
    summary_sheet.append(["drying_days", status_counts["DRYING"]])
    summary_sheet.append(["dry_days", status_counts["DRY"]])
    summary_sheet.append(["carbon_reduction_kgco2eq", float(report.carbon_reduction) if report.carbon_reduction is not None else None])
    summary_sheet.append(["status", report.status])
    summary_sheet.append(["created_at", str(report.created_at)])

    daily_sheet = workbook.create_sheet(title="Daily Data")
    daily_sheet.append(["date", "avg_inner_level", "status"])
    for s in daily_summaries:
        daily_sheet.append([
            str(s.record_date),
            float(s.avg_inner_level) if s.avg_inner_level is not None else None,
            s.daily_status,
        ])

    validation_sheet = workbook.create_sheet(title="Validation")
    validation_sheet.append(["항목", "값"])
    validation_sheet.append(["validation_method", validation["validation_method"]])
    validation_sheet.append(["validation_sample_count", validation["validation_sample_count"]])
    validation_sheet.append(["validation_match_count", validation["validation_match_count"]])
    validation_sheet.append(["validation_mismatch_count", validation["validation_mismatch_count"]])
    validation_sheet.append(["validation_unknown_count", validation["validation_unknown_count"]])
    validation_sheet.append(["validation_accuracy", validation["validation_accuracy"]])
    validation_sheet.append(["validation_note", validation["validation_note"]])

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
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("")
def delete_mrv_report(field_id: int, report_month: str, db: Session = Depends(get_db)):
    report = db.query(MrvReport).filter(
        MrvReport.field_id == field_id,
        MrvReport.report_month == report_month,
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="보고서 없음")

    db.delete(report)
    db.commit()

    return success_response(None, "MRV 보고서 삭제 성공")

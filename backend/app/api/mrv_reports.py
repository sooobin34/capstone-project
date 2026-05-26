import os
import urllib.request
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font as XLFont, PatternFill, Side
from openpyxl.utils import get_column_letter
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
from app.models.sensor_log import SensorLog

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
TOP_Y = 756  # A4 height(약 841) - 85: 본문을 위쪽 여백에서 충분히 내림
BOTTOM_Y = 55


def _font_path(filename: str) -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts", filename))


def register_korean_fonts() -> tuple[str, str]:
    """
    일반 본문 폰트와 Bold 폰트를 함께 등록한다.
    Render 서버에서는 Windows 폰트가 없으므로 app/fonts 폴더의 Nanum 폰트를 우선 사용한다.
    """
    regular_candidates = [
        _font_path("NanumMyeongjo.ttf"),
        _font_path("NanumGothic.ttf"),
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
    labels = ["월 초", "월 중", "월 말"]
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

    sensor_valid_rows = [row for row in rows if row.is_match is not None]
    match_count = sum(1 for row in sensor_valid_rows if row.is_match is True)
    mismatch_count = sum(1 for row in sensor_valid_rows if row.is_match is False)
    unknown_count = sum(1 for row in rows if row.is_match is None)
    accuracy = round((match_count / len(sensor_valid_rows)) * 100, 2) if sensor_valid_rows else 0

    ai_sensor_rows = [row for row in rows if row.ai_sensor_match is not None]
    ai_sensor_match_count = sum(1 for row in ai_sensor_rows if row.ai_sensor_match is True)
    ai_sensor_mismatch_count = sum(1 for row in ai_sensor_rows if row.ai_sensor_match is False)
    ai_sensor_unknown_count = sample_count - len(ai_sensor_rows)
    ai_sensor_accuracy = round((ai_sensor_match_count / len(ai_sensor_rows)) * 100, 2) if ai_sensor_rows else 0

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
        "ai_sensor_match_count": ai_sensor_match_count,
        "ai_sensor_mismatch_count": ai_sensor_mismatch_count,
        "ai_sensor_unknown_count": ai_sensor_unknown_count,
        "ai_sensor_accuracy": ai_sensor_accuracy,
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
        if prev_status == "DRY" and current_status in ("DRYING", "FLOODED", "OVERFLOODED"):
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



def draw_page_number(pdf, width, page_no: int, regular_font: str):
    """각 페이지 하단 중앙에 쪽수를 표시한다."""
    pdf.setFont(regular_font, 9)
    pdf.setFillColor(colors.black)
    pdf.drawCentredString(width / 2, 28, str(page_no))

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


def ensure_space_for_validation(
    pdf,
    y: int,
    needed: int,
    width: int,
    height: int,
    regular_font: str,
    page_no_ref: list[int],
) -> int:
    if y < needed:
        draw_page_number(pdf, width, page_no_ref[0], regular_font)
        pdf.showPage()
        page_no_ref[0] += 1
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


def validation_result_text(value):
    if value is True:
        return "일치"
    if value is False:
        return "불일치"
    return "판별 불가"


def get_sensor_ai_status_for_validation(row: ValidationRecord, db: Session):
    """
    검증 사진 촬영 시점 기준으로 센서 수위(cm)를 LOW/MID/HIGH 구간으로 변환한다.
    1순위: captured_at 기준 근접 sensor_log
    2순위: daily_summary.avg_inner_level
    """
    if row.node_id is None:
        return None

    sensor_level = None

    if row.captured_at is not None:
        target = row.captured_at.replace(tzinfo=None)
        start_at = target - timedelta(hours=3)
        end_at = target + timedelta(hours=3)

        candidates = (
            db.query(SensorLog)
            .filter(
                SensorLog.node_id == row.node_id,
                SensorLog.measured_at >= start_at,
                SensorLog.measured_at <= end_at,
            )
            .all()
        )

        if candidates:
            nearest_log = min(
                candidates,
                key=lambda log: abs((log.measured_at.replace(tzinfo=None) - target).total_seconds()),
            )
            sensor_level = nearest_log.inner_water_level

    if sensor_level is None:
        summary = (
            db.query(AwdDailySummary)
            .filter(
                AwdDailySummary.node_id == row.node_id,
                AwdDailySummary.record_date == row.record_date,
            )
            .order_by(AwdDailySummary.id.desc())
            .first()
        )
        sensor_level = summary.avg_inner_level if summary else None

    if sensor_level is None:
        return None

    value = float(sensor_level)
    if value < 2:
        return "LOW"
    if value < 4:
        return "MID"
    return "HIGH"


def validation_status_text(row: ValidationRecord, db: Session) -> str:
    sensor_observed_result = validation_result_text(row.is_match)
    ai_sensor_result = validation_result_text(row.ai_sensor_match)

    observed = row.observed_surface_status or "관찰값 없음"
    sensor_surface = row.sensor_predicted_status or "센서 표면 판정 없음"
    sensor_ai_status = get_sensor_ai_status_for_validation(row, db) or "센서 수위 구간 없음"
    ai = row.ai_predicted_status or "AI 분석 없음"

    return (
        f"촬영일: {row.record_date} / "
        f"사람 관찰값: {observed} / "
        f"센서 기반 표면 판정: {sensor_surface} / "
        f"센서-관찰 검증: {sensor_observed_result} / "
        f"센서 수위 구간: {sensor_ai_status} / "
        f"AI 예측 구간: {ai} / "
        f"AI-센서 구간 비교: {ai_sensor_result}"
    )


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
            "ai_sensor_match_count": validation["ai_sensor_match_count"],
            "ai_sensor_mismatch_count": validation["ai_sensor_mismatch_count"],
            "ai_sensor_accuracy": validation["ai_sensor_accuracy"],
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
    page_no_ref = [1]

    # 표지
    draw_page_frame(pdf, width, height)

    pdf.setFont(bold_font, COVER_TITLE_SIZE)
    pdf.drawCentredString(width / 2, height - 110, "AWD Water Management MRV Report")

    pdf.setLineWidth(1.0)
    pdf.setStrokeColor(colors.black)
    pdf.line(75, height - 135, width - 75, height - 135)

    logo_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
    )

    if os.path.exists(logo_path):
        pdf.drawImage(
            logo_path,
            width / 2 - 80,
            height - 330,
            width=160,
            height=160,
            preserveAspectRatio=True,
            mask="auto"
        )

    pdf.setFont(bold_font, COVER_SUBTITLE_SIZE)
    pdf.drawCentredString(width / 2, height - 420, field.field_name)
    pdf.drawCentredString(width / 2, height - 455, f"{report_month_kor} MRV 보고서")

    pdf.setFont(regular_font, COVER_INFO_SIZE)
    created_text = str(report.created_at.date()) if report.created_at else "-"
    pdf.drawCentredString(width / 2, height - 545, f"작성일: {created_text}")
    pdf.drawCentredString(width / 2, height - 570, "팀명: 강안장인")

    draw_page_number(pdf, width, page_no_ref[0], regular_font)
    pdf.showPage()
    page_no_ref[0] += 1

    # 목차
    pdf.setFont(bold_font, TOC_TITLE_SIZE)
    pdf.drawCentredString(width / 2, height - 55, "목차")

    section_7_page = "8" if len(validation["representative_rows"]) >= 2 else "7"

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
        ("7. 향후 계획", section_7_page, 0),
        ("8. 결론", section_7_page, 0),
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
    draw_page_number(pdf, width, page_no_ref[0], regular_font)
    pdf.showPage()
    page_no_ref[0] += 1

    # Page 1: 1~3
    y = TOP_Y

    y = draw_section_title(pdf, "1. 개요 (배경)", y, regular_font, bold_font)
    y = draw_text(
        pdf,
        f"이 보고서는 {field.field_name}을 대상으로 {report_month_kor} 동안 수행된 AWD(Alternate Wetting and Drying) 물관리 이력을 분석한 MRV 보고서이다.\n"
        "이 시스템은 IoT 센서를 활용하여 논의 수위 데이터를 자동으로 수집하고, 이를 기반으로 일 단위 상태를 분석하여 물관리 수행 여부를 기록하도록 설계되었다.",
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
        f"AWD 수행 기준은 DRY 상태 이후 DRYING, FLOODED 또는 OVERFLOODED 상태로 전환되는 경우를 1회로 정의하며, 해당 기간 동안 AWD 수행 횟수는 {report.total_awd_cycles}회로 나타났다.",
        LEFT_X, y, max_text_width, regular_font,
    )
    draw_page_number(pdf, width, page_no_ref[0], regular_font)
    pdf.showPage()
    page_no_ref[0] += 1

    # Page 2: 4
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
    draw_page_number(pdf, width, page_no_ref[0], regular_font)
    pdf.showPage()
    page_no_ref[0] += 1

    # Page 3: 5
    y = TOP_Y
    y = draw_section_title(pdf, "5. AWD 수행 및 탄소 감축 분석", y, regular_font, bold_font)

    y = draw_sub_title(pdf, "[AWD 수행 횟수 기준]", y, bold_font)
    y = draw_text(pdf, "논이 DRY 상태 이후 DRYING, FLOODED 또는 OVERFLOODED 상태로 전환되는 경우를 1회로 정의한다.", LEFT_X, y, max_text_width, regular_font)
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
    draw_page_number(pdf, width, page_no_ref[0], regular_font)
    pdf.showPage()
    page_no_ref[0] += 1

    # Page 4+: 6 검증 결과. 사진이 길면 자동 페이지 넘김.
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
                ["센서-관찰 검증 정확도", f"{validation['validation_accuracy']}%"],
                ["AI-센서 일치 수", f"{validation['ai_sensor_match_count']}건"],
                ["AI-센서 불일치 수", f"{validation['ai_sensor_mismatch_count']}건"],
                ["AI-센서 판별 불가", f"{validation['ai_sensor_unknown_count']}건"],
                ["AI-센서 일치율", f"{validation['ai_sensor_accuracy']}%"],
            ],
            [160, 260], regular_font, bold_font,
        )
        y = draw_text(
            pdf,
            "검증 결과는 센서 기반 상태 판정의 신뢰성을 확인하기 위한 보조 자료로 활용된다. "
            "일부 불일치 사례는 촬영 시점과 센서 측정 시점 간 차이 또는 수위 경계 구간에서의 판단 차이에 의해 발생할 수 있다. "
            "AI-센서 일치율은 촬영 시점 기준 근접 센서 로그의 수위값을 LOW/MID/HIGH 기준으로 변환한 뒤 AI 예측 결과와 비교하여 산정하였다. "
            "근접 센서 로그가 없는 경우 일일 요약 평균 수위값(daily_summary.avg_inner_level)을 보조 기준으로 사용하며, 비교 가능한 수위값이 없는 데이터는 정확도 산정에서 제외하였다.",
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
    y = ensure_space_for_validation(pdf, y, 300, width, height, regular_font, page_no_ref)
    y = draw_sub_title(pdf, "6.2 대표 검증 이미지 출력", y, bold_font)

    representative_rows = validation["representative_rows"]
    if representative_rows:
        y = draw_text(
            pdf,
            "본 보고서에서는 분석 기간을 기준으로 월 초, 월 중, 월 말 시점을 대표하는 이미지를 제시한다.",
            LEFT_X, y, max_text_width, regular_font,
        )
        y -= 10
        card_width = 160
        card_height = 245
        gap = 12
        start_x = LEFT_X
        card_y = y

        for idx, (label, row) in enumerate(representative_rows[:3]):
            x = start_x + idx * (card_width + gap)

            pdf.setStrokeColor(colors.lightgrey)
            pdf.setLineWidth(0.5)
            pdf.roundRect(x, card_y - card_height, card_width, card_height, 8, stroke=True, fill=False)

            pdf.setFont(bold_font, 10)
            pdf.drawString(x + 8, card_y - 18, f"{label} 대표 이미지")

            img = load_image_reader(row.image_url)
            if img:
                pdf.drawImage(
                    img,
                    x + 8,
                    card_y - 120,
                    width=card_width - 16,
                    height=90,
                    preserveAspectRatio=True,
                    mask="auto"
                )

            sensor_ai_status = get_sensor_ai_status_for_validation(row, db) or "-"
            ai_status = row.ai_predicted_status or "-"
            observed = row.observed_surface_status or "-"
            sensor_surface = row.sensor_predicted_status or "-"
            match_text = validation_result_text(row.is_match)
            ai_match_text = validation_result_text(row.ai_sensor_match)

            info_lines = [
                f"촬영일: {row.record_date}",
                f"사람 관찰: {observed}",
                f"센서 표면: {sensor_surface}",
                f"센서 구간: {sensor_ai_status}",
                f"AI 구간: {ai_status}",
                f"검증: {match_text}",
                f"AI-센서: {ai_match_text}",
            ]

            text_y = card_y - 138
            pdf.setFont(regular_font, 8)
            for line in info_lines:
                pdf.drawString(x + 8, text_y, line)
                text_y -= 12

        y = card_y - card_height - 20
    
    else:
        y = draw_text(
            pdf,
            "해당 기간에 등록된 대표 검증 이미지가 존재하지 않는다.\n"
            "향후 검증 이미지가 확보될 경우, 월간 대표 이미지를 통해 상태 검증 근거를 시각적으로 제공할 수 있다.",
            LEFT_X, y, max_text_width, regular_font,
        )

    # 7~8은 검증 결과가 몇 페이지에서 끝나든 항상 새 페이지에서 시작
    draw_page_number(pdf, width, page_no_ref[0], regular_font)
    pdf.showPage()
    page_no_ref[0] += 1
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

    draw_page_number(pdf, width, page_no_ref[0], regular_font)
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
    validation_rows = get_validation_rows(report.field_id, start_date, end_date, db)

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
    dominant_status = get_dominant_status(status_counts)
    month_avg = get_month_avg_inner_level(daily_summaries)
    report_month_kor = format_report_month(report.report_month)
    created_text = str(report.created_at.date()) if report.created_at else "-"

    workbook = Workbook()

    # 공통 Excel 스타일
    title_font = XLFont(name="맑은 고딕", size=16, bold=True)
    section_font = XLFont(name="맑은 고딕", size=12, bold=True)
    header_font = XLFont(name="맑은 고딕", size=10, bold=True)
    body_font = XLFont(name="맑은 고딕", size=10)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    thin_side = Side(style="thin", color="808080")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    header_fill = PatternFill("solid", fgColor="D9E2F3")
    section_fill = PatternFill("solid", fgColor="EAF1F8")
    note_fill = PatternFill("solid", fgColor="F7F7F7")

    def set_widths(sheet, widths: dict[str, float]):
        for col, width in widths.items():
            sheet.column_dimensions[col].width = width

    def style_range(sheet, cell_range: str, fill=None, font=None, alignment=None, border_style=True):
        for row in sheet[cell_range]:
            for cell in row:
                if fill:
                    cell.fill = fill
                if font:
                    cell.font = font
                if alignment:
                    cell.alignment = alignment
                if border_style:
                    cell.border = border

    def put_section_title(sheet, row: int, title: str, last_col: str = "H") -> int:
        sheet.merge_cells(f"A{row}:{last_col}{row}")
        cell = sheet[f"A{row}"]
        cell.value = title
        cell.font = section_font
        cell.fill = section_fill
        cell.alignment = left
        style_range(sheet, f"A{row}:{last_col}{row}", fill=section_fill, font=section_font, alignment=left)
        sheet.row_dimensions[row].height = 24
        return row + 1

    def put_kv(sheet, row: int, key: str, value, key_range: str, value_range: str) -> int:
        sheet.merge_cells(key_range.format(row=row))
        sheet.merge_cells(value_range.format(row=row))
        key_cell = sheet[f"A{row}"]
        value_col = value_range.split("{")[0].split(":")[-1].rstrip("0123456789") or "C"
        # value_range는 보통 C{row}:H{row} 형태이므로 시작 열을 직접 계산
        value_cell_ref = value_range.format(row=row).split(":")[0]
        value_cell = sheet[value_cell_ref]
        key_cell.value = key
        value_cell.value = value
        style_range(sheet, key_range.format(row=row), fill=header_fill, font=header_font, alignment=center)
        style_range(sheet, value_range.format(row=row), font=body_font, alignment=left)
        sheet.row_dimensions[row].height = 22
        return row + 1

    # -----------------------------
    # 시트1: 보고서형 요약 템플릿
    # -----------------------------
    summary_sheet = workbook.active
    summary_sheet.title = "요약"
    summary_sheet.sheet_view.showGridLines = False
    set_widths(summary_sheet, {
        "A": 4, "B": 16, "C": 16, "D": 16, "E": 16, "F": 16, "G": 16, "H": 18
    })

    summary_sheet.merge_cells("A1:H1")
    summary_sheet["A1"] = "AWD Water Management MRV Report"
    summary_sheet["A1"].font = title_font
    summary_sheet["A1"].alignment = center
    summary_sheet.row_dimensions[1].height = 32

    summary_sheet.merge_cells("A2:H2")
    summary_sheet["A2"] = f"{field.field_name} / {report_month_kor} MRV 보고서"
    summary_sheet["A2"].font = XLFont(name="맑은 고딕", size=11, bold=True)
    summary_sheet["A2"].alignment = center
    summary_sheet.row_dimensions[2].height = 24

    row = 4
    row = put_section_title(summary_sheet, row, "1. 분석 대상 및 기간")
    row = put_kv(summary_sheet, row, "대상 논", field.field_name, "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "분석 기간", report_month_kor, "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "사용 노드 수", f"{len(nodes)}개", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "보고서 생성일", created_text, "A{row}:B{row}", "C{row}:H{row}")

    row += 1
    row = put_section_title(summary_sheet, row, "2. 결과 요약")
    summary_sheet.merge_cells(f"A{row}:D{row}")
    summary_sheet.merge_cells(f"E{row}:H{row}")
    summary_sheet[f"A{row}"] = "상태"
    summary_sheet[f"E{row}"] = "일수"
    style_range(summary_sheet, f"A{row}:H{row}", fill=header_fill, font=header_font, alignment=center)
    row += 1
    for status, days in [
        ("OVERFLOODED", status_counts["OVERFLOODED"]),
        ("FLOODED", status_counts["FLOODED"]),
        ("DRYING", status_counts["DRYING"]),
        ("DRY", status_counts["DRY"]),
    ]:
        summary_sheet.merge_cells(f"A{row}:D{row}")
        summary_sheet.merge_cells(f"E{row}:H{row}")
        summary_sheet[f"A{row}"] = status
        summary_sheet[f"E{row}"] = f"{days}일"
        style_range(summary_sheet, f"A{row}:H{row}", font=body_font, alignment=center)
        row += 1

    row += 1
    row = put_section_title(summary_sheet, row, "3. AWD 수행 및 탄소 감축 분석")
    row = put_kv(summary_sheet, row, "AWD 수행 기준", "DRY 상태 이후 FLOODED 상태로 전환되는 경우를 1회로 정의", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "AWD 수행 횟수", f"{report.total_awd_cycles}회", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "탄소 감축 산식", "AWD 수행 횟수 × 15.25 (kgCO2-eq)", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "탄소 감축량", f"{report.carbon_reduction} kgCO2-eq", "A{row}:B{row}", "C{row}:H{row}")

    row += 1
    row = put_section_title(summary_sheet, row, "4. 검증 결과")
    row = put_kv(summary_sheet, row, "검증 방법", validation["validation_method"], "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "샘플 수", f"{validation['validation_sample_count']}건", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "일치 / 불일치", f"{validation['validation_match_count']}건 / {validation['validation_mismatch_count']}건", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "센서-관찰 검증 정확도", f"{validation['validation_accuracy']}%", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "AI-센서 일치", f"{validation['ai_sensor_match_count']}건", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "AI-센서 불일치", f"{validation['ai_sensor_mismatch_count']}건", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "AI-센서 판별 불가", f"{validation['ai_sensor_unknown_count']}건", "A{row}:B{row}", "C{row}:H{row}")
    row = put_kv(summary_sheet, row, "AI-센서 일치율", f"{validation['ai_sensor_accuracy']}%", "A{row}:B{row}", "C{row}:H{row}")

    row += 1
    row = put_section_title(summary_sheet, row, "5. 결론 및 향후 계획")
    conclusion = (
        f"분석 기간 동안 주요 상태는 {dominant_status}로 확인되었으며, "
        f"AWD 수행 횟수는 {report.total_awd_cycles}회, 탄소 감축량은 {report.carbon_reduction} kgCO2-eq로 산정되었다."
    )
    if report.total_awd_cycles == 0:
        plan = "향후 DRY 상태 이후 적절한 시점의 계획적 재관개와 현장 검증 데이터 확보가 필요하다."
    else:
        plan = "향후 검증 데이터 확대와 주기적 수위 관리 기준 보완을 통해 MRV 신뢰도를 높일 필요가 있다."
    summary_sheet.merge_cells(f"A{row}:H{row + 2}")
    summary_sheet[f"A{row}"] = f"{conclusion}\n{plan}"
    style_range(summary_sheet, f"A{row}:H{row + 2}", fill=note_fill, font=body_font, alignment=left)
    summary_sheet.row_dimensions[row].height = 55

    # -----------------------------
    # 시트2: 날짜별 흐름 데이터
    # 한 달 흐름을 날짜별 1행으로 확인하기 위한 시트
    # -----------------------------
    daily_grouped = defaultdict(list)
    for s in summaries:
        daily_grouped[s.record_date].append(s)

    representative_by_date = {s.record_date: s for s in daily_summaries}
    node_ids = [node.id for node in nodes]

    flow_sheet = workbook.create_sheet(title="날짜별 흐름 데이터")
    flow_sheet.sheet_view.showGridLines = False

    # 기본 열: 날짜, 대표 평균 수위, 대표 상태 + 노드별 수위/상태
    flow_headers = ["날짜", "대표 평균 수위(cm)", "대표 상태"]
    for node_id in node_ids:
        flow_headers.extend([f"노드 {node_id} 수위(cm)", f"노드 {node_id} 상태"])

    flow_sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(flow_headers))
    flow_sheet["A1"] = "날짜별 흐름 데이터"
    flow_sheet["A1"].font = title_font
    flow_sheet["A1"].alignment = center
    flow_sheet.row_dimensions[1].height = 30
    flow_sheet.append([])
    flow_sheet.append(flow_headers)

    for col_idx in range(1, len(flow_headers) + 1):
        cell = flow_sheet.cell(row=3, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center
        cell.border = border

    flow_sheet.column_dimensions["A"].width = 16
    flow_sheet.column_dimensions["B"].width = 20
    flow_sheet.column_dimensions["C"].width = 18
    for col_idx in range(4, len(flow_headers) + 1):
        flow_sheet.column_dimensions[get_column_letter(col_idx)].width = 18

    current_row = 4
    for record_date in sorted(daily_grouped.keys()):
        node_map = {item.node_id: item for item in daily_grouped[record_date]}
        representative = representative_by_date.get(record_date)
        row_values = [
            str(record_date),
            round(float(representative.avg_inner_level), 2) if representative and representative.avg_inner_level is not None else None,
            representative.daily_status if representative else None,
        ]
        for node_id in node_ids:
            item = node_map.get(node_id)
            row_values.extend([
                round(float(item.avg_inner_level), 2) if item and item.avg_inner_level is not None else None,
                item.daily_status if item else None,
            ])

        for col_idx, value in enumerate(row_values, start=1):
            cell = flow_sheet.cell(row=current_row, column=col_idx, value=value)
            cell.font = body_font
            cell.alignment = center
            cell.border = border
        current_row += 1

    # -----------------------------
    # 시트3: 노드별 상세 데이터
    # daily_summary 원본 데이터를 날짜별 묶음으로 확인하기 위한 시트
    # -----------------------------
    detail_sheet = workbook.create_sheet(title="노드별 상세 데이터")
    detail_sheet.sheet_view.showGridLines = False
    set_widths(detail_sheet, {"A": 16, "B": 12, "C": 18, "D": 18, "E": 45})
    detail_sheet.merge_cells("A1:E1")
    detail_sheet["A1"] = "노드별 상세 데이터"
    detail_sheet["A1"].font = title_font
    detail_sheet["A1"].alignment = center
    detail_sheet.row_dimensions[1].height = 30
    detail_sheet.append([])
    detail_sheet.append(["날짜", "노드 ID", "평균 내부 수위(cm)", "일일 상태", "검증 이미지 URL"])
    style_range(detail_sheet, "A3:E3", fill=header_fill, font=header_font, alignment=center)

    thick_side = Side(style="medium", color="404040")

    current_row = 4
    for record_date in sorted(daily_grouped.keys()):
        items = sorted(daily_grouped[record_date], key=lambda x: x.node_id)
        group_start = current_row

        for idx, item in enumerate(items):
            detail_sheet.cell(row=current_row, column=1, value=str(record_date) if idx == 0 else None)
            detail_sheet.cell(row=current_row, column=2, value=item.node_id)
            detail_sheet.cell(
                row=current_row,
                column=3,
                value=round(float(item.avg_inner_level), 2) if item.avg_inner_level is not None else None,
            )
            detail_sheet.cell(row=current_row, column=4, value=item.daily_status)
            detail_sheet.cell(row=current_row, column=5, value=item.verification_image_url)
            current_row += 1

        group_end = current_row - 1

        if group_end > group_start:
            detail_sheet.merge_cells(start_row=group_start, start_column=1, end_row=group_end, end_column=1)

        # 날짜 단위 묶음이 눈에 보이도록 첫 행/마지막 행에 굵은 테두리 적용
        for row_idx in range(group_start, group_end + 1):
            for col_idx in range(1, 6):
                cell = detail_sheet.cell(row=row_idx, column=col_idx)
                cell.font = body_font
                cell.alignment = left if col_idx == 5 else center
                cell.border = Border(
                    left=thin_side,
                    right=thin_side,
                    top=thick_side if row_idx == group_start else thin_side,
                    bottom=thick_side if row_idx == group_end else thin_side,
                )

        # 날짜별 묶음 사이 간격을 조금 더 주기 위해 행 높이 조정
        detail_sheet.row_dimensions[group_end].height = 22

    # -----------------------------
    # 시트3: 검증 상세
    # -----------------------------
    validation_sheet = workbook.create_sheet(title="검증 상세")
    validation_sheet.sheet_view.showGridLines = False
    set_widths(validation_sheet, {
        "A": 14, "B": 12, "C": 22, "D": 18, "E": 16,
        "F": 16, "G": 16, "H": 18, "I": 45, "J": 30
    })
    validation_sheet.merge_cells("A1:J1")
    validation_sheet["A1"] = "검증 상세"
    validation_sheet["A1"].font = title_font
    validation_sheet["A1"].alignment = center
    validation_sheet.row_dimensions[1].height = 30
    validation_sheet.append([])
    validation_sheet.append([
        "날짜",
        "노드 ID",
        "센서 기반 표면 판정",
        "사람 관찰값",
        "센서-관찰 검증",
        "센서 수위 구간",
        "AI 예측 구간",
        "AI-센서 구간 비교",
        "이미지 URL",
        "비고"
    ])
    
    style_range(validation_sheet, "A3:J3", fill=header_fill, font=header_font, alignment=center)

    if validation_rows:
        for row_data in validation_rows:
            if row_data.is_match is True:
                match_text = "일치"
            elif row_data.is_match is False:
                match_text = "불일치"
            else:
                match_text = "판별 불가"

            if row_data.ai_sensor_match is True:
                ai_sensor_text = "일치"
            elif row_data.ai_sensor_match is False:
                ai_sensor_text = "불일치"
            else:
                ai_sensor_text = "판별 불가"

            validation_sheet.append([
                str(row_data.record_date),
                row_data.node_id,
                row_data.sensor_predicted_status,
                row_data.observed_surface_status,
                match_text,
                get_sensor_ai_status_for_validation(row_data, db),
                row_data.ai_predicted_status,
                ai_sensor_text,
                row_data.image_url,
                row_data.note,
            ])
    else:
        validation_sheet.append(["검증 데이터 없음", "", "", "", "", "", "", "", "", ""])

    for row_cells in validation_sheet.iter_rows(min_row=4, max_row=validation_sheet.max_row, min_col=1, max_col=10):
        for cell in row_cells:
            cell.font = body_font
            cell.alignment = left if cell.column in (9, 10) else center
            cell.border = border

    for sheet in workbook.worksheets:
        sheet.freeze_panes = "A4"
        for row_cells in sheet.iter_rows():
            for cell in row_cells:
                if cell.value is not None and not cell.font:
                    cell.font = body_font

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

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
    우선순위
    1. Windows 로컬 테스트용 맑은 고딕
    2. 프로젝트 내부 backend/fonts/NanumGothic.ttf
    3. ReportLab 내장 CID 폰트 (배포 서버 fallback)
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

    # Render / Linux fallback
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        return "HYSMyeongJo-Medium"
    except Exception:
        raise RuntimeError(
            "사용 가능한 한글 폰트를 찾지 못했습니다. "
            "backend/fonts/NanumGothic.ttf 파일을 추가하거나 폰트 설정을 확인하세요."
        )
    

def get_month_range(report_month: str) -> tuple[date, date]:
    year, month = map(int, report_month.split("-"))

    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return start_date, end_date

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
        "representative_images": images[:3],
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

    nodes = (
        db.query(IotNode)
        .filter(IotNode.field_id == report.field_id)
        .order_by(IotNode.id.asc())
        .all()
    )

    daily_summaries = aggregate_daily_summaries(summaries)
    status_counts = summarize_status_counts(daily_summaries)
    weekly_groups = group_summaries_by_week(daily_summaries)
    month_avg = get_month_avg_inner_level(daily_summaries)

    weekly_dict = {week_no: week_summaries for week_no, week_summaries in weekly_groups}
    representative_images = validation["representative_images"]
    dominant_status = get_dominant_status(status_counts)

    font_name = register_korean_font()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left_x = 50
    right_x = width - 50
    max_text_width = int(right_x - left_x)
    y = height - 50

    def ensure_space(current_y: int, needed: int = 90):
        nonlocal pdf
        if current_y < needed:
            pdf.showPage()
            pdf.setFont(font_name, 11)
            return height - 50
        return current_y

    def draw_section_title(title: str, current_y: int):
        current_y = ensure_space(current_y, needed=100)
        pdf.setFont(font_name, 13)
        pdf.drawString(left_x, current_y, title)
        current_y -= 24
        pdf.setFont(font_name, 11)
        return current_y

    def draw_lines(lines: list[str], current_y: int):
        pdf.setFont(font_name, 11)
        for line in lines:
            current_y = ensure_space(current_y)
            if line == "":
                current_y -= 8
            else:
                current_y = draw_wrapped_text(
                    pdf, line, left_x, current_y, max_text_width, font_name=font_name
                )
        return current_y

    pdf.setTitle(f"mrv_report_{report.id}")

    # 제목
    pdf.setFont(font_name, 16)
    pdf.drawString(left_x, y, "AWD Water Management MRV Report")
    y -= 32

    pdf.setFont(font_name, 11)
    y = draw_wrapped_text(
        pdf,
        f"이 보고서는 {field.field_name}의 {report.report_month} 기간 동안 수행된 AWD 물관리 이력을 정리한 MRV 보고서입니다. "
        f"이 시스템은 IoT 센서를 이용하여 논의 수위 데이터를 자동으로 수집하고, 이를 기반으로 일 단위 상태를 분석하여 물관리 수행 여부를 기록하도록 설계되었습니다.",
        left_x, y, max_text_width, font_name=font_name
    )
    y -= 12

    # 1. 시스템 개요
    y = draw_section_title("1. 시스템 개요", y)
    y = draw_lines([
        "이 시스템은 논 내부 수위를 기준으로 상태를 다음과 같이 구분합니다.",
        "",
        "OVERFLOODED: 과다 담수 상태",
        "FLOODED: 적정 담수 상태",
        "DRYING: 건조 진행 상태",
        "DRY: 재관개 필요 상태",
        "",
        "일일 상태는 하루 동안 수집된 센서 데이터를 평균 수위 기준으로 분석하여 각 날짜별 대표 상태 하나로 정의합니다.",
    ], y)
    y -= 10

    # 2. 분석 대상 및 기간
    y = draw_section_title("2. 분석 대상 및 기간", y)
    y = draw_lines([
        f"대상 논: {field.field_name}",
        f"분석 기간: {report.report_month}",
        f"사용 노드 수: {len(nodes)}",
        f"보고서 생성일: {report.created_at.date() if report.created_at else '-'}",
    ], y)
    y -= 10

    # 3. 월간 운영 요약
    y = draw_section_title("3. 월간 운영 요약", y)
    y = draw_lines([
        "해당 기간 동안의 일일 상태를 집계한 결과는 다음과 같습니다.",
        "",
        f"OVERFLOODED: {status_counts['OVERFLOODED']}일",
        f"FLOODED: {status_counts['FLOODED']}일",
        f"DRYING: {status_counts['DRYING']}일",
        f"DRY: {status_counts['DRY']}일",
        "",
        f"분석 결과, 해당 기간 동안 논은 전반적으로 {dominant_status} 상태를 중심으로 변화하고 있습니다.",
        "이는 일일 평균 수위 기준으로 산정된 대표 상태를 바탕으로 해석한 결과입니다.",
        "",
        "AWD 수행은 다음 기준으로 정의합니다.",
        "DRY 상태 이후 FLOODED 상태로 전환되는 경우를 AWD 1회로 정의합니다.",
        "",
        f"해당 기간 동안 AWD 수행 횟수는 {report.total_awd_cycles}회로 집계됩니다.",
    ], y)
    y -= 10

    # 4. 주차별 수위 변화 분석
    y = draw_section_title("4. 주차별 수위 변화 분석", y)

    for week_no in range(1, 5):
        y = ensure_space(y, needed=150)
        week_lines = make_weekly_summary_text(week_no, weekly_dict.get(week_no, []))

        for line in week_lines:
            if line.startswith("■"):
                pdf.setFont(font_name, 12)
                pdf.drawString(left_x, y, line)
                y -= 20
                pdf.setFont(font_name, 11)
            elif line == "":
                y -= 8
            else:
                y = draw_wrapped_text(
                    pdf, line, left_x, y, max_text_width, font_name=font_name
                )
        y -= 12

    # 5. 수위 변화 분석
    y = draw_section_title("5. 수위 변화 분석", y)

    if month_avg is not None:
        y = draw_lines([
            f"분석 기간 동안 평균 내부 수위는 {month_avg:.2f}cm로 나타납니다.",
            "",
            f"이는 일일 평균 수위 기준으로 산정된 값이며, 주요 상태는 {dominant_status}로 해석됩니다.",
            "전체적인 수위 변화는 주차별 수위 변화 분석 결과를 함께 고려하여 판단합니다.",
        ], y)
    else:
        y = draw_lines([
            "분석 기간 동안 평균 내부 수위 데이터가 없어 월간 수위 변화 분석이 제한됩니다."
        ], y)
    y -= 10

    # 6. 현장 검증 결과
    y = draw_section_title("6. 현장 검증 결과", y)

    if validation["validation_sample_count"] > 0:
        y = draw_lines([
            "센서 기반 상태 판정의 정확성을 확인하기 위해, 현장 촬영 이미지와 비교 검증을 수행하였습니다.",
            "",
            "드론 또는 현장 촬영 이미지는 표면에 물이 존재하는지 여부를 기준으로 분석하였으며,",
            "이를 통해 논의 표면 상태를 WATER 또는 NO_WATER 수준으로 구분하였습니다.",
            "",
            "FLOODED 및 OVERFLOODED 상태는 표면 담수 여부를 통해 비교할 수 있으나,",
            "DRYING과 DRY 상태의 세부 구분은 사진만으로 판단하기 어렵습니다.",
            "따라서 DRYING과 DRY 상태는 센서 수위 데이터를 기준으로 해석하고,",
            "사진 검증은 표면 담수 여부를 확인하는 보조 검증 자료로 활용하였습니다.",
            "",
            f"검증 방법: {validation['validation_method']}",
            f"샘플 수: {validation['validation_sample_count']}",
            f"일치 수: {validation['validation_match_count']}",
            f"정확도: {validation['validation_accuracy']}%",
            f"비고: {validation['validation_note']}",
            "",
            f"검증 결과, 총 {validation['validation_sample_count']}건 중 {validation['validation_match_count']}건이 일치하는 것으로 확인됩니다.",
            "이를 통해 센서 기반 상태 판정 결과와 현장 관찰 결과를 비교할 수 있습니다.",
            "일부 불일치 사례는 센서 수위 데이터와 실제 현장 상태 간의 시간적 차이 또는 촬영 시점 차이에 의해 발생했을 가능성이 있습니다.",
            "따라서 검증 결과는 센서 기반 상태 판정의 신뢰성을 확인하는 동시에, 향후 상태 판정 기준을 보완하기 위한 근거로 활용할 수 있습니다.",
        ], y)
    else:
        y = draw_lines([
            "해당 기간에는 등록된 현장 검증 데이터가 없어 검증 결과 분석이 제한됩니다.",
            "검증 사진과 실제 관찰 상태가 등록되면 샘플 수, 일치 수, 정확도가 자동으로 집계됩니다.",
        ], y)
    y -= 10

    # 7. 대표 검증 이미지
    y = draw_section_title("7. 대표 검증 이미지", y)

    if representative_images:
        y = draw_lines([
            "해당 기간의 대표 검증 이미지는 다음과 같습니다.",
            "",
        ], y)

        for idx, img_url in enumerate(representative_images, start=1):
            y = ensure_space(y)
            y = draw_wrapped_text(
                pdf, f"이미지 {idx}: {img_url}", left_x, y, max_text_width, font_name=font_name
            )
    else:
        y = draw_lines([
            "해당 기간에 등록된 대표 검증 이미지가 없습니다."
        ], y)
    y -= 10

    # 8. 탄소 감축 추정 결과
    y = draw_section_title("8. 탄소 감축 추정 결과", y)

    y = draw_lines([
        "탄소 감축량은 AWD 수행 횟수를 기반으로 산출합니다.",
        "",
        "탄소 감축량 = AWD 수행 횟수 × 15.25 (kgCO2-eq)",
        "",
        f"해당 기간 동안 AWD 수행 횟수는 {report.total_awd_cycles}회이며, 탄소 감축 추정량은 {report.carbon_reduction} kgCO2-eq로 계산됩니다.",
        "이 값은 실제 측정값이 아닌, AWD 수행 이력 기반 추정값입니다.",
    ], y)
    y -= 10

    # 9. 종합 결론
    y = draw_section_title("9. 종합 결론", y)

    if report.total_awd_cycles == 0:
        conclusion_lines = [
            f"해당 기간 동안 논은 주로 {dominant_status} 상태를 중심으로 변화하였으며, AWD 수행은 발생하지 않았습니다.",
            "이는 분석 기간 내 일일 대표 상태 기준으로 DRY 이후 FLOODED 전환이 관측되지 않았기 때문입니다.",
            "향후 AWD 수행을 위해서는 추가적인 건조 및 재관개 과정이 필요합니다.",
        ]
    else:
        conclusion_lines = [
            f"해당 기간 동안 AWD 수행은 {report.total_awd_cycles}회 관측되었습니다.",
            "이는 일일 대표 상태 기준으로 DRY 이후 FLOODED 전환이 확인된 결과입니다.",
            "해당 데이터는 AWD 물관리 수행 이력을 정량적으로 기록하는 근거로 활용할 수 있습니다.",
        ]

    conclusion_lines += [
        "",
        "이 시스템은 IoT 센서를 활용하여 수위 데이터를 자동으로 수집하고, 이를 기반으로 일일 상태 분석 및 MRV 보고서 생성을 수행할 수 있습니다.",
        "이를 통해 AWD 물관리의 디지털화 및 MRV 자동화 가능성을 확인할 수 있습니다.",
    ]

    y = draw_lines(conclusion_lines, y)

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
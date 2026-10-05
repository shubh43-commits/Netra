"""
Celery Background Tasks for Netra Data Hygiene and Analytics.
Includes:
- purge_expired_feedback_reports: Enforces 90-day privacy retention by removing old bug frames
- aggregate_daily_usage_metrics: Pre-aggregates daily metrics and purges raw events older than 30 days
"""
import logging
from datetime import timedelta
from django.utils import timezone
from celery import shared_task

from apps.feedback.models import DetectionReport
from .models import UsageEvent, DailyAnalyticsSummary, SafetyIncident

logger = logging.getLogger('netra.analytics.tasks')


@shared_task(name='apps.analytics.tasks.purge_expired_feedback_reports')
def purge_expired_feedback_reports() -> int:
    """
    Enforces privacy policy by deleting all DetectionReport rows and their
    associated stored camera image files that are older than 90 days.
    """
    cutoff = timezone.now() - timedelta(days=90)
    expired_reports = DetectionReport.objects.filter(created_at__lt=cutoff)
    count = expired_reports.count()

    if count == 0:
        logger.info("Feedback retention check: 0 expired reports found.")
        return 0

    deleted_count = 0
    for report in expired_reports:
        try:
            # Delete physical image file from storage
            if report.image:
                report.image.delete(save=False)
            report.delete()
            deleted_count += 1
        except Exception as e:
            logger.error(f"Error purging report {report.id}: {str(e)}")

    logger.info(f"Feedback retention purge complete: Deleted {deleted_count} reports older than 90 days.")
    return deleted_count


@shared_task(name='apps.analytics.tasks.aggregate_daily_usage_metrics')
def aggregate_daily_usage_metrics(target_date_str: str = None) -> dict:
    """
    Aggregates daily navigation usage metrics into DailyAnalyticsSummary
    and cleans up raw telemetry events older than 30 days.
    """
    if target_date_str:
        target_date = timezone.datetime.fromisoformat(target_date_str).date()
    else:
        # Defaults to yesterday
        target_date = (timezone.now() - timedelta(days=1)).date()

    start_dt = timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.min.time()))
    end_dt = timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.max.time()))

    day_events = UsageEvent.objects.filter(timestamp__range=(start_dt, end_dt))

    total_sessions = day_events.filter(event_type='session_start').count()
    total_hazards = day_events.filter(event_type='hazard_detected').count()
    total_incidents = SafetyIncident.objects.filter(created_at__range=(start_dt, end_dt)).count()
    unique_devices = day_events.values('device_id').distinct().count()

    # Calculate average FPS if recorded
    fps_sum = 0.0
    fps_count = 0
    for ev in day_events.filter(event_type='session_end'):
        fps_val = ev.event_data.get('avg_fps') or ev.event_data.get('fps')
        if fps_val is not None:
            try:
                fps_sum += float(fps_val)
                fps_count += 1
            except (ValueError, TypeError):
                pass

    avg_fps = round(fps_sum / max(1, fps_count), 1) if fps_count > 0 else 0.0

    summary, created = DailyAnalyticsSummary.objects.update_or_create(
        date=target_date,
        defaults={
            'total_sessions': total_sessions,
            'total_hazards_detected': total_hazards,
            'total_incidents': total_incidents,
            'unique_devices': unique_devices,
            'average_fps': avg_fps,
        }
    )

    # Privacy cleanup: Purge raw telemetry events older than 30 days
    raw_event_cutoff = timezone.now() - timedelta(days=30)
    purged_events, _ = UsageEvent.objects.filter(timestamp__lt=raw_event_cutoff).delete()

    logger.info(
        f"Aggregated metrics for {target_date}: {total_sessions} sessions, {total_hazards} hazards, "
        f"{total_incidents} incidents. Purged {purged_events} raw events older than 30 days."
    )

    return {
        'date': str(target_date),
        'total_sessions': total_sessions,
        'total_hazards': total_hazards,
        'total_incidents': total_incidents,
        'unique_devices': unique_devices,
        'purged_raw_events': purged_events
    }

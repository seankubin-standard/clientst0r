"""
field_ops web views — Phase 8.3 Timeclock dashboard + payroll export
                     + Phase 8.5 per-tech location history + org settings.
"""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from audit.models import AuditLog

from .models import OrganizationFieldOpsSettings, TechnicianLocation, TimeclockEntry


def _staff_only(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _audit(user, event: str, extra: dict | None = None):
    try:
        AuditLog.objects.create(
            user=user,
            username=getattr(user, 'username', '') or '',
            action='read' if event.endswith('_view') else 'api_call',
            object_type='FieldOps',
            extra_data={'event': event, **(extra or {})},
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Sub-phase 8.3 — Timeclock dashboard (v3.17.413)
# ---------------------------------------------------------------------------

@login_required
def timeclock_dashboard(request):
    """
    `/timeclock/` — staff view of who's currently clocked in.

    Long-shift / missing-clock-out exception flags. Pay-period (last 7 days)
    totals per tech.
    """
    if not _staff_only(request.user):
        return HttpResponseForbidden('Staff only.')

    now = timezone.now()
    open_entries = (
        TimeclockEntry.objects
        .filter(clocked_out_at__isnull=True)
        .select_related('tech', 'organization', 'ticket')
        .order_by('clocked_in_at')
    )
    rows = []
    for e in open_entries:
        duration_min = e.duration_minutes
        hours = duration_min / 60.0
        long_shift = hours > 12
        # Missing clock-out: still open AND > 8h past clock-in (heuristic
        # for techs who forgot to clock out).
        missing_clockout = hours > 8
        rows.append({
            'entry': e,
            'duration_minutes': duration_min,
            'duration_hours': round(hours, 2),
            'long_shift': long_shift,
            'missing_clockout': missing_clockout,
        })

    # Pay-period totals (last 7 days, closed entries).
    period_start = now - timedelta(days=7)
    period_entries = (
        TimeclockEntry.objects
        .filter(clocked_out_at__isnull=False, clocked_in_at__gte=period_start)
        .select_related('tech')
    )
    totals_by_tech = {}
    for e in period_entries:
        key = e.tech_id
        totals_by_tech.setdefault(key, {'tech': e.tech, 'minutes': 0})
        totals_by_tech[key]['minutes'] += e.duration_minutes
    period_totals = sorted(
        ({'tech': v['tech'], 'hours': round(v['minutes'] / 60.0, 2)}
         for v in totals_by_tech.values()),
        key=lambda d: d['tech'].username,
    )

    return render(request, 'field_ops/timeclock_dashboard.html', {
        'rows': rows,
        'period_totals': period_totals,
        'period_start': period_start,
    })


@login_required
def timeclock_payroll_export(request):
    """
    `/timeclock/payroll-export.csv` — per-pay-period CSV. Columns
    `tech, week_start, hours, overtime_hours, org`. Compatible with
    QuickBooks Time / Gusto manual import.
    """
    if not _staff_only(request.user):
        return HttpResponseForbidden('Staff only.')

    now = timezone.now()
    weeks_back = 4
    start = now - timedelta(days=weeks_back * 7)

    qs = (
        TimeclockEntry.objects
        .filter(clocked_out_at__isnull=False, clocked_in_at__gte=start)
        .select_related('tech', 'organization')
    )

    # Bucket by (tech, week_start, org)
    buckets = {}
    for e in qs:
        ws = e.clocked_in_at.date() - timedelta(days=e.clocked_in_at.weekday())
        org_name = e.organization.name if e.organization_id else ''
        key = (e.tech.username, ws.isoformat(), org_name)
        buckets.setdefault(key, 0)
        buckets[key] += e.duration_minutes

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payroll_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['tech', 'week_start', 'hours', 'overtime_hours', 'org'])
    for (tech, ws, org_name), minutes in sorted(buckets.items()):
        hours = round(minutes / 60.0, 2)
        overtime = round(max(0, hours - 40), 2)
        writer.writerow([tech, ws, hours, overtime, org_name])

    _audit(request.user, 'payroll_export', {'weeks_back': weeks_back})
    return response


# ---------------------------------------------------------------------------
# Sub-phase 8.5 — Per-tech location history (v3.17.415)
# ---------------------------------------------------------------------------

@login_required
def my_location_history(request):
    """`/field-ops/my-location-history/` — paginated list of the caller's
    own GPS pings. Per-row delete + bulk delete-all."""
    qs = TechnicianLocation.objects.filter(tech=request.user).order_by('-timestamp')
    try:
        page = max(int(request.GET.get('page', 1)), 1)
    except ValueError:
        page = 1
    page_size = 50
    start = (page - 1) * page_size
    total = qs.count()
    rows = list(qs[start:start + page_size])
    has_next = total > start + page_size

    _audit(request.user, 'my_location_history_view', {'page': page, 'total': total})

    return render(request, 'field_ops/my_location_history.html', {
        'rows': rows,
        'page': page,
        'page_size': page_size,
        'total': total,
        'has_next': has_next,
        'has_prev': page > 1,
    })


@login_required
@require_http_methods(['POST'])
def my_location_delete(request, pk: int):
    """Per-row delete of the caller's own location row."""
    loc = get_object_or_404(TechnicianLocation, pk=pk, tech=request.user)
    loc.delete()
    _audit(request.user, 'my_location_history_delete', {'row_id': pk})
    messages.success(request, 'Deleted location row.')
    return redirect('field_ops:my_location_history')


@login_required
@require_http_methods(['POST'])
def my_location_delete_all(request):
    """Bulk delete every TechnicianLocation row owned by the caller."""
    confirm = request.POST.get('confirm') or ''
    if confirm != 'DELETE':
        messages.error(request, "Type DELETE to confirm.")
        return redirect('field_ops:my_location_history')
    deleted, _ = TechnicianLocation.objects.filter(tech=request.user).delete()
    _audit(request.user, 'my_location_history_delete_all', {'deleted': deleted})
    messages.success(request, f'Deleted {deleted} location row(s).')
    return redirect('field_ops:my_location_history')

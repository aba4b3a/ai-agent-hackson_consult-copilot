"""Rule-based discovery signal detection over in-memory observations (§11).

Aggregates observation entity mentions into ISO-week buckets and derives
discovery signals: weekly increases, rolling-average increases (when enough
history exists), and newly appearing entities. Thresholds follow the structure
of design §14.3; the values are tuned low so hackathon demo data actually
fires. Workspace-level threshold configuration (R11.9) is a follow-up.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from app.schemas.discovery import DiscoverySignal, Observation, Workspace

# Demo-tuned thresholds (design §14.3 structure).
WEEKLY_INCREASE_RATE = 0.5
MIN_CURRENT_COUNT = 2
ROLLING_MIN_WEEKS = 3
NEW_ENTITY_MIN_COUNT = 1


def detect_signals(
    observations: list[Observation],
    workspace: Workspace,
    now: datetime | None = None,
) -> list[DiscoverySignal]:
    now = now or datetime.now(UTC)
    current_week = now.isocalendar()[:2]

    # entity -> (iso_year, iso_week) -> mention count
    weekly: dict[str, dict[tuple[int, int], int]] = defaultdict(lambda: defaultdict(int))
    for obs in observations:
        week = _week_of(obs.observed_at)
        if week is None:
            continue
        for entity in obs.related_entities:
            weekly[entity][week] += 1

    known_terms = _known_terms(workspace)
    signals: list[DiscoverySignal] = []
    counter = 0

    for entity, buckets in sorted(weekly.items()):
        current = buckets.get(current_week, 0)
        if current == 0:
            continue
        past_weeks = {week: count for week, count in buckets.items() if week != current_week}
        previous = past_weeks.get(_previous_week(now), 0)

        counter += 1
        signal_id = f"sig_auto_{counter:03d}"

        # new_entity: first appearance of a term outside the initial company
        # context (§11.4).
        if not past_weeks and entity not in known_terms and current >= NEW_ENTITY_MIN_COUNT:
            signals.append(
                _signal(
                    signal_id,
                    workspace.workspace_id,
                    "new_entity",
                    f"new_mention_{entity}",
                    entity,
                    current=current,
                    baseline=0,
                )
            )
            continue

        # weekly_increase: current week vs previous week (§11.2).
        if previous > 0:
            rate = (current - previous) / previous
            if rate >= WEEKLY_INCREASE_RATE and current >= MIN_CURRENT_COUNT:
                signals.append(
                    _signal(
                        signal_id,
                        workspace.workspace_id,
                        "weekly_increase",
                        f"weekly_mentions_{entity}",
                        entity,
                        current=current,
                        baseline=previous,
                    )
                )
                continue

        # rolling_average_increase: current vs average of past weeks when
        # enough history exists (simplified §11.3).
        if len(past_weeks) >= ROLLING_MIN_WEEKS:
            average = sum(past_weeks.values()) / len(past_weeks)
            if average > 0:
                rate = (current - average) / average
                if rate >= WEEKLY_INCREASE_RATE and current >= MIN_CURRENT_COUNT:
                    signals.append(
                        _signal(
                            signal_id,
                            workspace.workspace_id,
                            "rolling_average_increase",
                            f"rolling_mentions_{entity}",
                            entity,
                            current=current,
                            baseline=round(average, 2),
                        )
                    )

    return signals


def _week_of(observed_at: str) -> tuple[int, int] | None:
    if not observed_at:
        return None
    try:
        moment = datetime.fromisoformat(observed_at)
    except ValueError:
        return None
    return moment.isocalendar()[:2]


def _previous_week(now: datetime) -> tuple[int, int]:
    from datetime import timedelta

    return (now - timedelta(weeks=1)).isocalendar()[:2]


def _known_terms(workspace: Workspace) -> set[str]:
    return {
        *workspace.products,
        *workspace.customer_segments,
        *workspace.competitors,
        *workspace.known_issues,
        *workspace.kpis,
        *workspace.observation_topics,
    }


def _signal(
    signal_id: str,
    workspace_id: str,
    signal_type: str,
    metric_name: str,
    entity: str,
    current: float,
    baseline: float,
) -> DiscoverySignal:
    rate = (current - baseline) / baseline if baseline > 0 else 1.0
    if rate > 1.0:
        severity = "danger"
    elif rate > 0.5:
        severity = "warning"
    else:
        severity = "info"
    return DiscoverySignal(
        signal_id=signal_id,
        workspace_id=workspace_id,
        signal_type=signal_type,
        metric_name=metric_name,
        current_value=current,
        baseline_value=baseline,
        change_rate=round(rate, 2),
        related_entities=[entity],
        evidence_count=int(current),
        severity=severity,
    )

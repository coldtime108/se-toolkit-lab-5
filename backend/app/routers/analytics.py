"""Router for analytics endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlmodel import select, func
from sqlalchemy import case
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.auth import verify_api_key
from app.models.item import ItemRecord
from app.models.learner import Learner
from app.models.interaction import InteractionLog

router = APIRouter()

@router.get("/scores")
async def get_scores(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    result = await session.exec(select(ItemRecord).where(ItemRecord.title.ilike(search_pattern)))
    lab_item = result.first()
    if not lab_item:
        return []

    # Get tasks as full objects, not just IDs
    tasks_result = await session.exec(select(ItemRecord).where(ItemRecord.parent_id == lab_item.id))
    tasks = tasks_result.all()
    task_ids = [t.id for t in tasks]  # now t is an object with id
    if not task_ids:
        return [{"bucket": "0-25", "count": 0},
                {"bucket": "26-50", "count": 0},
                {"bucket": "51-75", "count": 0},
                {"bucket": "76-100", "count": 0}]

    buckets = [
        (0, 25, "0-25"),
        (26, 50, "26-50"),
        (51, 75, "51-75"),
        (76, 100, "76-100"),
    ]

    count_exprs = []
    bucket_labels = []
    for low, high, label in buckets:
        count_exprs.append(
            func.sum(case((InteractionLog.score.between(low, high), 1), else_=0)).label(label)
        )
        bucket_labels.append(label)

    row_result = await session.exec(
        select(*count_exprs).where(
            InteractionLog.item_id.in_(task_ids),
            InteractionLog.score.is_not(None)
        )
    )
    row = row_result.first()

    result = []
    for label in bucket_labels:
        count = getattr(row, label) if row else 0
        result.append({"bucket": label, "count": count or 0})

    return result

@router.get("/pass-rates")
async def get_pass_rates(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    lab_result = await session.exec(select(ItemRecord).where(ItemRecord.title.ilike(search_pattern)))
    lab_item = lab_result.first()
    if not lab_item:
        return []

    tasks_result = await session.exec(select(ItemRecord).where(ItemRecord.parent_id == lab_item.id))
    tasks = tasks_result.all()
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []

    results = await session.exec(
        select(
            ItemRecord.title.label("task"),
            func.round(func.avg(InteractionLog.score), 1).label("avg_score"),
            func.count(InteractionLog.id).label("attempts")
        )
        .where(InteractionLog.item_id.in_(task_ids))
        .join(ItemRecord, ItemRecord.id == InteractionLog.item_id)
        .group_by(ItemRecord.id, ItemRecord.title)
        .order_by(ItemRecord.title)
    )
    items = results.all()
    return [{"task": r.task, "avg_score": r.avg_score, "attempts": r.attempts} for r in items]

@router.get("/timeline")
async def get_timeline(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    lab_result = await session.exec(select(ItemRecord).where(ItemRecord.title.ilike(search_pattern)))
    lab_item = lab_result.first()
    if not lab_item:
        return []

    tasks_result = await session.exec(select(ItemRecord).where(ItemRecord.parent_id == lab_item.id))
    tasks = tasks_result.all()
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []

    results = await session.exec(
        select(
            func.date(InteractionLog.created_at).label("date"),
            func.count().label("submissions")
        )
        .where(InteractionLog.item_id.in_(task_ids))
        .group_by(func.date(InteractionLog.created_at))
        .order_by("date")
    )
    items = results.all()
    return [{"date": str(r.date), "submissions": r.submissions} for r in items]

@router.get("/groups")
async def get_groups(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    lab_result = await session.exec(select(ItemRecord).where(ItemRecord.title.ilike(search_pattern)))
    lab_item = lab_result.first()
    if not lab_item:
        return []

    tasks_result = await session.exec(select(ItemRecord).where(ItemRecord.parent_id == lab_item.id))
    tasks = tasks_result.all()
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []

    results = await session.exec(
        select(
            Learner.student_group.label("group"),
            func.round(func.avg(InteractionLog.score), 1).label("avg_score"),
            func.count(func.distinct(InteractionLog.learner_id)).label("students")
        )
        .where(InteractionLog.item_id.in_(task_ids))
        .join(Learner, Learner.id == InteractionLog.learner_id)
        .group_by(Learner.student_group)
        .order_by(Learner.student_group)
    )
    items = results.all()
    return [{"group": r.group, "avg_score": r.avg_score, "students": r.students} for r in items]
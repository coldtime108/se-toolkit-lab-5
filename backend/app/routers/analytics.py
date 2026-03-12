"""Router for analytics endpoints.
populated by the ETL pipeline. All endpoints require a ).
"""
from app.auth import verify_api_key
from sqlmodel import select
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import func
from sqlalchemy import case
from app.database import get_session
from app.models.item import Item
from app.models.learner import Learner
from app.models.interaction import Interaction
router = APIRouter()


@router.get("/scores")
async def get_scores(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    """Score distribution histogram for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item by matching title (e.g. "lab-04" → title contains "Lab 04")
    - Find all tasks that belong to this lab (parent_id = lab.id)
    - Query interactions for these items that have a score
    - Group scores into buckets: "0-25", "26-50", "51-75", "76-100"
      using CASE WHEN expressions
    - Return a JSON array:
      [{"bucket": "0-25", "count": 12}, {"bucket": "26-50", "count": 8}, ...]
    - Always return all four buckets, even if count is 0
    """
    # Transform lab parameter: "lab-04" -> "%Lab 04%"
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    
    lab_item = await session.exec(select(Item).where(Item.title.ilike(search_pattern))).first()
    if not lab_item:
        return []
    
    # Get all task ids under this lab
    tasks = await session.exec(select(Item.id).where(Item.parent_id == lab_item.id)).all()
    task_ids = [t.id for t in tasks]
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
            func.sum(case((Interaction.score.between(low, high), 1), else_=0)).label(label)
        )
        bucket_labels.append(label)
    
    row = await session.exec(
        select(*count_exprs).where(
            Interaction.item_id.in_(task_ids),
            Interaction.score.is_not(None)
        )
    ).first()
    
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
    """Per-task pass rates for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item and its child task items
    - For each task, compute:
      - avg_score: average of interaction scores (round to 1 decimal)
      - attempts: total number of interactions
    - Return a JSON array:
      [{"task": "Repository Setup", "avg_score": 92.3, "attempts": 150}, ...]
    - Order by task title
    """
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    lab_item = await session.exec(select(Item).where(Item.title.ilike(search_pattern))).first()
    if not lab_item:
        return []
    
    tasks = await session.exec(select(Item).where(Item.parent_id == lab_item.id)).all()
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []
    
    results = await session.exec(
        select(
            Item.title.label("task"),
            func.round(func.avg(Interaction.score), 1).label("avg_score"),
            func.count(Interaction.id).label("attempts")
        )
        .where(Interaction.item_id.in_(task_ids))
        .join(Item, Item.id == Interaction.item_id)
        .group_by(Item.id, Item.title)
        .order_by(Item.title)
    ).all()
    
    return [{"task": r.task, "avg_score": r.avg_score, "attempts": r.attempts} for r in results]


@router.get("/timeline")
async def get_timeline(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    """Submissions per day for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item and its child task items
    - Group interactions by date (use func.date(created_at))
    - Count the number of submissions per day
    - Return a JSON array:
      [{"date": "2026-02-28", "submissions": 45}, ...]
    - Order by date ascending
    """
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    lab_item = await session.exec(select(Item).where(Item.title.ilike(search_pattern))).first()
    if not lab_item:
        return []
    
    tasks = await session.exec(select(Item.id).where(Item.parent_id == lab_item.id)).all()
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []
    
    results = await session.exec(
        select(
            func.date(Interaction.created_at).label("date"),
            func.count().label("submissions")
        )
        .where(Interaction.item_id.in_(task_ids))
        .group_by(func.date(Interaction.created_at))
        .order_by("date")
    ).all()
    
    return [{"date": str(r.date), "submissions": r.submissions} for r in results]


@router.get("/groups")
async def get_groups(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    """Per-group performance for a given lab.

    TODO: Implement this endpoint.
    - Find the lab item and its child task items
    - Join interactions with learners to get student_group
    - For each group, compute:
      - avg_score: average score (round to 1 decimal)
      - students: count of distinct learners
    - Return a JSON array:
      [{"group": "B23-CS-01", "avg_score": 78.5, "students": 25}, ...]
    - Order by group name
    """
    search_pattern = f"%{lab.replace('-', ' ').title()}%"
    lab_item = await session.exec(select(Item).where(Item.title.ilike(search_pattern))).first()
    if not lab_item:
        return []
    
    tasks = await session.exec(select(Item.id).where(Item.parent_id == lab_item.id)).all()
    task_ids = [t.id for t in tasks]
    if not task_ids:
        return []
    
    results = await session.exec(
        select(
            Learner.student_group.label("group"),
            func.round(func.avg(Interaction.score), 1).label("avg_score"),
            func.count(func.distinct(Interaction.learner_id)).label("students")
        )
        .where(Interaction.item_id.in_(task_ids))
        .join(Learner, Learner.id == Interaction.learner_id)
        .group_by(Learner.student_group)
        .order_by(Learner.student_group)
    ).all()
    
    return [{"group": r.group, "avg_score": r.avg_score, "students": r.students} for r in results]

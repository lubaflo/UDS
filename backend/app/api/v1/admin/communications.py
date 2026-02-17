from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models import CommunicationCampaign
from app.schemas.communications import (
    AppointmentCreateRequest,
    AppointmentOut,
    CommunicationCampaignCreateRequest,
    CommunicationCampaignListResponse,
    CommunicationCampaignOut,
    CommunicationLaunchResponse,
    CommunicationStatsOut,
    CommunicationStepOut,
    CommunicationTrackRequest,
    ReminderRulesResponse,
    ReminderRulesUpdateRequest,
    ReminderRuleOut,
    ReminderRunResponse,
    WorkflowCreateRequest,
    WorkflowStateResponse,
    WorkflowStep1AudienceRequest,
    WorkflowStep2ContentRequest,
    WorkflowStep3ScheduleRequest,
    WorkflowStep4ConfirmationResponse,
    WorkflowStep5StatsResponse,
)
from app.services.communications_service import (
    campaign_stats,
    create_appointment,
    create_campaign,
    create_workflow_campaign,
    get_campaign_by_id,
    get_campaign_steps,
    get_reminder_rules,
    launch_campaign,
    list_campaigns,
    run_reminders,
    set_reminder_rules,
    track_recipient_event,
    workflow_estimated_recipients,
    workflow_state,
    workflow_step1_audience,
    workflow_step2_content,
    workflow_step3_schedule,
)

router = APIRouter(prefix="/admin/communications", tags=["admin.communications"])


@router.get("", response_model=CommunicationCampaignListResponse)
def get_communications(
    tab: str = Query(default="active", pattern="^(active|archive|all)$"),
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CommunicationCampaignListResponse:
    status = None if tab == "all" else tab
    items, active_count, archived_count = list_campaigns(db, salon_id=ctx.salon_id, status=status)
    out: list[CommunicationCampaignOut] = []
    for item in items:
        steps = get_campaign_steps(db, item.id)
        out.append(
            CommunicationCampaignOut(
                id=item.id,
                title=item.title,
                purpose=item.purpose,
                audience_type=item.audience_type,
                status=item.status,
                schedule_type=item.schedule_type,
                schedule_at=item.schedule_at,
                created_at=item.created_at,
                steps=[
                    CommunicationStepOut(
                        id=s.id,
                        step_order=s.step_order,
                        channel=s.channel,
                        subject=s.subject,
                        body=s.body,
                        delay_minutes=s.delay_minutes,
                    )
                    for s in steps
                ],
            )
        )
    return CommunicationCampaignListResponse(items=out, active_count=active_count, archived_count=archived_count)


@router.post("", response_model=CommunicationCampaignOut)
def post_create_communication(
    req: CommunicationCampaignCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CommunicationCampaignOut:
    campaign = create_campaign(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        title=req.title,
        purpose=req.purpose,
        audience_type=req.audience_type,
        schedule_type=req.schedule_type,
        schedule_at=req.schedule_at,
        steps=req.steps,
    )
    steps = get_campaign_steps(db, campaign.id)
    return CommunicationCampaignOut(
        id=campaign.id,
        title=campaign.title,
        purpose=campaign.purpose,
        audience_type=campaign.audience_type,
        status=campaign.status,
        schedule_type=campaign.schedule_type,
        schedule_at=campaign.schedule_at,
        created_at=campaign.created_at,
        steps=[
            CommunicationStepOut(
                id=s.id,
                step_order=s.step_order,
                channel=s.channel,
                subject=s.subject,
                body=s.body,
                delay_minutes=s.delay_minutes,
            )
            for s in steps
        ],
    )


# Wizard 1..5
@router.post("/workflows", response_model=WorkflowStateResponse)
def post_workflow_create(
    req: WorkflowCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> WorkflowStateResponse:
    row = create_workflow_campaign(db, salon_id=ctx.salon_id, actor_user_id=ctx.user_id, title=req.title)
    current_step, can_confirm, has_audience, has_content, has_schedule = workflow_state(
        db, salon_id=ctx.salon_id, campaign_id=row.id
    )
    return WorkflowStateResponse(
        campaign_id=row.id,
        current_step=current_step,
        can_confirm=can_confirm,
        has_audience=has_audience,
        has_content=has_content,
        has_schedule=has_schedule,
    )


@router.put("/workflows/{campaign_id}/step-1-audience", response_model=WorkflowStateResponse)
def put_workflow_step1(
    campaign_id: int,
    req: WorkflowStep1AudienceRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> WorkflowStateResponse:
    workflow_step1_audience(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        campaign_id=campaign_id,
        purpose=req.purpose,
        audience_type=req.audience_type,
    )
    current_step, can_confirm, has_audience, has_content, has_schedule = workflow_state(
        db, salon_id=ctx.salon_id, campaign_id=campaign_id
    )
    return WorkflowStateResponse(
        campaign_id=campaign_id,
        current_step=current_step,
        can_confirm=can_confirm,
        has_audience=has_audience,
        has_content=has_content,
        has_schedule=has_schedule,
    )


@router.put("/workflows/{campaign_id}/step-2-content", response_model=WorkflowStateResponse)
def put_workflow_step2(
    campaign_id: int,
    req: WorkflowStep2ContentRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> WorkflowStateResponse:
    workflow_step2_content(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        campaign_id=campaign_id,
        steps=req.steps,
    )
    current_step, can_confirm, has_audience, has_content, has_schedule = workflow_state(
        db, salon_id=ctx.salon_id, campaign_id=campaign_id
    )
    return WorkflowStateResponse(
        campaign_id=campaign_id,
        current_step=current_step,
        can_confirm=can_confirm,
        has_audience=has_audience,
        has_content=has_content,
        has_schedule=has_schedule,
    )


@router.put("/workflows/{campaign_id}/step-3-schedule", response_model=WorkflowStateResponse)
def put_workflow_step3(
    campaign_id: int,
    req: WorkflowStep3ScheduleRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> WorkflowStateResponse:
    if req.schedule_type == "scheduled" and req.schedule_at is None:
        raise HTTPException(status_code=400, detail="schedule_at required for scheduled workflow")

    workflow_step3_schedule(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        campaign_id=campaign_id,
        schedule_type=req.schedule_type,
        schedule_at=req.schedule_at,
    )
    current_step, can_confirm, has_audience, has_content, has_schedule = workflow_state(
        db, salon_id=ctx.salon_id, campaign_id=campaign_id
    )
    return WorkflowStateResponse(
        campaign_id=campaign_id,
        current_step=current_step,
        can_confirm=can_confirm,
        has_audience=has_audience,
        has_content=has_content,
        has_schedule=has_schedule,
    )


@router.get("/workflows/{campaign_id}/step-4-confirmation", response_model=WorkflowStep4ConfirmationResponse)
def get_workflow_step4(
    campaign_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> WorkflowStep4ConfirmationResponse:
    campaign = get_campaign_by_id(db, salon_id=ctx.salon_id, campaign_id=campaign_id)
    steps = get_campaign_steps(db, campaign_id)
    return WorkflowStep4ConfirmationResponse(
        campaign_id=campaign_id,
        title=campaign.title,
        purpose=campaign.purpose,
        audience_type=campaign.audience_type,
        schedule_type=campaign.schedule_type,
        schedule_at=campaign.schedule_at,
        steps_count=len(steps),
        estimated_recipients=workflow_estimated_recipients(db, salon_id=ctx.salon_id, campaign_id=campaign_id),
    )


@router.post("/workflows/{campaign_id}/step-4-confirm", response_model=CommunicationLaunchResponse)
def post_workflow_step4_confirm(
    campaign_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CommunicationLaunchResponse:
    current_step, can_confirm, *_ = workflow_state(db, salon_id=ctx.salon_id, campaign_id=campaign_id)
    if not can_confirm:
        raise HTTPException(status_code=400, detail=f"workflow is incomplete, current_step={current_step}")

    selected, queued = launch_campaign(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        campaign_id=campaign_id,
    )
    return CommunicationLaunchResponse(campaign_id=campaign_id, selected_clients=selected, queued_recipients=queued)


@router.get("/workflows/{campaign_id}/step-5-stats", response_model=WorkflowStep5StatsResponse)
def get_workflow_step5_stats(
    campaign_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> WorkflowStep5StatsResponse:
    _ = get_campaign_by_id(db, salon_id=ctx.salon_id, campaign_id=campaign_id)
    total, sent, opened, clicked, converted = campaign_stats(db, campaign_id)
    return WorkflowStep5StatsResponse(
        campaign_id=campaign_id,
        total=total,
        sent=sent,
        opened=opened,
        clicked=clicked,
        converted=converted,
        open_rate=round((opened / sent) * 100, 2) if sent else 0,
        click_rate=round((clicked / sent) * 100, 2) if sent else 0,
        conversion_rate=round((converted / sent) * 100, 2) if sent else 0,
    )


@router.post("/{campaign_id}/launch", response_model=CommunicationLaunchResponse)
def post_launch_campaign(
    campaign_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CommunicationLaunchResponse:
    selected, queued = launch_campaign(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        campaign_id=campaign_id,
    )
    return CommunicationLaunchResponse(campaign_id=campaign_id, selected_clients=selected, queued_recipients=queued)


@router.post("/track", response_model=CommunicationStatsOut)
def post_track(
    req: CommunicationTrackRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CommunicationStatsOut:
    row = track_recipient_event(db, recipient_id=req.recipient_id, event=req.event)
    campaign = db.execute(
        select(CommunicationCampaign).where(
            and_(
                CommunicationCampaign.id == row.campaign_id,
                CommunicationCampaign.salon_id == ctx.salon_id,
            )
        )
    ).scalar_one()
    total, sent, opened, clicked, converted = campaign_stats(db, campaign.id)
    return CommunicationStatsOut(
        campaign_id=campaign.id,
        total=total,
        sent=sent,
        opened=opened,
        clicked=clicked,
        converted=converted,
        open_rate=round((opened / sent) * 100, 2) if sent else 0,
        click_rate=round((clicked / sent) * 100, 2) if sent else 0,
        conversion_rate=round((converted / sent) * 100, 2) if sent else 0,
    )


@router.get("/{campaign_id}/stats", response_model=CommunicationStatsOut)
def get_campaign_stats(
    campaign_id: int,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> CommunicationStatsOut:
    _ = db.execute(
        select(CommunicationCampaign).where(
            CommunicationCampaign.id == campaign_id,
            CommunicationCampaign.salon_id == ctx.salon_id,
        )
    ).scalar_one()
    total, sent, opened, clicked, converted = campaign_stats(db, campaign_id)
    return CommunicationStatsOut(
        campaign_id=campaign_id,
        total=total,
        sent=sent,
        opened=opened,
        clicked=clicked,
        converted=converted,
        open_rate=round((opened / sent) * 100, 2) if sent else 0,
        click_rate=round((clicked / sent) * 100, 2) if sent else 0,
        conversion_rate=round((converted / sent) * 100, 2) if sent else 0,
    )


@router.get("/reminders/rules", response_model=ReminderRulesResponse)
def get_rules(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ReminderRulesResponse:
    rows = get_reminder_rules(db, ctx.salon_id)
    return ReminderRulesResponse(
        items=[
            ReminderRuleOut(id=x.id, offset_minutes=x.offset_minutes, channel=x.channel, is_enabled=x.is_enabled)
            for x in rows
        ]
    )


@router.put("/reminders/rules", response_model=ReminderRulesResponse)
def put_rules(
    req: ReminderRulesUpdateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ReminderRulesResponse:
    rows = set_reminder_rules(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        rules=[(x.offset_minutes, x.channel, x.is_enabled) for x in req.rules],
    )
    return ReminderRulesResponse(
        items=[
            ReminderRuleOut(id=x.id, offset_minutes=x.offset_minutes, channel=x.channel, is_enabled=x.is_enabled)
            for x in rows
        ]
    )


@router.post("/appointments", response_model=AppointmentOut)
def post_appointment(
    req: AppointmentCreateRequest,
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> AppointmentOut:
    row = create_appointment(
        db,
        salon_id=ctx.salon_id,
        actor_user_id=ctx.user_id,
        client_id=req.client_id,
        employee_id=req.employee_id,
        service_id=req.service_id,
        title=req.title,
        starts_at=req.starts_at,
        duration_minutes=req.duration_minutes,
        source=req.source,
    )
    return AppointmentOut(
        id=row.id,
        client_id=row.client_id,
        employee_id=row.employee_id,
        service_id=row.service_id,
        title=row.title,
        starts_at=row.starts_at,
        duration_minutes=row.duration_minutes,
        status=row.status,
        source=row.source,
    )


@router.post("/reminders/run", response_model=ReminderRunResponse)
def post_run_reminders(
    ctx=Depends(require_roles("owner", "admin")),
    db: Session = Depends(get_db),
) -> ReminderRunResponse:
    processed, sent, skipped = run_reminders(db, salon_id=ctx.salon_id)
    return ReminderRunResponse(processed=processed, sent=sent, skipped=skipped)

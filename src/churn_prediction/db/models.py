import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from churn_prediction.db.session import Base


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class CustomerPrediction(Base):
    """Registro de predições de churn (inferência individual ou batch)."""

    __tablename__ = "customer_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(32), nullable=False)
    mrr_at_risk: Mapped[float] = mapped_column(Float, default=0.0)
    top_drivers_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str] = mapped_column(String(32), default="v1.0.0")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )

    __table_args__ = (Index("ix_predictions_customer_created", "customer_id", "created_at"),)


class RetentionPlaybookAction(Base):
    """Registro de aplicação de playbooks de retenção para um cliente."""

    __tablename__ = "retention_playbook_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    playbook: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    discount_pct: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_risk_reduction: Mapped[float] = mapped_column(Float, default=0.0)
    expected_annual_savings: Mapped[float] = mapped_column(Float, default=0.0)
    applied_by: Mapped[str] = mapped_column(String(64), default="analyst")
    status: Mapped[str] = mapped_column(
        String(32), default="applied"
    )  # applied, accepted, rejected
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


class CustomerOutcome(Base):
    """Desfecho real observado (Ground Truth) para fechamento do ciclo de retenção."""

    __tablename__ = "customer_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    churn_occurred: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Retido, 1=Churn
    observed_months: Mapped[int] = mapped_column(Integer, default=1)
    actual_revenue_saved: Mapped[float] = mapped_column(Float, default=0.0)
    outcome_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuditLog(Base):
    """Trilha de auditoria para conformidade, segurança e governança de dados."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource: Mapped[str] = mapped_column(String(128), nullable=False)
    user: Mapped[str] = mapped_column(String(64), default="system")
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )

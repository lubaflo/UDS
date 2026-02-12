from __future__ import annotations

from sqlalchemy import Date, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmployeeCategory(Base):
    __tablename__ = "employee_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_employee_categories_salon", "salon_id"),
        Index("ix_employee_categories_salon_name", "salon_id", "name"),
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee_categories.id", ondelete="SET NULL"), nullable=True
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(254), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")

    payment_type: Mapped[str] = mapped_column(String(24), nullable=False, default="hourly")  # hourly/piecework
    hourly_rate: Mapped[float] = mapped_column(nullable=False, default=0)
    piece_rate: Mapped[float] = mapped_column(nullable=False, default=0)

    created_at: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_employees_salon", "salon_id"),
        Index("ix_employees_salon_name", "salon_id", "full_name"),
        Index("ix_employees_salon_category", "salon_id", "category_id"),
    )


class EmployeeTimeEntry(Base):
    __tablename__ = "employee_time_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    work_date: Mapped[Date] = mapped_column(Date, nullable=False)
    start_at: Mapped[str] = mapped_column(String(5), nullable=False, default="")
    end_at: Mapped[str] = mapped_column(String(5), nullable=False, default="")
    hours_worked: Mapped[float] = mapped_column(nullable=False, default=0)
    units_completed: Mapped[float] = mapped_column(nullable=False, default=0)
    note: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_employee_time_entries_salon_employee_date", "salon_id", "employee_id", "work_date"),
    )


class EmployeeSchedule(Base):
    __tablename__ = "employee_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    work_date: Mapped[Date] = mapped_column(Date, nullable=False)
    planned_start: Mapped[str] = mapped_column(String(5), nullable=False)
    planned_end: Mapped[str] = mapped_column(String(5), nullable=False)
    break_minutes: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="planned")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_employee_schedules_salon_employee_date", "salon_id", "employee_id", "work_date"),
    )


class EmployeePayrollAccrual(Base):
    __tablename__ = "employee_payroll_accruals"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)

    period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    period_end: Mapped[Date] = mapped_column(Date, nullable=False)
    payment_type: Mapped[str] = mapped_column(String(24), nullable=False)
    hours: Mapped[float] = mapped_column(nullable=False, default=0)
    units: Mapped[float] = mapped_column(nullable=False, default=0)
    amount: Mapped[float] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="calculated")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_employee_payroll_accruals_salon_employee", "salon_id", "employee_id"),
        Index("ix_employee_payroll_accruals_period", "salon_id", "period_start", "period_end"),
    )


class EmployeeHistory(Base):
    __tablename__ = "employee_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    payload_json: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    created_at: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_employee_history_salon_employee", "salon_id", "employee_id"),
    )

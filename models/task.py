from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .metadata import Base

class Task(Base):
    __tablename__ = 'task'

    task_id: Mapped[int] = mapped_column(primary_key=True)

    task_code: Mapped[str] = mapped_column(String(64))
    task_name: Mapped[str] = mapped_column(String(255))
    task_status: Mapped[int]

    time_intervals: Mapped[List['Time_Interval']] = relationship(back_populates='task')
    notes: Mapped[List['Note']] = relationship(back_populates='task')

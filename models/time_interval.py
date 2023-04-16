import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .metadata import Base

class Time_Interval(Base):
    __tablename__ = 'time_interval'

    time_interval_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.task_id'))
    started: Mapped[datetime.datetime]
    ended: Mapped[Optional[datetime.datetime]]

    task: Mapped['Task'] = relationship(back_populates = 'time_intervals')
    notes: Mapped[List['Note']] = relationship(back_populates='time_interval')


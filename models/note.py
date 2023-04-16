from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey

from .metadata import Base

class Note(Base):
    __tablename__ = 'note'

    note_id: Mapped[int] = mapped_column(primary_key=True)
    time_interval_id: Mapped[Optional[int]] = mapped_column(ForeignKey('time_interval.time_interval_id'))
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey('task.task_id'))
    note_text: Mapped[str] = mapped_column(String(4096))

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .metadata import Base

class Task(Base):
    __tablename__ = 'task'

    task_id: Mapped[int] = mapped_column(primary_key=True)

    task_code: Mapped[str] = mapped_column(String(64))
    task_name: Mapped[str] = mapped_column(String(255))
    task_status: Mapped[int]

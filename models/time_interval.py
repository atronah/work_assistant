from .metadata import metadata_obj
from sqlalchemy import Table, Column, Integer, DateTime, ForeignKey

time_interval_table = Table(
    "time_interval",
    metadata_obj,
    Column('time_interval_id', Integer, primary_key=True),
    Column('task_id', ForeignKey("task.task_id"), nullable=False),
    Column('started', DateTime, nullable=False),
    Column('ended', DateTime, nullable=True)
)

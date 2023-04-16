from .metadata import metadata_obj
from sqlalchemy import Table, Column, Integer, String, ForeignKey

note_table = Table(
    "note",
    metadata_obj,
    Column('note_id', Integer, primary_key=True),
    Column('time_interval_id', ForeignKey("time_interval.time_interval_id"), nullable=True),
    Column('task_id', ForeignKey("task.task_id"), nullable=True),
    Column('note_text', String(4096), nullable=False)
)

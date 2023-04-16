from .metadata import metadata_obj
from sqlalchemy import Table, Column, Integer, String

task_table = Table(
    "task",
    metadata_obj,
    Column('task_id', Integer, primary_key=True),
    Column('task_code', String(64), nullable=False),
    Column('task_name', String(255), nullable=False),
    Column('task_status', Integer, nullable=False)
)

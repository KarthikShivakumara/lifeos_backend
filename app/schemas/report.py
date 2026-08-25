from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ReportRead(ORMModel):
    id: str
    user_id: str
    report_type: str
    title: str
    summary: str
    file_url: str | None
    created_at: datetime


class ReportCreate(BaseModel):
    report_type: str
    title: str
    summary: str

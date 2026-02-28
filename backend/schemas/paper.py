from pydantic import BaseModel
from datetime import datetime


# --- Project ---

class ProjectCreate(BaseModel):
    title: str = "未命名论文"
    abstract: str = ""

class ProjectUpdate(BaseModel):
    title: str | None = None
    abstract: str | None = None
    status: str | None = None

class ProjectOut(BaseModel):
    id: int
    title: str
    abstract: str
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# --- Section ---

class SectionCreate(BaseModel):
    project_id: int
    parent_id: int | None = None
    title: str = ""
    content: str = ""
    order: int = 0

class SectionUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    order: int | None = None
    status: str | None = None

class SectionOut(BaseModel):
    id: int
    project_id: int
    parent_id: int | None
    title: str
    content: str
    order: int
    status: str
    model_config = {"from_attributes": True}


# --- Reference ---

class ReferenceCreate(BaseModel):
    project_id: int
    title: str = ""
    authors: str = ""
    year: int | None = None
    doi: str = ""
    abstract: str = ""

class ReferenceOut(BaseModel):
    id: int
    project_id: int
    title: str
    authors: str
    year: int | None
    doi: str
    abstract: str
    file_path: str
    model_config = {"from_attributes": True}

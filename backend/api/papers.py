"""论文项目 CRUD 路由。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.postgres import get_db
from backend.database.models import Project, Section
from backend.schemas.paper import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    SectionCreate, SectionUpdate, SectionOut,
)

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/projects", response_model=ProjectOut)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(title=body.title, abstract=body.abstract)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectOut)
async def update_project(project_id: int, body: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(project, k, v)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    await db.delete(project)
    await db.commit()
    return {"ok": True}


# --- Sections ---

@router.post("/sections", response_model=SectionOut)
async def create_section(body: SectionCreate, db: AsyncSession = Depends(get_db)):
    section = Section(**body.model_dump())
    db.add(section)
    await db.commit()
    await db.refresh(section)
    return section


@router.get("/projects/{project_id}/sections", response_model=list[SectionOut])
async def list_sections(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Section).where(Section.project_id == project_id).order_by(Section.order)
    )
    return result.scalars().all()


@router.patch("/sections/{section_id}", response_model=SectionOut)
async def update_section(section_id: int, body: SectionUpdate, db: AsyncSession = Depends(get_db)):
    section = await db.get(Section, section_id)
    if not section:
        raise HTTPException(404, "章节不存在")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(section, k, v)
    await db.commit()
    await db.refresh(section)
    return section

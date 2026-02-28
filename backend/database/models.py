import datetime
from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    """论文项目。"""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(default="未命名论文")
    abstract: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(default="draft")  # draft / writing / reviewing / done
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    sections: Mapped[list["Section"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    references: Mapped[list["Reference"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    agent_tasks: Mapped[list["AgentTask"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Section(Base):
    """论文章节（树形结构）。"""
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id"), default=None)
    title: Mapped[str] = mapped_column(default="")
    content: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(default="pending")  # pending / writing / review / done

    project: Mapped["Project"] = relationship(back_populates="sections")
    children: Mapped[list["Section"]] = relationship(back_populates="parent")
    parent: Mapped["Section | None"] = relationship(back_populates="children", remote_side="Section.id")
    revisions: Mapped[list["Revision"]] = relationship(back_populates="section", cascade="all, delete-orphan")


class Reference(Base):
    """参考文献元数据。"""
    __tablename__ = "references"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(default="")
    authors: Mapped[str] = mapped_column(default="")
    year: Mapped[int | None] = mapped_column(default=None)
    doi: Mapped[str] = mapped_column(default="")
    abstract: Mapped[str] = mapped_column(Text, default="")
    file_path: Mapped[str] = mapped_column(default="")

    project: Mapped["Project"] = relationship(back_populates="references")


class AgentTask(Base):
    """Agent 任务执行记录。"""
    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    agent_type: Mapped[str] = mapped_column(default="")  # literature / outline / writer / reviewer / formatter
    status: Mapped[str] = mapped_column(default="pending")  # pending / running / done / failed
    input_data: Mapped[str] = mapped_column(Text, default="{}")
    output_data: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="agent_tasks")


class Revision(Base):
    """章节修订历史。"""
    __tablename__ = "revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"))
    content: Mapped[str] = mapped_column(Text, default="")
    revision_type: Mapped[str] = mapped_column(default="auto")  # auto / manual
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    section: Mapped["Section"] = relationship(back_populates="revisions")

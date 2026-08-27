from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class DomainTag:
    id: int
    name: str
    color: Optional[str] = None

@dataclass
class DomainNote:
    id: int
    content: str
    created_at: datetime
    github_id: Optional[int] = None
    metadata: dict = field(default_factory=dict)
    deleted_at: Optional[datetime] = None

@dataclass
class DomainWorkItem:
    id: Optional[int]
    repo_name: str
    item_type: str
    title: str
    body: Optional[str] = ""
    github_id: Optional[str] = None
    github_number: Optional[str] = None
    state: str = "open"
    sync_status: str = "PENDING_PUSH"
    local_updated_at: datetime = field(default_factory=datetime.now)
    tags: List[DomainTag] = field(default_factory=list)
    notes: List[DomainNote] = field(default_factory=list)
    github_sha: Optional[str] = None
    type_metadata: dict = field(default_factory=dict)
    deleted_at: Optional[datetime] = None

@dataclass
class DomainRepo:
    id: int
    name: str
    owner: str
    github_id: Optional[str] = None
    is_offline: bool = False
    deleted_at: Optional[datetime] = None

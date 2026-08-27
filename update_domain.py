import re

with open("src/core/domain.py", "r") as f:
    content = f.read()

# DomainRepo
repo_old = """@dataclass
class DomainRepo:
    id: int
    name: str
    owner: Optional[str]
    github_id: Optional[str]"""
repo_new = """@dataclass
class DomainRepo:
    id: int
    name: str
    owner: Optional[str]
    github_id: Optional[str]
    is_offline: bool = False
    deleted_at: Optional[datetime] = None"""
content = content.replace(repo_old, repo_new)

# DomainWorkItem
wi_old = """@dataclass
class DomainWorkItem:
    id: Optional[int]
    repo_name: str
    item_type: str
    title: str
    body: str
    github_id: Optional[int]
    github_number: Optional[int]
    state: str
    sync_status: str
    local_updated_at: datetime
    tags: List[DomainTag] = field(default_factory=list)
    notes: List[DomainNote] = field(default_factory=list)"""
wi_new = """@dataclass
class DomainWorkItem:
    id: Optional[int]
    repo_name: str
    item_type: str
    title: str
    body: str
    github_id: Optional[int]
    github_number: Optional[int]
    state: str
    sync_status: str
    local_updated_at: datetime
    tags: List[DomainTag] = field(default_factory=list)
    notes: List[DomainNote] = field(default_factory=list)
    github_sha: Optional[str] = None
    type_metadata: dict = field(default_factory=dict)
    deleted_at: Optional[datetime] = None"""
content = content.replace(wi_old, wi_new)

# DomainNote
note_old = """@dataclass
class DomainNote:
    id: int
    content: str
    created_at: datetime
    github_id: Optional[int] = None"""
note_new = """@dataclass
class DomainNote:
    id: int
    content: str
    created_at: datetime
    github_id: Optional[int] = None
    metadata: dict = field(default_factory=dict)
    deleted_at: Optional[datetime] = None"""
content = content.replace(note_old, note_new)

with open("src/core/domain.py", "w") as f:
    f.write(content)

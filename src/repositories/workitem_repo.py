import logging
from typing import List, Optional
import datetime
from src.core.domain import DomainWorkItem, DomainRepo, DomainNote, DomainTag
from src.models.schema import Repo, WorkItem, WorkItemType, Note, Tag, WorkItemTag
from src.models.database import db

logger = logging.getLogger(__name__)

class WorkItemRepository:
    """
    The Anti-Corruption Layer. 
    Abstracts Peewee DB queries and returns pure Domain models.
    """
    
    def __init__(self):
        # Ensure database is connected
        if not db.is_closed():
            pass

    def get_all_repos(self, include_deleted=False) -> List[DomainRepo]:
        if include_deleted:
            repos = Repo.select()
        else:
            repos = Repo.select().where(Repo.deleted_at.is_null())
        return [DomainRepo(id=r.id, name=r.name, owner=r.owner, github_id=r.github_id, is_offline=r.is_offline, deleted_at=r.deleted_at) for r in repos]

    def _to_domain_workitem(self, wi) -> DomainWorkItem:
        import json
        domain_wi = DomainWorkItem(
            id=wi.id,
            repo_name=wi.repo.name,
            item_type=wi.item_type.name,
            title=wi.title,
            body=wi.body,
            github_id=wi.github_id,
            github_number=wi.github_number,
            state=wi.state,
            sync_status=wi.sync_status,
            local_updated_at=wi.local_updated_at,
            github_sha=wi.github_sha,
            type_metadata=json.loads(wi.type_metadata) if wi.type_metadata else {},
            deleted_at=wi.deleted_at
        )
        
        # Map tags
        from src.models.schema import Tag, WorkItemTag, Note
        tags = (Tag.select()
                .join(WorkItemTag)
                .where(WorkItemTag.work_item == wi))
        domain_wi.tags = [DomainTag(id=t.id, name=t.name, color=t.color) for t in tags]
        
        # Map notes
        notes = Note.select().where(Note.work_item == wi, Note.deleted_at.is_null()).order_by(Note.created_at.asc())
        domain_wi.notes = [
            DomainNote(
                id=n.id, 
                content=n.content, 
                created_at=n.created_at, 
                metadata=json.loads(n.metadata) if n.metadata else {},
                deleted_at=n.deleted_at
            ) for n in notes
        ]
        
        return domain_wi

    def get_workitems_for_repo(self, repo_name: str, include_deleted=False) -> List[DomainWorkItem]:
        query = (WorkItem.select()
                     .join(Repo)
                     .where(Repo.name == repo_name))
        if not include_deleted:
            query = query.where(WorkItem.deleted_at.is_null())
        workitems = query.order_by(WorkItem.local_updated_at.desc())
        domain_items = []
        for wi in workitems:
            domain_items.append(self._to_domain_workitem(wi))
            
        return domain_items

    def save_workitem(self, domain_item: DomainWorkItem) -> DomainWorkItem:
        """Saves a WorkItem to local DB and returns the updated Domain model (with DB ID)."""
        with db.connection_context():
            # Get or create the Repo and Type (simplification for this phase)
            repo, _ = Repo.get_or_create(name=domain_item.repo_name, defaults={'owner': 'unknown'})
            item_type, _ = WorkItemType.get_or_create(name=domain_item.item_type)
            
            if domain_item.id:
                # Update existing
                wi = WorkItem.get(WorkItem.id == domain_item.id)
                wi.title = domain_item.title
                wi.body = domain_item.body
                wi.state = domain_item.state
                wi.sync_status = domain_item.sync_status
                wi.github_sha = domain_item.github_sha
                wi.save()
            else:
                # Create new
                wi = WorkItem.create(
                    repo=repo,
                    item_type=item_type,
                    title=domain_item.title,
                    body=domain_item.body,
                    state=domain_item.state,
                    sync_status=domain_item.sync_status,
                    github_sha=domain_item.github_sha
                )
                domain_item.id = wi.id
                
            return domain_item

    def add_note(self, workitem_id: int, content: str) -> DomainNote:
        with db.connection_context():
            wi = WorkItem.get(WorkItem.id == workitem_id)
            note = Note.create(work_item=wi, content=content)
            return DomainNote(id=note.id, content=note.content, created_at=note.created_at)


    def get_workitem_by_id(self, item_id: int) -> Optional[DomainWorkItem]:
        from src.models.schema import WorkItem
        try:
            db_item = WorkItem.get_by_id(item_id)
            return self._to_domain_workitem(db_item)
        except WorkItem.DoesNotExist:
            return None

    def delete_repo(self, name: str):
        repo = Repo.get_or_none(Repo.name == name)
        if repo:
            repo.deleted_at = datetime.datetime.now()
            repo.save()

    def delete_workitem(self, wi_id: int):
        wi = WorkItem.get_or_none(WorkItem.id == wi_id)
        if wi:
            wi.deleted_at = datetime.datetime.now()
            wi.save()

    def delete_note(self, note_id: int):
        n = Note.get_or_none(Note.id == note_id)
        if n:
            n.deleted_at = datetime.datetime.now()
            n.save()

    def restore_workitem(self, wi_id: int):
        wi = WorkItem.get_or_none(WorkItem.id == wi_id)
        if wi:
            wi.deleted_at = None
            wi.save()

    def restore_note(self, note_id: int):
        n = Note.get_or_none(Note.id == note_id)
        if n:
            n.deleted_at = None
            n.save()

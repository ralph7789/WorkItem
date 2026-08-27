import re

with open("src/repositories/workitem_repo.py", "r") as f:
    content = f.read()

import json

# Replace _to_domain_workitem
to_domain_old = """    def _to_domain_workitem(self, wi) -> DomainWorkItem:
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
            local_updated_at=wi.local_updated_at
        )
        
        # Map tags
        from src.models.schema import Tag, WorkItemTag, Note
        tags = (Tag.select()
                .join(WorkItemTag)
                .where(WorkItemTag.work_item == wi))
        domain_wi.tags = [DomainTag(id=t.id, name=t.name, color=t.color) for t in tags]
        
        # Map notes
        notes = Note.select().where(Note.work_item == wi).order_by(Note.created_at.asc())
        domain_wi.notes = [DomainNote(id=n.id, content=n.content, created_at=n.created_at) for n in notes]
        
        return domain_wi"""

to_domain_new = """    def _to_domain_workitem(self, wi) -> DomainWorkItem:
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
                github_id=n.github_id,
                metadata=json.loads(n.metadata) if n.metadata else {},
                deleted_at=n.deleted_at
            ) for n in notes
        ]
        
        return domain_wi"""
content = content.replace(to_domain_old, to_domain_new)

# Update get_all_repos to filter deleted
get_repos_old = """    def get_all_repos(self) -> List[DomainRepo]:
        repos = Repo.select()
        return [DomainRepo(id=r.id, name=r.name, owner=r.owner, github_id=r.github_id) for r in repos]"""
get_repos_new = """    def get_all_repos(self, include_deleted=False) -> List[DomainRepo]:
        if include_deleted:
            repos = Repo.select()
        else:
            repos = Repo.select().where(Repo.deleted_at.is_null())
        return [DomainRepo(id=r.id, name=r.name, owner=r.owner, github_id=r.github_id, is_offline=r.is_offline, deleted_at=r.deleted_at) for r in repos]"""
content = content.replace(get_repos_old, get_repos_new)

# Update get_workitems_for_repo to filter deleted
get_wi_old = """    def get_workitems_for_repo(self, repo_name: str) -> List[DomainWorkItem]:
        workitems = (WorkItem.select()
                     .join(Repo)
                     .where(Repo.name == repo_name))"""
get_wi_new = """    def get_workitems_for_repo(self, repo_name: str, include_deleted=False) -> List[DomainWorkItem]:
        query = (WorkItem.select()
                     .join(Repo)
                     .where(Repo.name == repo_name))
        if not include_deleted:
            query = query.where(WorkItem.deleted_at.is_null())
        workitems = query.order_by(WorkItem.local_updated_at.desc())"""
content = content.replace(get_wi_old, get_wi_new)

# Update save_workitem
save_wi_old = """            if domain_item.id:
                wi = WorkItem.get_by_id(domain_item.id)
                wi.title = domain_item.title
                wi.body = domain_item.body
                wi.state = domain_item.state
                wi.sync_status = domain_item.sync_status
                wi.local_updated_at = domain_item.local_updated_at
                wi.github_id = domain_item.github_id
                wi.github_number = domain_item.github_number
                wi.save()
            else:
                repo = Repo.get(Repo.name == domain_item.repo_name)
                wt, _ = WorkItemType.get_or_create(name=domain_item.item_type)
                
                wi = WorkItem.create(
                    repo=repo,
                    item_type=wt,
                    title=domain_item.title,
                    body=domain_item.body,
                    state=domain_item.state,
                    sync_status=domain_item.sync_status,
                    local_updated_at=domain_item.local_updated_at,
                    github_id=domain_item.github_id,
                    github_number=domain_item.github_number
                )
                domain_item.id = wi.id"""
save_wi_new = """            import json
            if domain_item.id:
                wi = WorkItem.get_by_id(domain_item.id)
                wi.title = domain_item.title
                wi.body = domain_item.body
                wi.state = domain_item.state
                wi.sync_status = domain_item.sync_status
                wi.local_updated_at = domain_item.local_updated_at
                wi.github_id = domain_item.github_id
                wi.github_number = domain_item.github_number
                wi.github_sha = domain_item.github_sha
                wi.type_metadata = json.dumps(domain_item.type_metadata)
                wi.deleted_at = domain_item.deleted_at
                wi.save()
            else:
                repo = Repo.get(Repo.name == domain_item.repo_name)
                wt, _ = WorkItemType.get_or_create(name=domain_item.item_type)
                
                wi = WorkItem.create(
                    repo=repo,
                    item_type=wt,
                    title=domain_item.title,
                    body=domain_item.body,
                    state=domain_item.state,
                    sync_status=domain_item.sync_status,
                    local_updated_at=domain_item.local_updated_at,
                    github_id=domain_item.github_id,
                    github_number=domain_item.github_number,
                    github_sha=domain_item.github_sha,
                    type_metadata=json.dumps(domain_item.type_metadata),
                    deleted_at=domain_item.deleted_at
                )
                domain_item.id = wi.id"""
content = content.replace(save_wi_old, save_wi_new)


with open("src/repositories/workitem_repo.py", "w") as f:
    f.write(content)

with open("src/repositories/workitem_repo.py", "r") as f:
    content = f.read()

mapper_code = """    def _to_domain_workitem(self, wi) -> DomainWorkItem:
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
        
        return domain_wi

    def get_workitems_for_repo"""
content = content.replace("    def get_workitems_for_repo", mapper_code)

get_workitems_old = """        for wi in workitems:
            # Map simple fields
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
            tags = (Tag.select()
                    .join(WorkItemTag)
                    .where(WorkItemTag.work_item == wi))
            domain_wi.tags = [DomainTag(id=t.id, name=t.name, color=t.color) for t in tags]
            
            # Map notes
            notes = Note.select().where(Note.work_item == wi).order_by(Note.created_at.asc())
            domain_wi.notes = [DomainNote(id=n.id, content=n.content, created_at=n.created_at) for n in notes]
            
            domain_items.append(domain_wi)"""
get_workitems_new = """        for wi in workitems:
            domain_items.append(self._to_domain_workitem(wi))"""

content = content.replace(get_workitems_old, get_workitems_new)

with open("src/repositories/workitem_repo.py", "w") as f:
    f.write(content)

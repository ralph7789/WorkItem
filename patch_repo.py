with open("src/repositories/workitem_repo.py", "r") as f:
    content = f.read()

delete_methods = """
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
"""
content = content + delete_methods
with open("src/repositories/workitem_repo.py", "w") as f:
    f.write(content)

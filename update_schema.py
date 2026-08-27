import re

with open("src/models/schema.py", "r") as f:
    content = f.read()

# BaseModel
base_old = """class BaseModel(Model):
    class Meta:
        database = db"""
base_new = """class BaseModel(Model):
    deleted_at = DateTimeField(null=True)
    class Meta:
        database = db"""
content = content.replace(base_old, base_new)

# Repo
repo_old = """class Repo(BaseModel):
    name = CharField(unique=True)
    owner = CharField(null=True)
    github_id = CharField(null=True)"""
repo_new = """class Repo(BaseModel):
    name = CharField(unique=True)
    owner = CharField(null=True)
    github_id = CharField(null=True)
    is_offline = BooleanField(default=False)"""
content = content.replace(repo_old, repo_new)

# WorkItem
wi_old = """class WorkItem(BaseModel):
    repo = ForeignKeyField(Repo, backref='work_items')
    item_type = ForeignKeyField(WorkItemType, backref='work_items')
    title = CharField()
    body = TextField(null=True)
    github_id = IntegerField(null=True, unique=True)
    github_number = IntegerField(null=True)
    state = CharField(default='open')
    sync_status = CharField(default='synced')
    local_updated_at = DateTimeField(default=datetime.datetime.now)"""
wi_new = """class WorkItem(BaseModel):
    repo = ForeignKeyField(Repo, backref='work_items')
    item_type = ForeignKeyField(WorkItemType, backref='work_items')
    title = CharField()
    body = TextField(null=True)
    github_id = IntegerField(null=True, unique=True)
    github_number = IntegerField(null=True)
    state = CharField(default='open')
    sync_status = CharField(default='synced')
    local_updated_at = DateTimeField(default=datetime.datetime.now)
    github_sha = CharField(null=True)
    type_metadata = TextField(default='{}')"""
content = content.replace(wi_old, wi_new)

# Note
note_old = """class Note(BaseModel):
    work_item = ForeignKeyField(WorkItem, backref='notes')
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    github_id = IntegerField(null=True, unique=True)"""
note_new = """class Note(BaseModel):
    work_item = ForeignKeyField(WorkItem, backref='notes')
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    github_id = IntegerField(null=True, unique=True)
    metadata = TextField(default='{}')"""
content = content.replace(note_old, note_new)


with open("src/models/schema.py", "w") as f:
    f.write(content)

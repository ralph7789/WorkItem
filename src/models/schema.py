from peewee import Model, CharField, DateTimeField, ForeignKeyField, TextField, BooleanField, IntegerField
import datetime
from .database import db

class BaseModel(Model):
    deleted_at = DateTimeField(null=True)
    class Meta:
        database = db

class Repo(BaseModel):
    name = CharField()
    owner = CharField()
    github_id = CharField(unique=True, null=True)
    is_offline = BooleanField(default=False)

class WorkItemType(BaseModel):
    name = CharField(unique=True)
    description = TextField(null=True)

class WorkItem(BaseModel):
    repo = ForeignKeyField(Repo, backref='work_items')
    item_type = ForeignKeyField(WorkItemType, backref='work_items')
    title = CharField()
    body = TextField(null=True)
    
    # GitHub references
    github_id = CharField(unique=True, null=True)
    github_number = CharField(null=True)
    state = CharField(default='open')
    
    # Required Sync status fields
    local_updated_at = DateTimeField(default=datetime.datetime.now)
    github_updated_at = DateTimeField(null=True)
    
    # Recommended sync metadata
    sync_status = CharField(default='PENDING_PUSH') # PENDING_PUSH, SYNCED, CONFLICT

    # New fields for File sync
    github_sha = CharField(null=True)
    type_metadata = TextField(default='{}')

class Note(BaseModel):
    work_item = ForeignKeyField(WorkItem, backref='notes')
    content = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    metadata = TextField(default='{}')

class Tag(BaseModel):
    name = CharField(unique=True)
    color = CharField(null=True)

class WorkItemTag(BaseModel):
    work_item = ForeignKeyField(WorkItem, backref='tags')
    tag = ForeignKeyField(Tag, backref='work_items')

# Create tables helper
def initialize_database():
    db.connect()
    db.create_tables([Repo, WorkItemType, WorkItem, Note, Tag, WorkItemTag], safe=True)
    db.close()

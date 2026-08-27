from src.models.schema import WorkItem
for wi in WorkItem.select().where(WorkItem.title.in_(['dex', 'aladin'])):
    print(wi.title, wi.sync_status, wi.deleted_at)

from src.core.github_sync import GitHubSyncWorker
import traceback
worker = GitHubSyncWorker("ralph7789/WorkItem")
try:
    print("Items:", worker.repo.get_workitems_for_repo("ralph7789/WorkItem"))
except Exception as e:
    traceback.print_exc()

from src.core.github_sync import GitHubSyncWorker
import os
import sys

worker = GitHubSyncWorker("ralph7789/WorkItem")
worker.run()
print("Done")

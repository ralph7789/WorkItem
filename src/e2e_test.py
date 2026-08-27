import sys
import json
import time
import traceback
from PySide6.QtCore import QTimer, QObject, Qt
from PySide6.QtWidgets import QApplication

class E2ETestRunner(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.results = []
        self.current_test = 0
        self.wait_ticks = 0
        
        self.tests = [
            self.test_repos_loaded,
            self.test_create_local_repo,
            self.test_create_workitem,
            self.test_add_note,
            self.test_details_card_visible,
            self.test_theme_toggle,
            self.test_recycle_bin
        ]
        
        print("--- E2E TEST: INITIALIZING TEST SUITE ---")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(500) # 500ms tick rate

    def tick(self):
        if self.current_test >= len(self.tests):
            self.generate_report()
            QApplication.quit()
            return
            
        test_func = self.tests[self.current_test]
        
        try:
            status = test_func()
            if status == "WAIT":
                self.wait_ticks += 1
                if self.wait_ticks > 20: # 10 seconds timeout
                    raise TimeoutError(f"Test timed out after 10 seconds.")
                return # Keep waiting
                
            # If it didn't return WAIT, it passed
            self.results.append({
                "name": test_func.__name__,
                "status": "PASS",
                "error": None
            })
            print(f"✅ PASS: {test_func.__name__}")
            
        except Exception as e:
            self.results.append({
                "name": test_func.__name__,
                "status": "FAIL",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            print(f"❌ FAIL: {test_func.__name__} - {str(e)}")
            
        self.current_test += 1
        self.wait_ticks = 0

    # --- TEST CASES ---

    def test_repos_loaded(self):
        if self.window.repo_combo.count() == 0:
            return "WAIT"
        
        # Select first available repo
        for i in range(self.window.repo_combo.count()):
            text = self.window.repo_combo.itemText(i)
            if "---" not in text:
                self.window.repo_combo.setCurrentIndex(i)
                return "PASS"
        raise ValueError("No selectable repositories found")

    def test_create_local_repo(self):
        # We can simulate creation by directly hitting the Repo model
        from src.models.schema import Repo
        Repo.get_or_create(name="e2e-test-repo", defaults={'owner': 'local', 'is_offline': True})
        self.window.load_repos()
        
        # Verify it exists in combo
        found = False
        for i in range(self.window.repo_combo.count()):
            if "e2e-test-repo" in self.window.repo_combo.itemText(i):
                found = True
                self.window.repo_combo.setCurrentIndex(i)
                break
        if not found:
            raise ValueError("Created local repo not found in UI combo box")
        return "PASS"

    def test_create_workitem(self):
        # Simulate creating a workitem directly via Repo
        from src.core.domain import DomainWorkItem
        from datetime import datetime, timezone
        domain_item = DomainWorkItem(
            id=None,
            repo_name="e2e-test-repo",
            item_type="Bug",
            title="E2E Test Bug",
            body="This is a test description.",
            github_id=None,
            github_number=None,
            state="open",
            sync_status="local",
            local_updated_at=datetime.now(timezone.utc)
        )
        self.window.repo.save_workitem(domain_item)
        self.window.load_local_data("e2e-test-repo")
        
        if self.window.workitem_model.rowCount() == 0:
            raise ValueError("WorkItem list is empty after creation")
            
        # Select it
        idx = self.window.workitem_model.index(0, 0)
        self.window.workitem_view.setCurrentIndex(idx)
        self.window.on_workitem_selected(idx)
        return "PASS"

    def test_add_note(self):
        if not self.window.current_workitem_id:
            raise ValueError("No WorkItem selected to add note")
            
        self.window.note_input.setPlainText("E2E Automated Note")
        self.window.on_submit_note()
        
        # Verify note is in HTML
        html = self.window.notes_browser.toHtml()
        if "E2E Automated Note" not in html:
            raise ValueError("Submitted note did not render in notes browser")
        return "PASS"
        
    def test_details_card_visible(self):
        if not self.window.details_card.isVisible():
            raise ValueError("Details card is not visible when a WorkItem is selected")
        if "E2E Test Bug" not in self.window.title_label.text():
            raise ValueError("Title label did not update correctly")
        return "PASS"

    def test_theme_toggle(self):
        initial_theme = self.window.is_classic_theme
        self.window.theme_toggle_btn.click()
        if self.window.is_classic_theme == initial_theme:
            raise ValueError("Theme toggle button failed to change theme state")
        # Toggle back
        self.window.theme_toggle_btn.click()
        return "PASS"
        
    def test_recycle_bin(self):
        self.window.recycle_toggle.setChecked(True)
        # Should now be in recycle mode
        if not self.window.is_recycle_mode:
            raise ValueError("Failed to enter Recycle Bin mode")
        self.window.recycle_toggle.setChecked(False)
        return "PASS"

    # --- REPORTING ---
    def generate_report(self):
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        total = len(self.results)
        
        # Write JSON
        json_report = {
            "timestamp": time.time(),
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": self.results
        }
        with open("e2e_report.json", "w") as f:
            json.dump(json_report, f, indent=4)
            
        # Write HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>WorkItems E2E Test Report</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; background: #1e1e1e; color: #e0e0e0; padding: 2rem; }}
        h1 {{ color: #3b82f6; }}
        .summary {{ font-size: 1.2rem; margin-bottom: 2rem; padding: 1rem; background: #252526; border-radius: 8px; border: 1px solid #333; }}
        .pass {{ color: #10b981; font-weight: bold; }}
        .fail {{ color: #ef4444; font-weight: bold; }}
        .test-card {{ background: #2b2d31; margin-bottom: 1rem; padding: 1rem; border-radius: 6px; border-left: 5px solid #333; }}
        .test-card.pass-card {{ border-left-color: #10b981; }}
        .test-card.fail-card {{ border-left-color: #ef4444; }}
        pre {{ background: #111; padding: 1rem; overflow-x: auto; border-radius: 4px; }}
    </style>
</head>
<body>
    <h1>WorkItems E2E Test Report</h1>
    <div class="summary">
        Total Tests: {total} | <span class="pass">Passed: {passed}</span> | <span class="fail">Failed: {total - passed}</span>
    </div>
"""
        for r in self.results:
            status_class = "pass-card" if r["status"] == "PASS" else "fail-card"
            html += f"""
    <div class="test-card {status_class}">
        <h3>{r['name']} - <span class="{'pass' if r['status'] == 'PASS' else 'fail'}">{r['status']}</span></h3>
"""
            if r["error"]:
                html += f"<h4>Error:</h4><p>{r['error']}</p>"
                html += f"<h4>Traceback:</h4><pre>{r['traceback']}</pre>"
            html += "</div>"
            
        html += "</body></html>"
        with open("e2e_report.html", "w") as f:
            f.write(html)
            
        print("--- E2E TEST: REPORT GENERATED ---")
        print(f"Results saved to e2e_report.json and e2e_report.html")


with open("src/ui/main_window.py", "r") as f:
    content = f.read()

main_code_old = """if __name__ == "__main__":
    logger.info("=== WORKITEMS APP STARTING ===")
    initialize_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit_code = app.exec()
    logger.info(f"=== WORKITEMS APP CLOSING (Exit Code: {exit_code}) ===")
    sys.exit(exit_code)"""

main_code_new = """if __name__ == "__main__":
    logger.info("=== WORKITEMS APP STARTING ===")
    initialize_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    _test_runner = None
    if "--ni" in sys.argv:
        try:
            from src.e2e_test import E2ETestRunner
            _test_runner = E2ETestRunner(window)
        except Exception as e:
            logger.error(f"Failed to start E2E test runner: {e}")
            
    exit_code = app.exec()
    logger.info(f"=== WORKITEMS APP CLOSING (Exit Code: {exit_code}) ===")
    sys.exit(exit_code)"""

content = content.replace(main_code_old, main_code_new)
with open("src/ui/main_window.py", "w") as f:
    f.write(content)

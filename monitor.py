import subprocess
import os
import sys
import threading
import time
from datetime import datetime

log_file = "workitems_monitor.log"

print(f"--- Starting Advanced Python Telemetry Monitor ---")
print(f"--- All app activity will be captured and written to {log_file} ---")

executable_path = os.path.join(os.path.dirname(__file__), "dist", "WorkItems")

if not os.path.exists(executable_path):
    print("Executable not found. Please build the app first.")
    sys.exit(1)

# Check for --ni flag
non_interactive = "--ni" in sys.argv

# We will pass --ni down to the executable
cmd = [executable_path]
if non_interactive:
    cmd.append("--ni")
    print("--- RUNNING IN NON-INTERACTIVE AUTOMATED TEST MODE ---")

with open(log_file, "a") as f:
    f.write(f"\n[{datetime.now().isoformat()}] --- TELEMETRY SESSION STARTED ---\n")
    f.flush()
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Read output line by line in real time
    for line in iter(process.stdout.readline, ''):
        timestamped_line = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] TELEMETRY_CAPTURE: {line}"
        print(timestamped_line, end="") # Echo to terminal
        f.write(timestamped_line)       # Write to log file
        f.flush()
        
    process.wait()
    
    close_msg = f"\n[{datetime.now().isoformat()}] --- TELEMETRY SESSION ENDED (Exit Code {process.returncode}) ---\n"
    print(close_msg)
    f.write(close_msg)

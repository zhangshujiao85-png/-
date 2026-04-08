# -*- coding: utf-8 -*-
"""
Monitor Streamlit installation and auto-start when ready
"""
import subprocess
import time
import sys
from pathlib import Path

def check_streamlit():
    """Check if Streamlit is installed and working"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import streamlit; from streamlit.cli import main; print('OK')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0 and 'OK' in result.stdout
    except:
        return False

def main():
    print("=" * 60)
    print("AI Timing Assistant - Installation Monitor")
    print("=" * 60)
    print("\nWaiting for Streamlit installation to complete...")
    print("Checking every 30 seconds...\n")

    check_count = 0
    while True:
        check_count += 1
        print(f"[Check #{check_count}] Testing Streamlit...", end=" ")

        if check_streamlit():
            print("\n" + "=" * 60)
            print("SUCCESS! Streamlit is ready!")
            print("=" * 60)
            print("\nYou can now start the web application:")
            print("\n  cd D:\\ai_timing_assistant")
            print("  streamlit run web/app.py")
            print("\nThen open: http://localhost:8501")
            print("\n" + "=" * 60)
            break
        else:
            print("Not ready yet, waiting...")

        if check_count >= 20:  # Max 10 minutes
            print("\nTaking too long. Please check manually:")
            print("  streamlit run web/app.py")
            break

        time.sleep(30)  # Wait 30 seconds between checks

if __name__ == "__main__":
    main()

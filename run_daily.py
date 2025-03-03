#!/usr/bin/env python3
import subprocess
import os
import datetime
import time


def run_daily_process():
    """Run the entire data collection and analysis process"""
    print(f"Starting daily process at {datetime.datetime.now()}")

    # Step 1: Run data collector
    print("Running data collector...")
    try:
        subprocess.run(['python', 'data_collector.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running data collector: {e}")
        return

    # Give a little time for file operations to complete
    time.sleep(2)

    # Step 2: Run analysis
    print("Running Buffett analysis...")
    try:
        subprocess.run(['python', 'buffett_analyzer.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running analysis: {e}")
        return

    print("Daily process completed successfully.")


if __name__ == "__main__":
    run_daily_process()
#!/usr/bin/env python3
"""
Daily inventory update script
Fetches latest new and used vehicle data from Ford Fairfield
"""
import subprocess
import sys
from datetime import datetime

def run_scraper(script_name):
    """Run a scraper script and return success status"""
    try:
        print(f"\n{'='*60}")
        print(f"Running {script_name}...")
        print(f"{'='*60}")
        result = subprocess.run(['python', script_name], capture_output=True, text=True, timeout=120)
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}", file=sys.stderr)
        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully")
            return True
        else:
            print(f"❌ {script_name} failed with return code {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {script_name} timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    print(f"\n{'*'*60}")
    print(f"Ford Inventory Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'*'*60}")
    
    new_success = run_scraper('scrapeNew.py')
    used_success = run_scraper('scrapeUsed.py')
    
    print(f"\n{'='*60}")
    print(f"Update Summary:")
    print(f"  New Inventory: {'✅ Success' if new_success else '❌ Failed'}")
    print(f"  Used Inventory: {'✅ Success' if used_success else '❌ Failed'}")
    print(f"{'='*60}\n")
    
    if new_success and used_success:
        print("🎉 Inventory update completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Some updates failed. Check logs above.")
        sys.exit(1)

if __name__ == '__main__':
    main()

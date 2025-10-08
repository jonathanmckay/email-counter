"""Helper script to set up daily scheduling on macOS using launchd."""

import os
import sys
from pathlib import Path


def create_launchd_plist():
    """Create a launchd plist file for macOS scheduling."""
    
    # Get absolute path to this directory
    script_dir = Path(__file__).parent.absolute()
    venv_python = script_dir / "venv" / "bin" / "python"
    reporter_script = script_dir / "email_reporter.py"
    
    # Get user's home directory
    home = Path.home()
    plist_dir = home / "Library" / "LaunchAgents"
    plist_file = plist_dir / "com.emailcounter.dailyreport.plist"
    
    # Create LaunchAgents directory if it doesn't exist
    plist_dir.mkdir(parents=True, exist_ok=True)
    
    # plist content - runs daily at 9 AM
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.emailcounter.dailyreport</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{venv_python}</string>
        <string>{reporter_script}</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>{script_dir}</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>{script_dir}/emailcounter.log</string>
    
    <key>StandardErrorPath</key>
    <string>{script_dir}/emailcounter.error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""
    
    # Write plist file
    with open(plist_file, 'w') as f:
        f.write(plist_content)
    
    print(f"✓ Created launchd plist file: {plist_file}")
    print(f"\nTo activate the daily scheduler, run:")
    print(f"  launchctl load {plist_file}")
    print(f"\nTo deactivate it:")
    print(f"  launchctl unload {plist_file}")
    print(f"\nTo test it immediately:")
    print(f"  launchctl start com.emailcounter.dailyreport")
    print(f"\nLogs will be written to:")
    print(f"  {script_dir}/emailcounter.log")
    print(f"  {script_dir}/emailcounter.error.log")
    
    return str(plist_file)


def create_cron_entry():
    """Print instructions for cron setup (Linux/Unix)."""
    script_dir = Path(__file__).parent.absolute()
    venv_python = script_dir / "venv" / "bin" / "python"
    reporter_script = script_dir / "email_reporter.py"
    
    cron_line = f"0 9 * * * cd {script_dir} && {venv_python} {reporter_script} >> {script_dir}/emailcounter.log 2>&1"
    
    print("\nFor Linux/Unix systems, add this line to your crontab:")
    print("  (Run: crontab -e)")
    print(f"\n{cron_line}")


def main():
    """Main entry point."""
    if sys.platform == 'darwin':
        print("Detected macOS - setting up launchd...")
        plist_file = create_launchd_plist()
        print("\n" + "="*60)
        create_cron_entry()
    elif sys.platform.startswith('linux') or sys.platform.startswith('unix'):
        print("Detected Linux/Unix - printing cron instructions...")
        create_cron_entry()
    elif sys.platform == 'win32':
        print("Windows detected. Please use Task Scheduler to schedule:")
        script_dir = Path(__file__).parent.absolute()
        print(f"  Program: {script_dir}\\venv\\Scripts\\python.exe")
        print(f"  Arguments: {script_dir}\\email_reporter.py")
        print(f"  Start in: {script_dir}")
    else:
        print(f"Unknown platform: {sys.platform}")
        print("Please manually schedule email_reporter.py to run daily.")


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Log Management Script for Voice Assistant
=========================================

This script helps manage and centralize all log files in the 'logs' directory.
It can be used to:
1. Check current log files and their locations
2. Move misplaced log files to the correct location
3. Clean up old log files
4. Display log file sizes and status

Usage:
    python3 manage_logs.py --check     # Check current log files
    python3 manage_logs.py --organize  # Move files to logs directory
    python3 manage_logs.py --clean     # Clean old files (>7 days)
    python3 manage_logs.py --status    # Show detailed status
"""

import os
import sys
import argparse
import shutil
from datetime import datetime, timedelta
from pathlib import Path


class LogManager:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root).resolve()
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Define expected log files and their patterns
        self.log_patterns = {
            "app.jsonl": "Main application logs (JSON format)",
            "performance.jsonl": "Performance metrics logs",
            "dialog_*.log": "LLM conversation logs",
            "transcriptions.log": "STT transcriptions log",
            "transcriptions.log.*": "Rotated transcription logs",
            "main_app.log": "Main application stdout/stderr",
            "memory_usage.log": "Memory usage monitoring",
        }
        
        # Files that should NOT be in logs (they belong elsewhere)
        self.excluded_files = {
            "config/memory.log": "User memory file (belongs in config)"
        }

    def find_all_log_files(self):
        """Find all log files in the project directory."""
        log_files = {}
        
        # Search for log files in project root and subdirectories
        for pattern in ["*.log", "*.jsonl"]:
            for log_file in self.project_root.rglob(pattern):
                if log_file.is_file():
                    relative_path = log_file.relative_to(self.project_root)
                    log_files[str(relative_path)] = {
                        "path": log_file,
                        "size": log_file.stat().st_size,
                        "modified": datetime.fromtimestamp(log_file.stat().st_mtime),
                        "in_logs_dir": log_file.parent == self.logs_dir
                    }
        
        return log_files

    def check_log_files(self):
        """Check and display current log files status."""
        print("🔍 Voice Assistant Log Files Status")
        print("=" * 50)
        
        log_files = self.find_all_log_files()
        
        if not log_files:
            print("No log files found.")
            return
        
        # Categorize files
        correct_location = []
        wrong_location = []
        
        for file_path, info in log_files.items():
            if info["in_logs_dir"]:
                correct_location.append((file_path, info))
            else:
                # Check if it should be excluded
                if not any(file_path.startswith(excluded) for excluded in self.excluded_files):
                    wrong_location.append((file_path, info))
        
        # Display correctly placed files
        if correct_location:
            print(f"\n✅ Files in correct location (logs/):")
            for file_path, info in correct_location:
                size_mb = info["size"] / (1024 * 1024)
                print(f"   📄 {file_path:<30} {size_mb:>6.2f} MB  {info['modified'].strftime('%Y-%m-%d %H:%M')}")
        
        # Display misplaced files
        if wrong_location:
            print(f"\n⚠️  Files that should be moved to logs/:")
            for file_path, info in wrong_location:
                size_mb = info["size"] / (1024 * 1024)
                print(f"   📄 {file_path:<30} {size_mb:>6.2f} MB  {info['modified'].strftime('%Y-%m-%d %H:%M')}")
        
        # Display excluded files (for reference)
        excluded_found = []
        for file_path, info in log_files.items():
            if any(file_path.startswith(excluded) for excluded in self.excluded_files):
                excluded_found.append((file_path, info))
        
        if excluded_found:
            print(f"\n📁 Files in correct location (not logs/):")
            for file_path, info in excluded_found:
                size_mb = info["size"] / (1024 * 1024)
                reason = next((desc for pattern, desc in self.excluded_files.items() if file_path.startswith(pattern)), "")
                print(f"   📄 {file_path:<30} {size_mb:>6.2f} MB  {reason}")

    def organize_log_files(self):
        """Move misplaced log files to the logs directory."""
        print("🔧 Organizing log files...")
        
        log_files = self.find_all_log_files()
        moved_count = 0
        
        for file_path, info in log_files.items():
            if not info["in_logs_dir"]:
                # Check if it should be excluded
                if any(file_path.startswith(excluded) for excluded in self.excluded_files):
                    continue  # Skip excluded files
                
                source_path = info["path"]
                filename = source_path.name
                dest_path = self.logs_dir / filename
                
                try:
                    # Handle filename conflicts
                    if dest_path.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        name_parts = filename.rsplit(".", 1)
                        if len(name_parts) == 2:
                            new_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                        else:
                            new_filename = f"{filename}_{timestamp}"
                        dest_path = self.logs_dir / new_filename
                        print(f"   ⚠️  Renamed to avoid conflict: {new_filename}")
                    
                    shutil.move(str(source_path), str(dest_path))
                    print(f"   ✅ Moved: {file_path} → logs/{dest_path.name}")
                    moved_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed to move {file_path}: {e}")
        
        if moved_count == 0:
            print("   👍 All log files are already in the correct location!")
        else:
            print(f"\n✅ Moved {moved_count} files to logs/ directory")

    def clean_old_logs(self, days=7):
        """Clean up old log files."""
        print(f"🧹 Cleaning log files older than {days} days...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = self.find_all_log_files()
        removed_count = 0
        total_size_freed = 0
        
        for file_path, info in log_files.items():
            if info["modified"] < cutoff_date:
                # Don't remove the main logs, only rotated/backup logs
                if any(pattern in file_path for pattern in [".log.", "_backup", "_old"]):
                    try:
                        file_size = info["size"]
                        info["path"].unlink()
                        print(f"   🗑️  Removed: {file_path} ({file_size / 1024:.1f} KB)")
                        removed_count += 1
                        total_size_freed += file_size
                    except Exception as e:
                        print(f"   ❌ Failed to remove {file_path}: {e}")
        
        if removed_count == 0:
            print("   👍 No old log files to clean up!")
        else:
            print(f"\n✅ Removed {removed_count} old files, freed {total_size_freed / (1024*1024):.2f} MB")

    def show_status(self):
        """Show detailed status of logging system."""
        print("📊 Voice Assistant Logging System Status")
        print("=" * 50)
        
        # Check if logs directory exists
        print(f"📁 Logs directory: {self.logs_dir}")
        print(f"   Exists: {'✅ Yes' if self.logs_dir.exists() else '❌ No'}")
        
        if self.logs_dir.exists():
            print(f"   Permissions: {oct(self.logs_dir.stat().st_mode)[-3:]}")
        
        # Check log files
        log_files = self.find_all_log_files()
        total_size = sum(info["size"] for info in log_files.values())
        
        print(f"\n📈 Statistics:")
        print(f"   Total log files: {len(log_files)}")
        print(f"   Total size: {total_size / (1024*1024):.2f} MB")
        
        # Show expected vs actual files
        print(f"\n📋 Expected log files:")
        for pattern, description in self.log_patterns.items():
            matching_files = [f for f in log_files.keys() if self._matches_pattern(f, pattern)]
            status = "✅ Found" if matching_files else "⚠️  Missing"
            print(f"   {pattern:<20} {status:<10} {description}")
            for match in matching_files[:3]:  # Show first 3 matches
                print(f"      └─ {match}")
        
        print(f"\n🔧 Recommendations:")
        misplaced = sum(1 for info in log_files.values() if not info["in_logs_dir"])
        if misplaced > 0:
            print(f"   • Run --organize to move {misplaced} misplaced files")
        
        old_files = sum(1 for info in log_files.values() 
                       if info["modified"] < datetime.now() - timedelta(days=7))
        if old_files > 0:
            print(f"   • Run --clean to remove {old_files} old files")
        
        if misplaced == 0 and old_files == 0:
            print("   • Logging system is well organized! 👍")

    def _matches_pattern(self, filename, pattern):
        """Check if filename matches a pattern (simple glob-like matching)."""
        if "*" not in pattern:
            return filename == pattern
        
        # Simple wildcard matching
        parts = pattern.split("*")
        if len(parts) == 2:
            return filename.startswith(parts[0]) and filename.endswith(parts[1])
        
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Voice Assistant Log Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--check", action="store_true", 
                       help="Check current log files status")
    parser.add_argument("--organize", action="store_true",
                       help="Move misplaced log files to logs/ directory")
    parser.add_argument("--clean", action="store_true",
                       help="Clean up old log files (>7 days)")
    parser.add_argument("--status", action="store_true",
                       help="Show detailed logging system status")
    parser.add_argument("--days", type=int, default=7,
                       help="Days threshold for cleaning (default: 7)")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any([args.check, args.organize, args.clean, args.status]):
        parser.print_help()
        return
    
    log_manager = LogManager()
    
    if args.check:
        log_manager.check_log_files()
    
    if args.organize:
        log_manager.organize_log_files()
    
    if args.clean:
        log_manager.clean_old_logs(args.days)
    
    if args.status:
        log_manager.show_status()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to extract content of all files from config, docs, services directories,
their subfolders, and root folder into source_code.md file.
"""

import os
import glob
from pathlib import Path

def should_include_file(filepath):
    """Determine if a file should be included in the extraction."""
    # Skip binary files and common non-text files
    binary_extensions = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin', 
                        '.dat', '.db', '.sqlite', '.sqlite3', '.jpg', '.jpeg', 
                        '.png', '.gif', '.ico', '.mp3', '.wav', '.mp4', '.avi',
                        '.onnx', '.model', '.h5', '.pkl', '.pickle'}
    
    # Skip hidden files and directories
    if any(part.startswith('.') for part in filepath.split(os.sep)):
        return False
    
    # Skip specific files
    skip_files = {'.env', '.gitignore', 'extract_source_code.py', 'source_code.md', 'scen.md'}
    filename = os.path.basename(filepath)
    if filename in skip_files:
        return False
    
    # Skip specific directories
    skip_dirs = {'__pycache__', 'node_modules', '.git', 'logs', 'models', 'sounds', 'tests'}
    if any(skip_dir in filepath for skip_dir in skip_dirs):
        return False
    
    # Check file extension
    ext = Path(filepath).suffix.lower()
    if ext in binary_extensions:
        return False
    
    return True

def get_files_to_extract():
    """Get all files to extract from config, docs, services, and root."""
    files = []
    
    # Root directory files (excluding script itself)
    root_files = glob.glob('*')
    for file_path in root_files:
        if os.path.isfile(file_path) and file_path != 'extract_source_code.py' and file_path != 'source_code.md':
            if should_include_file(file_path):
                files.append(file_path)
    
    # Config directory and subdirectories
    for pattern in ['config/**/*', 'config/*']:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path) and should_include_file(file_path):
                files.append(file_path)
    
    # Docs directory and subdirectories
    for pattern in ['docs/**/*', 'docs/*']:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path) and should_include_file(file_path):
                files.append(file_path)
    
    # Services directory and subdirectories
    for pattern in ['services/**/*', 'services/*']:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path) and should_include_file(file_path):
                files.append(file_path)
    
    # Remove duplicates and sort
    return sorted(set(files))

def extract_file_content(filepath):
    """Extract content from a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def create_scen_file():
    """Create the scen.md file listing all files in mentioned folders with paths."""
    files = get_files_to_extract()
    
    with open('scen.md', 'w', encoding='utf-8') as f:
        f.write("# Project File Structure (SCEN)\n\n")
        f.write("This file lists all files in config, docs, services directories, their subfolders, and root folder.\n\n")
        f.write("## File Inventory\n\n")
        
        # Group files by directory
        root_files = []
        config_files = []
        docs_files = []
        services_files = []
        
        for file_path in files:
            if '/' not in file_path:
                root_files.append(file_path)
            elif file_path.startswith('config/'):
                config_files.append(file_path)
            elif file_path.startswith('docs/'):
                docs_files.append(file_path)
            elif file_path.startswith('services/'):
                services_files.append(file_path)
        
        # Root directory files
        if root_files:
            f.write("### Root Directory\n")
            for file_path in sorted(root_files):
                f.write(f"- `{file_path}`\n")
            f.write("\n")
        
        # Config directory files
        if config_files:
            f.write("### Config Directory\n")
            for file_path in sorted(config_files):
                f.write(f"- `{file_path}`\n")
            f.write("\n")
        
        # Docs directory files
        if docs_files:
            f.write("### Docs Directory\n")
            for file_path in sorted(docs_files):
                f.write(f"- `{file_path}`\n")
            f.write("\n")
        
        # Services directory files
        if services_files:
            f.write("### Services Directory\n")
            for file_path in sorted(services_files):
                f.write(f"- `{file_path}`\n")
            f.write("\n")
        
        f.write(f"\n**Total files: {len(files)}**\n")
    
    print(f"Successfully created scen.md with {len(files)} files listed")

def create_source_code_md():
    """Create the source_code.md file with all extracted content."""
    files = get_files_to_extract()
    
    with open('source_code.md', 'w', encoding='utf-8') as f:
        f.write("# Source Code Documentation\n\n")
        f.write("This file contains the complete source code extracted from the project.\n\n")
        f.write("## How to Read This File\n\n")
        f.write("1. **File Headers**: Each section starts with a header containing the file name and relative path\n")
        f.write("2. **Code Blocks**: All code is preserved in its original format with proper indentation\n")
        f.write("3. **Navigation**: Use the file path headers to quickly locate specific files\n")
        f.write("4. **Search**: Use Ctrl+F (or Cmd+F on Mac) to search for specific functions, classes, or keywords\n")
        f.write("5. **Structure**: Files are organized alphabetically by their relative paths\n\n")
        f.write("## File List\n\n")
        
        # Create a table of contents
        for file_path in files:
            f.write(f"- `{file_path}`\n")
        
        f.write("\n---\n\n")
        
        # Extract content from each file
        for file_path in files:
            f.write(f"## File: `{file_path}`\n\n")
            f.write(f"**Path:** `{file_path}`\n\n")
            f.write("```\n")
            content = extract_file_content(file_path)
            f.write(content)
            f.write("\n```\n\n")
            f.write("---\n\n")
    
    print(f"Successfully extracted {len(files)} files into source_code.md")

def main():
    """Main function to create both scen.md and source_code.md files."""
    print("Starting source code extraction...")
    
    # Create scen.md first (listing all files)
    print("Creating scen.md file...")
    create_scen_file()
    
    # Create source_code.md (with actual content)
    print("Creating source_code.md file...")
    create_source_code_md()
    
    print("Extraction completed successfully!")

if __name__ == "__main__":
    main()

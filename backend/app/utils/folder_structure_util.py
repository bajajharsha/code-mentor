import json
import os
from collections import defaultdict
from io import StringIO
import sys

def folder_struct_util(json_file_path="uploads/raw_dataset.json", exclude_dirs=None):
    """
    Generate folder structure as a string from file paths in a JSON file
    
    Args:
        json_file_path (str): Path to the JSON file containing file paths
        exclude_dirs (list): List of directory names to exclude (default: ['venv', 'node_modules', '.git', '__pycache__'])
    
    Returns:
        str: Formatted folder structure as a string
    """
    if exclude_dirs is None:
        exclude_dirs = ['venv', 'node_modules', '.git', '__pycache__']
    
    # Extract unique file paths
    unique_paths = extract_unique_file_paths(json_file_path, exclude_dirs)
    
    # Build tree structure
    tree = build_tree_from_paths(unique_paths)
    
    # Capture the output to a string
    old_stdout = sys.stdout
    string_buffer = StringIO()
    sys.stdout = string_buffer
    
    # Print the header and folder structure to the buffer
    print(f"Found {len(unique_paths)} unique file paths (excluding {', '.join(exclude_dirs)})\n")
    print("Folder Structure:")
    print_tree(tree)
    
    # Restore stdout and get the output string
    sys.stdout = old_stdout
    folder_structure = string_buffer.getvalue()
    
    return folder_structure

def is_excluded_path(file_path, exclude_dirs):
    """Check if the file path should be excluded"""
    path_parts = file_path.split('/')
    return any(excluded_dir in path_parts for excluded_dir in exclude_dirs)

def extract_unique_file_paths(json_file_path, exclude_dirs):
    """Extract unique file paths from the JSON file, excluding specified directories"""
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return [f"Error loading JSON file: {str(e)}"]
    
    unique_paths = set()
    
    # Handle different possible JSON structures
    if isinstance(data, list):
        # If it's a list of documents
        for item in data:
            if isinstance(item, dict):
                if 'file_path' in item:
                    file_path = item['file_path']
                    if not is_excluded_path(file_path, exclude_dirs):
                        unique_paths.add(file_path)
                elif 'metadata' in item and isinstance(item['metadata'], dict) and 'file_path' in item['metadata']:
                    file_path = item['metadata']['file_path']
                    if not is_excluded_path(file_path, exclude_dirs):
                        unique_paths.add(file_path)
    elif isinstance(data, dict):
        # If it's a dictionary with documents
        for key, item in data.items():
            if isinstance(item, dict):
                if 'file_path' in item:
                    file_path = item['file_path']
                    if not is_excluded_path(file_path, exclude_dirs):
                        unique_paths.add(file_path)
                elif 'metadata' in item and isinstance(item['metadata'], dict) and 'file_path' in item['metadata']:
                    file_path = item['metadata']['file_path']
                    if not is_excluded_path(file_path, exclude_dirs):
                        unique_paths.add(file_path)
    
    return sorted(list(unique_paths))

def build_tree_from_paths(paths):
    """Build a tree structure from a list of file paths"""
    tree = defaultdict(dict)
    
    for path in paths:
        parts = path.split('/')
        current = tree
        
        # Build the nested dictionary structure
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # Leaf/file node
                current[part] = None
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
    
    return tree

def print_tree(tree, indent=0, is_last=False, prefix=""):
    """Print the tree structure with visual indentation"""
    items = list(tree.items())
    
    for i, (name, subtree) in enumerate(items):
        is_last_item = i == len(items) - 1
        
        # Determine the connector and the next prefix
        if indent > 0:
            connector = "└── " if is_last_item else "├── "
        else:
            connector = ""
            
        next_prefix = prefix + ("    " if is_last_item else "│   ")
        
        # Print current node
        print(f"{prefix}{connector}{name}")
        
        # Recursively print children
        if subtree is not None:  # If not a leaf/file node
            print_tree(subtree, indent + 1, is_last_item, next_prefix)
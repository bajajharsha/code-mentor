import os
import sys

def generate_markdown_tree(directory, prefix=""):
    markdown = ""
    items = sorted(os.listdir(directory))
    
    excluded_items = {".env", "venv", ".git", "langfuse_tool", "__pycache__"}
    items = [item for item in items if item not in excluded_items]
    
    for i, item in enumerate(items):
        path = os.path.join(directory, item)
        is_last = i == len(items) - 1

        markdown += f"{prefix}{'└── ' if is_last else '├── '}{item}\n"
        
        if os.path.isdir(path):
            new_prefix = prefix + ("    " if is_last else "│   ")
            markdown += generate_markdown_tree(path, new_prefix)
    
    return markdown


if __name__ == '__main__':
    workspace_path = sys.argv[1]
    markdown_tree = f"# Workspace Structure\n\n```\n{generate_markdown_tree(workspace_path)}```"
    
    output_file = os.path.join(workspace_path, "workspace_structure.md")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown_tree)

    print("Workspace structure saved as workspace_structure.md")
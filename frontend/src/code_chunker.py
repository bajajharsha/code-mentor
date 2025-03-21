import os
import json
import ast
import re
import sys
from typing import Any, Generator
from pathlib import Path
from code_splitter import Language, TiktokenSplitter
from uuid import uuid4

class FunctionExtractor:

    @staticmethod    
    def extract_python_functions(file_path):
        """Extract functions from Python files."""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_source = ast.get_source_segment(content, node)
                    class_name = None
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef) and node in parent.body:
                            class_name = parent.name
                            break
                    
                    return {
                        'file_path': file_path,
                        'class_name': class_name,
                        'language': 'python',
                        'code': func_source
                    }
        except SyntaxError:
            FunctionExtractor._python_regex_fallback(content, file_path)
    
    @staticmethod
    def _python_regex_fallback(content, file_path):
        """Fallback to regex for Python files with syntax errors."""
        func_pattern = r'def\s+(\w+)\s*\(.*?\).*?:'
        for func_match in re.finditer(func_pattern, content, re.DOTALL):
            func_content = func_match.group(0)
            return {
                'file_path': file_path,
                'class_name': None,
                'language': 'python',
                'code': func_content
            }

def walk(dir: str, max_size: int) -> Generator[dict[str, Any], None, None]:
    splitter = TiktokenSplitter(Language.Python, max_size=max_size)
    
    for root, _, files in os.walk(dir):
        for file in files:
            # Only process Python files
            if not file.endswith(".py"):
                continue
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, dir)
            try:
                # First try reading the file as text to get lines
                with open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                try:
                    # Now try splitting the code
                    with open(file_path, mode="rb") as f:
                        code = f.read()
                        try:
                            chunks = splitter.split(code)
                            for chunk in chunks:
                                text = "\n".join(lines[chunk.start : chunk.end])
                                if text:
                                    yield {
                                        "_id" : str(uuid4()),
                                        "file_path": rel_path,
                                        "file_name": file,
                                        "start_line": chunk.start,
                                        "end_line": chunk.end,
                                        "text": text,
                                        "size": chunk.size,
                                    }
                        except RuntimeError as e:
                            print(f"Warning: Splitting issue with {file_path}: {e}")
                            # Try to handle the file as a single chunk if splitting fails
                            text = "\n".join(lines)
                            if text:
                                yield {
                                    "_id" : str(uuid4()),
                                    "file_path": rel_path,
                                    "file_name": file,
                                    "start_line": 0,
                                    "end_line": len(lines),
                                    "text": text,
                                    "size": len(code),
                                }
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
            except UnicodeDecodeError as e:
                print(f"Skipping file {file_path} due to encoding error: {e}")

def main():
    try:
        if len(sys.argv) != 3:
            print("Usage: python code_chunker.py <workspace_path> <output_path>")
            sys.exit(1)
            
        workspace_path = sys.argv[1]  # Get workspace directory from command-line argument
        output_path = sys.argv[2]     # Get output path from command-line argument
        print(f"Processing workspace at {workspace_path}")
        print(f"Output will be saved to {output_path}")
        
        if not os.path.exists(workspace_path):
            print(f"Error: Directory '{workspace_path}' does not exist")
            sys.exit(1)
            
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        max_chunk_size = 512  # Adjust as needed
        
        all_chunks = list(walk(workspace_path, max_chunk_size))
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=4, ensure_ascii=False)
            
        print(f"Processed {len(all_chunks)} chunks from {workspace_path}")
        print(f"Output saved to {output_path}")
    except Exception as e:
        print(f"Error in main execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
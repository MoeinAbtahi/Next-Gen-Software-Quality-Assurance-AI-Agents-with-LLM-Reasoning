import requests
import csv
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import pandas as pd

# Ask user for configuration
sonar_url = input("Enter the SonarQube URL (e.g., http://localhost:9000): ").strip()
api_token = input("Enter the SonarQube API token: ").strip()
project_key = input("Enter the SonarQube project key: ").strip()
project_root_path = input(r"Enter the full local path to your project root (e.g., C:/Users/.../DEV-Project): ").strip()
new_output_root_path = input(r"Enter the full new output root path (e.g., C:/Users/.../DEV-Project.Revised): ").strip()

# Extensions that support testing
testable_extensions = {
    ".js", ".jsx", ".ts", ".tsx",
    ".py", ".java", ".go", ".rb", ".php",
    ".cs", ".cpp", ".cxx", ".cc", ".c",
    ".kt", ".kts", ".swift", ".rs", ".mjs"
}

def get_test_location_and_name(file_path):
    file_path = file_path.replace("\\", "/")
    base_dir, file_name = os.path.split(file_path)
    name, ext = os.path.splitext(file_name)

    if not ext or name.startswith("."):
        return ("", "")

    ext = ext.lower()
    lang = ext[1:]  # e.g., '.py' -> 'py'

    # Determine language-specific conventions
    if ext == ".py":
        test_file_name = f"test_{name}.py"
        test_dir = base_dir.replace("/src/", "/tests/")
    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
        test_file_name = f"{name}.test{ext}"
        test_dir = os.path.join(base_dir, "__tests__")
    elif ext == ".java":
        test_file_name = f"{name}Test.java"
        test_dir = base_dir.replace("/main/", "/test/")
    elif ext == ".cs":
        test_file_name = f"{name}Tests.cs"
        test_dir = base_dir.replace("/src/", "/tests/")
    elif ext == ".go":
        test_file_name = f"{name}_test.go"
        test_dir = base_dir
    elif ext == ".cpp" or ext in {".cxx", ".cc", ".c"}:
        test_file_name = f"test_{name}{ext}"
        test_dir = os.path.join(base_dir, "tests")
    elif ext == ".php":
        test_file_name = f"{name}Test.php"
        test_dir = base_dir.replace("/src/", "/tests/")
    elif ext == ".kt" or ext == ".kts":
        test_file_name = f"{name}Test{ext}"
        test_dir = base_dir.replace("/src/", "/test/")
    elif ext == ".swift":
        test_file_name = f"{name}Tests.swift"
        test_dir = base_dir.replace("/Sources/", "/Tests/")
    elif ext == ".rs":
        test_file_name = f"{name}_test.rs"
        test_dir = base_dir.replace("/src/", "/tests/")
    else:
        # Fallback to a generic format
        test_file_name = f"{name}.test{ext}"
        test_dir = os.path.join(base_dir, "__tests__")

    test_path = os.path.join(test_dir, test_file_name).replace("\\", "/")
    return (test_path, test_file_name)

# def get_test_location_and_name(file_path):
#     file_path = file_path.replace("\\", "/")
#     base_dir, file_name = os.path.split(file_path)
#     name, ext = os.path.splitext(file_name)

#     if not ext and not name.startswith("."):
#         return ("", "")

#     if ext.lower() in testable_extensions:
#         test_dir = os.path.join(base_dir, "__tests__").replace("\\", "/")
#         test_file_name = f"{name}.test{ext}"
#         test_path = os.path.join(test_dir, test_file_name).replace("\\", "/")
#         return (test_path, test_file_name)

#     return ("", "")

# Fetch all unresolved issues from SonarQube
def get_all_issues(project_key):
    page_size = 500
    page_number = 1
    all_issues = []

    while True:
        url = f"{sonar_url}/api/issues/search"
        params = {
            'componentKeys': project_key,
            'resolved': 'false',
            'ps': page_size,
            'p': page_number
        }
        token = base64.b64encode(f"{api_token}:".encode('utf-8')).decode('utf-8')
        headers = {
            'Authorization': f'Basic {token}'
        }

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        issues = data.get('issues', [])
        if not issues:
            break

        all_issues.extend(issues)
        page_number += 1

        if len(issues) < page_size:
            break

    return all_issues

# Compute the full original file path
def modify_file_path(original_path, project_key, project_root):
    relative_path = original_path.replace(f"{project_key}:", "")
    modified_path = relative_path.replace(':', '').replace('\\', '/').replace('//', '/')
    full_path = os.path.normpath(os.path.join(project_root, modified_path)).replace('\\', '/')
    return full_path

# Replace the original root with the new root, keeping the relative path
def compute_output_location(original_path, original_root, new_root):
    original_path = os.path.normpath(original_path).replace('\\', '/')
    original_root = os.path.normpath(original_root).replace('\\', '/')
    new_root = os.path.normpath(new_root).replace('\\', '/')

    if original_path.startswith(original_root):
        relative_part = original_path[len(original_root):].lstrip('/')
        return f"{new_root}/{relative_part}".replace('//', '/')
    else:
        return original_path  # fallback if root doesn't match

# Save the issues data to a CSV file
def save_csv_with_output_location(issues, file_path, project_key, project_root, new_output_root):
    issue_data = []
    for issue in issues:
        original_path = modify_file_path(issue['component'], project_key, project_root)
        output_path = compute_output_location(original_path, project_root, new_output_root)
        test_path, test_name = get_test_location_and_name(output_path)

        issue_data.append({
            'file_Location': original_path,
            'file_name': os.path.basename(issue['component']),
            'line': issue.get('line', 'N/A'),
            'message': issue['message'],
            'type': issue['type'],
            'output_location': output_path,
            'test_location': test_path,
            'test_file_name': test_name
        })

    issue_data.sort(key=lambda x: x['file_Location'])

    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['file_Location', 'file_name', 'line', 'message', 'type', 'output_location', 'test_location', 'test_file_name'])
        writer.writeheader()
        writer.writerows(issue_data)

# Main execution
root = tk.Tk()
root.withdraw()

all_issues = get_all_issues(project_key)
csv_file = filedialog.asksaveasfilename(
    title="Save final CSV with output and test paths",
    defaultextension=".csv",
    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
)

if csv_file:
    save_csv_with_output_location(all_issues, csv_file, project_key, project_root_path, new_output_root_path)
    print(f"Final CSV saved with output and test locations to {csv_file}")
else:
    print("Save operation cancelled.")
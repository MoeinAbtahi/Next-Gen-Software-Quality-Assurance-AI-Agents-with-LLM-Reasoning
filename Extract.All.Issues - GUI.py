import requests
import csv
import base64
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# Extensions that support testing
TESTABLE_EXTENSIONS = {
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

#     if ext.lower() in TESTABLE_EXTENSIONS:
#         test_dir = os.path.join(base_dir, "__tests__").replace("\\", "/")
#         test_file_name = f"{name}.test{ext}"
#         test_path = os.path.join(test_dir, test_file_name).replace("\\", "/")
#         return (test_path, test_file_name)

#     return ("", "")

def get_all_issues(sonar_url, api_token, project_key):
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
        headers = {'Authorization': f'Basic {token}'}

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

def modify_file_path(original_path, project_key, project_root):
    relative_path = original_path.replace(f"{project_key}:", "")
    modified_path = relative_path.replace(':', '').replace('\\', '/').replace('//', '/')
    full_path = os.path.normpath(os.path.join(project_root, modified_path)).replace('\\', '/')
    return full_path

def compute_output_location(original_path, original_root, new_root):
    original_path = os.path.normpath(original_path).replace('\\', '/')
    original_root = os.path.normpath(original_root).replace('\\', '/')
    new_root = os.path.normpath(new_root).replace('\\', '/')

    if original_path.startswith(original_root):
        relative_part = original_path[len(original_root):].lstrip('/')
        return f"{new_root}/{relative_part}".replace('//', '/')
    else:
        return original_path

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
        writer = csv.DictWriter(file, fieldnames=[
            'file_Location', 'file_name', 'line', 'message', 'type',
            'output_location', 'test_location', 'test_file_name'])
        writer.writeheader()
        writer.writerows(issue_data)

class SonarApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SonarQube Issues Exporter")
        self.geometry("600x350")
        self.resizable(False, False)

        # Input fields
        self._create_widgets()

    def _create_widgets(self):
        pady = 6

        tk.Label(self, text="SonarQube URL:").grid(row=0, column=0, sticky='e', padx=10, pady=pady)
        self.url_entry = tk.Entry(self, width=50)
        self.url_entry.grid(row=0, column=1, padx=10, pady=pady)
        self.url_entry.insert(0, "http://localhost:9099")

        tk.Label(self, text="API Token:").grid(row=1, column=0, sticky='e', padx=10, pady=pady)
        self.token_entry = tk.Entry(self, width=50, show='*')
        self.token_entry.grid(row=1, column=1, padx=10, pady=pady)

        tk.Label(self, text="Project Key:").grid(row=2, column=0, sticky='e', padx=10, pady=pady)
        self.key_entry = tk.Entry(self, width=50)
        self.key_entry.grid(row=2, column=1, padx=10, pady=pady)

        tk.Label(self, text="Project Root Folder:").grid(row=3, column=0, sticky='e', padx=10, pady=pady)
        self.project_root_entry = tk.Entry(self, width=50)
        self.project_root_entry.grid(row=3, column=1, padx=10, pady=pady)
        tk.Button(self, text="Browse...", command=self.browse_project_root).grid(row=3, column=2, padx=5)

        tk.Label(self, text="New Output Root Folder:").grid(row=4, column=0, sticky='e', padx=10, pady=pady)
        self.output_root_entry = tk.Entry(self, width=50)
        self.output_root_entry.grid(row=4, column=1, padx=10, pady=pady)
        tk.Button(self, text="Browse...", command=self.browse_output_root).grid(row=4, column=2, padx=5)

        # Action Button
        tk.Button(self, text="Fetch & Export CSV", command=self.fetch_and_export).grid(row=5, column=1, pady=20)

    def browse_project_root(self):
        folder = filedialog.askdirectory(title="Select Project Root Folder")
        if folder:
            self.project_root_entry.delete(0, tk.END)
            self.project_root_entry.insert(0, folder)

    def browse_output_root(self):
        folder = filedialog.askdirectory(title="Select New Output Root Folder")
        if folder:
            self.output_root_entry.delete(0, tk.END)
            self.output_root_entry.insert(0, folder)

    def fetch_and_export(self):
        sonar_url = self.url_entry.get().strip()
        api_token = self.token_entry.get().strip()
        project_key = self.key_entry.get().strip()
        project_root = self.project_root_entry.get().strip()
        new_output_root = self.output_root_entry.get().strip()

        if not all([sonar_url, api_token, project_key, project_root, new_output_root]):
            messagebox.showerror("Error", "Please fill all fields.")
            return

        try:
            all_issues = get_all_issues(sonar_url, api_token, project_key)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch issues:\n{e}")
            return

        save_path = filedialog.asksaveasfilename(
            title="Save final CSV with output and test paths",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if not save_path:
            messagebox.showinfo("Cancelled", "Save operation cancelled.")
            return

        try:
            save_csv_with_output_location(all_issues, save_path, project_key, project_root, new_output_root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV:\n{e}")
            return

        messagebox.showinfo("Success", f"Final CSV saved successfully:\n{save_path}")

if __name__ == "__main__":
    app = SonarApp()
    app.mainloop()

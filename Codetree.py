import os
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python print_project_tree.py <csv_file_path>")
    sys.exit(1)

csv_file_path = sys.argv[1]

# Derive the project root by removing the CSV file part
project_root = os.path.dirname(csv_file_path)

def generate_tree(root_dir):
    tree = {
        "name": os.path.basename(os.path.abspath(root_dir)),
        "type": "directory",
        "children": []
    }

    try:
        items = sorted(os.listdir(root_dir))
    except PermissionError:
        print(f"Permission denied: {root_dir}")
        return tree

    for item in items:
        item_path = os.path.join(root_dir, item)
        node = {"name": item}

        if os.path.isdir(item_path):
            node["type"] = "directory"
            node["children"] = generate_tree(item_path)["children"]
        else:
            node["type"] = "file"

        tree["children"].append(node)

    return tree

def print_tree_json(root_dir):
    tree_structure = generate_tree(root_dir)
    print(json.dumps(tree_structure, indent=2))

# Generate and print the tree
print_tree_json(project_root)

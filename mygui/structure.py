import os

# Folders to ignore
EXCLUDE_FOLDERS = {"Scripts", "__pycache__", "venv", "build", "dist","other codes","typings","Lib"}

def print_tree(folder, indent=""):
    for item in sorted(os.listdir(folder)):
        path = os.path.join(folder, item)

        if item in EXCLUDE_FOLDERS:
            continue

        print(indent + "|-- " + item)

        if os.path.isdir(path):
            print_tree(path, indent + "    ")

# Start from current directory
print_tree(".")
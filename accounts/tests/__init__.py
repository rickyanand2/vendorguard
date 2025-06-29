import os

# Create directory and file structure for modular tests
base_dir = "/mnt/data/accounts/tests"
file_structure = {
    "test_registration.py": "",
    "test_login_logout.py": "",
    "test_profile_view.py": "",
    "test_team_management.py": "",
    "__init__.py": "",
}

# Create files
os.makedirs(base_dir, exist_ok=True)
for file_name, content in file_structure.items():
    with open(os.path.join(base_dir, file_name), "w") as f:
        f.write(content)

"Created test structure under accounts/tests"

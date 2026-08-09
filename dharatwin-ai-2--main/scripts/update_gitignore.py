import os

rules = ['.env', '.env.*', '!.env.example', '__pycache__/', '*.py[cod]', '*.pyo', '.venv/', 'venv/', 'env/', 'node_modules/', '.next/', 'out/', 'dist/', 'build/', '*.log', '*.sqlite', '*.sqlite3', '*.db', 'coverage/', '.pytest_cache/', '.vscode/', '.idea/', '.DS_Store', 'Thumbs.db', '*.pem', '*.key']

try:
    with open('.gitignore', 'r') as f:
        content = f.read()
except FileNotFoundError:
    content = ""

append = []
for req in rules:
    if req not in content:
        append.append(req)

if append:
    with open('.gitignore', 'a') as f:
        f.write('\n# Added for security\n' + '\n'.join(append) + '\n')
    print('Updated .gitignore with', append)
else:
    print('.gitignore already has all required rules.')

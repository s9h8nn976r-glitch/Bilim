import os
import py_compile

errors = []
for root, dirs, files in os.walk('.'):
    # skip virtualenv and .git directories
    if '.git' in root.split(os.sep) or 'venv' in root.split(os.sep) or '__pycache__' in root.split(os.sep):
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append((path, str(e)))

if not errors:
    print('OK: all .py files compiled successfully')
else:
    print('Found syntax errors in following files:')
    for p, msg in errors:
        print(f"--- {p} ---")
        print(msg)
    raise SystemExit(1)

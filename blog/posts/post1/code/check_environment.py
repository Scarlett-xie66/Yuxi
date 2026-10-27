"""Report missing dependencies before starting the analysis."""
import importlib
import importlib.metadata
import json
import sys

required = {"numpy": "numpy", "matplotlib": "matplotlib", "scikit-learn": "sklearn"}
errors = []
versions = {}
minimums = {"numpy": (1, 23), "matplotlib": (3, 6), "scikit-learn": (1, 2)}
if sys.version_info < (3, 10):
    errors.append("Python 3.10 or newer is required.")
for package, module in required.items():
    try:
        importlib.import_module(module)
        version = importlib.metadata.version(package)
        versions[package] = version
        major_minor = tuple(int(part) for part in version.split('.')[:2])
        if major_minor < minimums[package]:
            errors.append(package + " is too old: " + version)
    except Exception as exc:
        errors.append(package + ": " + str(exc))
print(json.dumps({"python": sys.executable, "versions": versions, "errors": errors}, indent=2))
sys.exit(1 if errors else 0)

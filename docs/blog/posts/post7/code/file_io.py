"""Preserve modification times for unchanged generated resources during preview."""
from pathlib import Path

def write_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode('utf-8')
    write_bytes(path, data)

def write_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)

def write_csv(path, frame):
    write_text(path, frame.to_csv(index=False, lineterminator='\n'))

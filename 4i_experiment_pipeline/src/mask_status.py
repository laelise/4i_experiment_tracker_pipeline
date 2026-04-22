"""
mask_status.py
--------------
Tracks which wells have completed masks so the plate selector can gray them out.
Status is stored in {base_dir}/masks/mask_status.json.
"""

import json
import os


def _status_path(base_dir):
    return os.path.join(base_dir, 'masks', 'mask_status.json')


def get_masked_wells(base_dir):
    """Return a set of well names that already have saved masks."""
    path = _status_path(base_dir)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return set(data.get('masked_wells', []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def mark_well_masked(well, base_dir):
    """Add well to the mask status file (creates the file if needed)."""
    masked = get_masked_wells(base_dir)
    masked.add(well)
    path = _status_path(base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'masked_wells': sorted(masked)}, f, indent=2)


def unmark_well_masked(well, base_dir):
    """Remove a well from the mask status (useful if a mask needs to be redone)."""
    masked = get_masked_wells(base_dir)
    masked.discard(well)
    path = _status_path(base_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'masked_wells': sorted(masked)}, f, indent=2)

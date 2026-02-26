import os
from pathlib import Path
from typing import List, Dict

def create_download_sh(root_dir: str) -> Dict[str, List[str]]:
    """
    Scan ``root_dir`` for subdirectories that represent season folders and ensure
    each contains an executable ``download.sh`` script.

    The function looks for any immediate child directory whose name contains the
    word ``season`` (case‑insensitive). If a ``download.sh`` file is already present
    inside the directory it is left untouched.

    For each missing file a minimal bash script is created:

        #!/usr/bin/env bash
        # Auto‑generated download script for {{season_folder}}
        echo "Add your download commands here"

    The created file is made executable (chmod +x).

    Returns
    -------
    dict
        {
            "created": [str, ...],   # paths of files that were created
            "skipped": [str, ...]   # season folder names that already had a download.sh
        }

    Raises
    ------
    FileNotFoundError
        If ``root_dir`` does not exist or is not a directory.
    """
    path = Path(root_dir).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"{root_dir!r} does not exist or is not a directory")

    created: List[str] = []
    skipped: List[str] = []

    for child in path.iterdir():
        if not child.is_dir():
            continue
        # Consider it a season folder if the name contains "season" (case‑insensitive)
        if "season" not in child.name.lower():
            continue

        script_path = child / "download.sh"
        if script_path.exists():
            skipped.append(str(child))
            continue

        # Write a basic stub script
        script_content = """#!/usr/bin/env bash
# Auto‑generated download script for {folder}
echo \"Add your download commands here\"
""".format(folder=child.name)

        script_path.write_text(script_content, encoding="utf-8")
        # Make it executable
        script_path.chmod(script_path.stat().st_mode | 0o111)

        created.append(str(script_path))

    return {"created": created, "skipped": skipped}

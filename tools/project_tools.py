import os
import subprocess
from pathlib import Path


def setup_project(project_name: str, description: str) -> str:
    """Create a new project folder under ~/dev, initialise git, copy templates,
    and populate specs.md with the project name and description.

    Returns the absolute path of the created project.
    """
    project_path = Path.home() / "dev" / project_name
    project_path.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init"], cwd=project_path, check=True)

    templates = Path.home() / "vimwiki" / "templates" / "project"
    if templates.exists():
        subprocess.run(f"cp -r {templates}/. {project_path}/", shell=True, check=True)

    specs = project_path / "specs.md"
    specs.write_text(f"## {project_name}\n{description}\n")

    return f"Project ready at {project_path}"

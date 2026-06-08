import os
import json
import hashlib
from datetime import datetime
from src.config import OUTPUT_DIR

_run_folders: dict[str, str] = {}

def get_output_folder(email_content: str) -> str:
    """Returns a consistent output folder for all files in a single workflow run."""
    if email_content not in _run_folders:
        email_hash = hashlib.md5(email_content.encode('utf-8')).hexdigest()[:10]
        folder_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{email_hash}"
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        _run_folders[email_content] = folder_path
    return _run_folders[email_content]

def generate_folder_name(email_content: str) -> str:
    """Generates a folder name based on the email content."""
    return os.path.basename(get_output_folder(email_content))

def write_markdown_file(content: str, filename: str, email_content: str) -> None:
    """Writes content to a markdown file inside a dynamically created folder."""
    folder_path = get_output_folder(email_content)

    with open(f"{folder_path}/{filename}.md", "w") as f:
        f.write(content)

    print(f"Generated response saved in: {folder_path}/{filename}.md")

def write_triage_metadata(metadata: dict, email_content: str) -> None:
    """Writes triage metadata as JSON in the same per-run output folder."""
    folder_path = get_output_folder(email_content)
    metadata_with_timestamp = {**metadata, "timestamp": datetime.now().isoformat()}

    with open(f"{folder_path}/triage_metadata.json", "w") as f:
        json.dump(metadata_with_timestamp, f, indent=2)

    print(f"Triage metadata saved in: {folder_path}/triage_metadata.json")

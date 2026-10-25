"""Build dist/robot_wars_student_kit.zip to hand out to students."""

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOP = "robot_wars_kit"


def add_folder(zf, folder):
    for path in sorted((ROOT / folder).rglob("*.py")):
        if "__pycache__" not in path.parts:
            zf.write(path, f"{TOP}/{path.relative_to(ROOT)}")


def main():
    out = ROOT / "dist" / "robot_wars_student_kit.zip"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in ("engine", "viewer", "examples"):
            add_folder(zf, folder)
        for path in sorted((ROOT / "student_kit").iterdir()):
            if path.is_file():
                zf.write(path, f"{TOP}/{path.name}")
        zf.write(ROOT / "requirements.txt", f"{TOP}/requirements.txt")
    print(f"Built {out}")


if __name__ == "__main__":
    main()

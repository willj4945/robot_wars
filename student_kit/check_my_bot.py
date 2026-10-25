"""Check your robot is ready to hand in.

    python check_my_bot.py my_bot.py
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in (HERE, HERE.parent):
    if (folder / "engine").is_dir():
        sys.path.insert(0, str(folder))
        break

from engine.checker import check_bot, print_report  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python check_my_bot.py my_bot.py")
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Can't find {path}. Is it in this folder?")
        sys.exit(2)

    print("Testing your robot against every example bot. This takes a few seconds...")
    if print_report(path, check_bot(path)):
        print(f"🎉 Ready to submit! Send {path.name} to your teacher.\n")
    else:
        print("Fix the ❌ problems above, then run this check again.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

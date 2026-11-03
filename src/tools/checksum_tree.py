"""Record / verify SHA-256 checksums of a folder (used to prove hgrtool-local/ is never modified).

    python checksum_tree.py write  <folder> <manifest>
    python checksum_tree.py check  <folder> <manifest>      (exit 1 on any difference)
"""

import hashlib
import sys
from pathlib import Path


def scan(folder: Path) -> dict:
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob("*")) if p.is_file()
    }


def main(argv) -> int:
    if len(argv) != 4 or argv[1] not in ("write", "check"):
        print(__doc__)
        return 2
    mode, folder, manifest = argv[1], Path(argv[2]), Path(argv[3])
    current = scan(folder)
    if mode == "write":
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("".join(f"{h}  {n}\n" for n, h in current.items()), encoding="utf-8")
        print(f"checksummed {len(current)} files in {folder}")
        return 0
    recorded = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        h, _, n = line.partition("  ")
        recorded[n] = h
    changed = sorted(n for n in set(recorded) | set(current) if recorded.get(n) != current.get(n))
    if changed:
        print("ERROR: upstream folder changed:", *changed, sep="\n  ")
        return 1
    print(f"OK: {folder} unchanged ({len(current)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Synchronize checked generated web files locally; never commits or pushes."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "_build" / "build"))
from site_common import DEFAULT_SITE, SOURCES, safe_destination, validate_manifest
from test_site import static_checks


def sync(site, dry_run=False):
    site = safe_destination(site)
    if not (site / ".raschet-build").is_file():
        raise ValueError("Refusing non-generated output without .raschet-build")
    manifest = validate_manifest(json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8")))
    errors = static_checks(site, SOURCES)
    if errors:
        raise ValueError("Refusing failed build: " + "; ".join(errors))
    paths = [p["path"] for p in manifest["pages"]]
    paths += [p["path"] for p in manifest["redirects"]] + manifest["static"]
    paths += ["CNAME", ".nojekyll", "robots.txt", "sitemap.xml", "manifest.webmanifest", "sw.js"]
    if (site / "llms.txt").is_file():
        paths.append("llms.txt")
    paths += [p.relative_to(site).as_posix() for p in sorted((site / "assets").rglob("*")) if p.is_file()]
    plan = []
    for rel in paths:
        source = (site / rel).resolve()
        target = (ROOT / rel).resolve()
        if site not in source.parents or ROOT not in target.parents:
            raise ValueError("Refusing escaped source/destination: " + rel)
        data = source.read_bytes()
        if not target.is_file() or target.read_bytes() != data:
            plan.append((rel, target, data))
    # All paths/content are preflighted before the first target write. Do not
    # remove unknown public files, sources, backend files or user artifacts.
    if not dry_run:
        for rel, target, data in plan:
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary = tempfile.mkstemp(prefix=".raschet-sync-", dir=target.parent)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(data)
                os.replace(temporary, target)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
    print("Local generated files", "planned:" if dry_run else "synchronized:", len(plan))
    return [rel for rel, target, data in plan]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=DEFAULT_SITE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sync(args.site, args.dry_run)


if __name__ == "__main__":
    main()

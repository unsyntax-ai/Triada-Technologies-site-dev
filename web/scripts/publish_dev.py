"""Publish a snapshot of the site to the DEV repo, for testing before anything reaches the live site.

Usage:  python scripts/publish_dev.py [area] [git-ref]
        area     "web" (default) or "mobile": which part of the dev site to update
        git-ref  the commit to publish (default: HEAD)

The dev site has one folder per area, so two sessions never overwrite each other:
    .../Triada-Technologies-site-dev/web/      the website work
    .../Triada-Technologies-site-dev/mobile/   the phone work
and a small front page at the root that links to both.

What it does to the snapshot, and why:
  * takes the tracked files of the given commit (nothing untracked),
  * drops CNAME, so the dev copy never claims the live domain triadatechnologies.com,
  * drops .github (the daily-insight workflow runs on the live repo only),
  * marks every page noindex and makes robots.txt disallow everything, so search engines ignore the dev copy,
  * replaces only its own area folder in the dev repo and pushes. The other area is left alone.
The live repo (origin) is never touched by this script.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

DEV_REMOTE = "https://github.com/unsyntax-ai/Triada-Technologies-site-dev.git"
DEV_URL = "https://unsyntax-ai.github.io/Triada-Technologies-site-dev"
AREAS = ("web", "mobile")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOINDEX = '<meta name="robots" content="noindex, nofollow">'
FRONT = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
""" + NOINDEX + """
<title>Triada dev site</title>
<style>body{font-family:system-ui,sans-serif;max-width:560px;margin:12vh auto;padding:0 20px;color:#111}
a{display:block;margin:12px 0;padding:16px 18px;border:1px solid #ccd;border-radius:12px;text-decoration:none;color:#1E3A8A;font-weight:600}
small{display:block;color:#667;font-weight:400;margin-top:4px}</style></head><body>
<h1>Triada dev site</h1><p>Testing copies. Nothing here is the live website.</p>
<a href="web/">Website (desktop)<small>latest web work in testing</small></a>
<a href="mobile/">Mobile<small>latest phone work in testing</small></a>
</body></html>
"""


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main():
    args = sys.argv[1:]
    area = args.pop(0) if args and args[0] in AREAS else "web"
    ref = args[0] if args else "HEAD"
    sha = run("git", "rev-parse", "--short", ref, cwd=ROOT)
    work = tempfile.mkdtemp(prefix="triada-dev-")
    try:
        # the snapshot of the chosen commit
        archive = os.path.join(work, "src.tar")
        run("git", "archive", "--format=tar", "-o", archive, ref, cwd=ROOT)
        snap = os.path.join(work, "snap")
        os.makedirs(snap)
        run("tar", "-xf", archive, "-C", snap)
        if os.path.exists(os.path.join(snap, "CNAME")):
            os.remove(os.path.join(snap, "CNAME"))
        shutil.rmtree(os.path.join(snap, ".github"), ignore_errors=True)
        with open(os.path.join(snap, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("User-agent: *\nDisallow: /\n")
        pages = 0
        for name in os.listdir(snap):
            if not name.endswith(".html"):
                continue
            path = os.path.join(snap, name)
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read()
            if NOINDEX not in text:
                text = re.sub(r"(<head[^>]*>)", r"\1\n" + NOINDEX, text, count=1)
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(text)
                pages += 1

        # the dev repo as it is now
        dev = os.path.join(work, "dev")
        run("git", "clone", "-q", "--depth", "1", DEV_REMOTE, dev)
        run("git", "config", "user.name", "Triada dev publish", cwd=dev)
        run("git", "config", "user.email", "dev-publish@users.noreply.github.com", cwd=dev)

        # an old layout (the whole site at the root) is cleared out once; the area folders are kept
        if os.path.exists(os.path.join(dev, "about.html")):
            for name in os.listdir(dev):
                if name == ".git" or name in AREAS:
                    continue
                p = os.path.join(dev, name)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)

        # root: front page, robots, no Jekyll processing
        with open(os.path.join(dev, "index.html"), "w", encoding="utf-8", newline="\n") as f:
            f.write(FRONT)
        with open(os.path.join(dev, "robots.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("User-agent: *\nDisallow: /\n")
        open(os.path.join(dev, ".nojekyll"), "w").close()

        # only this area is replaced
        target = os.path.join(dev, area)
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(snap, target)

        run("git", "add", "-A", cwd=dev)
        if not run("git", "status", "--porcelain", cwd=dev):
            print(f"Dev {area} area already matches {sha}; nothing to publish.")
            return
        run("git", "commit", "-q", "-m", f"Dev {area}: snapshot of {sha}", cwd=dev)
        try:
            run("git", "push", "-q", "origin", "main", cwd=dev)
        except subprocess.CalledProcessError:
            # the other session published meanwhile: take its change in, then push again
            run("git", "pull", "-q", "--rebase", "origin", "main", cwd=dev)
            run("git", "push", "-q", "origin", "main", cwd=dev)
        print(f"Published {sha} to the dev site, area '{area}' ({pages} pages marked noindex).")
        print(f"Open: {DEV_URL}/{area}/")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()

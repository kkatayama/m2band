from pathlib import Path
import subprocess
import os

# GitHub Updates ##############################################################
profile = Path(os.path.expanduser('~'), '.zshrc').as_posix()
os.chdir(Path.cwd().as_posix())
cmds = [
    f"source {profile}",
    "git add -A",
    "git commit -am 'update database'",
    "git push origin main",
]
for cmd in cmds:
    print(cmd)

    out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(out.stdout.strip())
    print(out.stderr.strip())

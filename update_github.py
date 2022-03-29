import subprocess

# GitHub Updates ##############################################################
cmds = [
    "git add -A",
    "git commit -am 'update database'",
    "git push origin main",
]
for cmd in cmds:
    print(cmd)

    out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(out.stdout.strip())
    print(out.stderr.strip())

import subprocess

import django.utils.html


def run(cmd_list: list[str]) -> str:
    return subprocess.run(cmd_list, capture_output=True, encoding="utf-8").stdout


git_log = run(["git", "log", "-1", "--format=%h %cs"])
git_symbolic_ref = run(["git", "symbolic-ref", "HEAD"])

print(django.utils.html.escape(git_log), end="")
print(django.utils.html.escape(git_symbolic_ref), end="")

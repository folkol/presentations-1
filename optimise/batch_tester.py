import glob
import subprocess

for py in sorted(glob.glob("v*.py")):
    # ignore variants and refactorings
    if len(py) != 6:
        continue

    params = f"python3 tester.py -f {py} -t 600 -o times.csv -i 5 -e 5".split()
    subprocess.run(params)
    subprocess.run(params + ["-p", "pypy3"])

for file in sorted(glob.glob("v*.c")):
    exe = [f"{file}O0", f"{file}O3"]
    subprocess.run(["g++", file, "-o", exe[0], "-std=c++17"])
    subprocess.run(["g++", file, "-o", exe[1], "-std=c++17", "-O3"])

    for e in exe:
        subprocess.run("python3 tester.py"
                       f" -f {e} -t 600 -o times.csv -i 5 -e 5 -c 1".split())

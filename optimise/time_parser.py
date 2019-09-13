import pandas as pd
from math import log
from itertools import tee
from pprint import pprint

MAXN = 1048576
MAX_ITERS = 100000
FIRST = "v00.py"
ETA = "eta_MAX_iter"

df = pd.read_csv("times.csv").drop(columns=['machine', 'date'])
# get rows with tests > 1 second
df = df[(df.runtime >= 1)]  # FIXME: if the fastest is <1 but there are >1?
# group by "run type"
group_df = df.groupby(['file_name', 'maxN', 'entries', 'runner'])
# get the fastest of each run type only, slower times are overhead
min_dict = group_df.min().to_dict()["runtime"]

summary_dict = {v: {} for v in sorted(set(df["file_name"]))}

# TODO: I should probably look more into pandas ^_^U
for k, v in min_dict.items():
    if not summary_dict[k[0]].get(k[3]):
        summary_dict[k[0]][k[3]] = {}
    if k[2] == 1:
        if not summary_dict[k[0]][k[3]].get(1):
            summary_dict[k[0]][k[3]][1] = {}
        summary_dict[k[0]][k[3]][1][k[1]] = v
    else:
        assert k[1] == MAXN
        if not summary_dict[k[0]][k[3]].get(MAXN):
            summary_dict[k[0]][k[3]][MAXN] = {}
        summary_dict[k[0]][k[3]][MAXN][k[2]] = v

# Time size ratios for a single calculation of size N <= 1048576
tsr_lt = []

# Calculate time_size_ratio + ETAs
for k_file, v_file in summary_dict.items():
    for k_runner, v_runner in v_file.items():
        maxN_lt_MAX_k = sorted(v_runner.get(1, {}).keys())
        maxN_lt_MAX_v = sorted(v_runner.get(1, {}).values())
        if maxN_lt_MAX_k and maxN_lt_MAX_k[-1] < MAXN:
            small, big = tee(maxN_lt_MAX_k)
            next(big)
            for s, b in zip(small, big):
                assert(s * 2 == b)
            small, big = tee(maxN_lt_MAX_v)
            next(big)
            time_size_ratio = [b / s for s, b in zip(small, big)]
            tsr_lt += time_size_ratio
            v_runner["ts_ratio"] = sum(time_size_ratio) / len(time_size_ratio)
            v_runner["eta_MAXN"] = (MAXN / maxN_lt_MAX_k[-1])\
                ** log(v_runner["ts_ratio"], 2)\
                * maxN_lt_MAX_v[-1]
            v_runner["eta_MAXN_y"] = v_runner["eta_MAXN"] / 3600 / 24 / 365
            v_runner["eta_MAX_iter"] = v_runner["eta_MAXN"] * MAX_ITERS

        maxN_lt_MAX_v = sorted(v_runner.get(MAXN, {}).values())
        maxN_lt_MAX_k = sorted(v_runner.get(MAXN, {}).keys())
        if maxN_lt_MAX_k:
            v_runner["eta_MAXN"] = maxN_lt_MAX_v[0]  # better than an estimate
            small, big = tee(maxN_lt_MAX_k)
            next(big)
            for s, b in zip(small, big):
                assert(s * 10 == b)
            small, big = tee(sorted(v_runner.get(MAXN, {}).values()))
            next(big)
            time_size_ratio = [b / s for s, b in zip(small, big)]
            v_runner["ts_ratio"] = sum(time_size_ratio) / len(time_size_ratio)
            v_runner["eta_MAX_iter"] = (MAX_ITERS / maxN_lt_MAX_k[-1])\
                ** log(v_runner["ts_ratio"], 10)\
                * maxN_lt_MAX_v[-1]

speedups = {k: {} for k in summary_dict.keys()}
python_1st = summary_dict[FIRST]["python3"][ETA]
pypy_1st = summary_dict[FIRST]["pypy3"][ETA]

for k, v in speedups.items():
    python = summary_dict[k].get("python3", {}).get(ETA)
    pypy = summary_dict[k].get("pypy3", {}).get(ETA)
    if python and pypy:
        v["total_python3"] = python_1st / python
        v["total_pypy3"] = pypy_1st / pypy
        v["total_vs_python3_pypy3"] = python_1st / pypy
        v["vs_pypy3_python3"] = python / pypy

previous, current = tee(speedups.keys())
next(current)

for pre, cur in zip(previous, current):
    cur_python3 = summary_dict[cur].get("python3", {}).get(ETA)
    cur_pypy3 = summary_dict[cur].get("pypy3", {}).get(ETA)
    pre_python3 = summary_dict[pre].get("python3", {}).get(ETA)
    pre_pypy3 = summary_dict[pre].get("pypy3", {}).get(ETA)

    if cur_python3 and cur_pypy3:
        vs = speedups[cur]
        vs["prev_python3"] = pre_python3 / cur_python3
        vs["prev_pypy3"] = pre_pypy3 / cur_pypy3

print(" ------ CONSTANTS ------")
print(f"MAXN={MAXN}; MAX_ITERS={MAX_ITERS}")
print(" ------ TIMING SUMMARY ------")
pprint(summary_dict)
print(" ------ SPEEDUP SUMMARY ------")
pprint(speedups)

# Some assertions on time_size_ratios, just for fun
for tsr in tsr_lt:
    # Versions that follow this basic algorithm (v00-05) are O(n^3).
    assert(6.5 < tsr < 9)  # 2n -> 8x
    # Other paradigm algorithms are too fast to be here (<1s) on the machine I
    # ran (e.g. v06 is close to O(n)). Could happen on slower machines, so take
    # this assertion with a grain of salt, rather than a truth that must hold.


# TODO scripts to do for each csv timing:
#  - plotting charts?
#  - versions with C and different compiler optimisations

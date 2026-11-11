# Short Order scheduler — `mise_en_place`

A CPU scheduler for the Short Order kitchen simulator (Operating Systems project).
Cooks are cores, orders are processes, oven steps are I/O bursts, and stations
are counting semaphores. The engine calls `schedule(obs)` at every scheduling
point and the scheduler decides which order each cook works on.

**The submission is [`scheduler.py`](scheduler.py)** — one file, uploaded to
Moodle as `my-scheduler/scheduler.py`.

## Results

Mean over all nine marking profiles, on seed sets not used for tuning:

| Seed set | mise_en_place | gordon_ramsay |
| --- | ---: | ---: |
| 3000–3011 | 70.97 | 68.78 |
| 4000–4015 | 70.45 | 68.22 |

The local `function` profile differs from the one used for marking; see
[`docs/NOTES.md`](docs/NOTES.md) for the four variants it was tested against.

## How it works

1. **Never preempt.** Only a resumption after a preemption counts against the
   switching component, so a non-preemptive scheduler keeps all of it.
2. **Rank by slowdown weight.** Shortest weighted job first:
   `remaining work × span^0.5`, smallest first.
3. **Never start a lost cause.** An order that cannot finish before its deadline
   goes behind every order that still can.
4. **Choose the set, then map it onto cooks.** A reassigned cook hands back its
   station place inside the same decision, so the station arithmetic is exact.
5. **On `function`, sweep once.** Give every order one tick of work (response
   stops at the first tick), then settle into shortest-job-first.

The reasoning, the measured negative results and the open uncertainties are in
[`docs/NOTES.md`](docs/NOTES.md). The assignment itself is summarised in
[`docs/project-brief.pdf`](docs/project-brief.pdf).

## Reproducing the numbers

The course kit (engine, SDK and profiles) is not in this repo: it comes from the
course site's Downloads tab and is the course's to distribute. With the kit
unzipped:

1. Copy `scheduler.py` to `my-scheduler/scheduler.py` inside the kit.
2. Copy the three scripts in `tools/` into the kit's root folder.
3. From that folder:

```bash
./start.sh check my-scheduler                                # the marker's acceptance checks
python3 bench.py my-scheduler/scheduler.py --seeds 3000..3012  # mark over all nine profiles
python3 diag.py my-scheduler/scheduler.py --vs gordon_ramsay   # component breakdown
python3 sweep.py my-scheduler/scheduler.py --set GAMMA=0.5,0.75,1.0 --detail
```

On Windows use `.\START.cmd check my-scheduler`, and download the Windows build
of the kit: the Linux build will not load there.

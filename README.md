# Short Order Scheduler

A non-preemptive, slowdown-weighted CPU scheduler for the **Short Order** kitchen
simulator, built for an Operating Systems course project.

In Short Order, a restaurant kitchen stands in for an operating system. Cooks
are CPU cores, orders are processes, a recipe's work steps are CPU bursts, its
oven steps are I/O bursts, and kitchen stations are counting semaphores with a
fixed number of places. Every customer has a patience deadline. The engine calls
`schedule(obs)` at every scheduling point, and the scheduler decides which order
each cook works on next.

**The submission is [`scheduler.py`](scheduler.py)**: one self-contained file,
uploaded as `my-scheduler/scheduler.py`.

## Results

Mark = mean over all nine marking profiles of the mean score per profile, measured
locally on seed sets that were not used for tuning:

| Seeds | `mise_en_place` | `gordon_ramsay` (strongest reference) | `julia_child` (SJF) |
| --- | ---: | ---: | ---: |
| 3000–3011 | **70.97** | 68.78 | 66.94 |
| 4000–4015 | **70.45** | 68.22 | — |

Every decision takes well under a millisecond (the limit is 50 ms), with zero
rejected assignments and zero exceptions on every profile tested.

The `function` profile used for marking differs from the one shipped in the kit:
it has 15 orders that arrive over time rather than all at once. The scheduler was
tested against four arrival patterns built to match it, and scored 17 to 18 points
above `gordon_ramsay` on each.

## How it works

1. **Never preempt.** The switching component only penalises resuming an order
   after a preemption. Returning from the oven, or resuming after a station bump,
   starts a fresh work step and is free. A scheduler that never preempts keeps the
   whole component, which is why SJF beats SRTF on this kitchen.
2. **Rank by slowdown weight.** One tick of delay costs an order `1 / max(span, bound)`
   of slowdown, so this is weighted shortest-job-first: sort by
   `remaining work × span^0.5`, smallest first.
3. **Never start a lost cause.** An order that cannot finish before its customer
   leaves goes behind every order that still can. It is only cooked when a cook
   would otherwise stand idle.
4. **Choose the set, then map it onto cooks.** Each decision picks the best set
   of orders that fit in the free station places, then assigns them while changing
   as few cooks as possible. A cook being reassigned hands its station place back
   inside the same decision, so the station arithmetic is exact.
5. **On `function`, sweep once.** Response time stops at an order's first tick of
   work, so every order gets one tick, longest first, and the cooks then settle
   into shortest-job-first. This cuts mean response from about 354 ticks to 11
   without the switching cost of round robin.

It also learns per-recipe, per-step durations from served orders. This lets it
estimate remaining work on the `blind` profile, where durations are hidden.

## What was tried and rejected

Every idea was measured across all nine profiles before it was kept or dropped.

| Idea | Result |
| --- | --- |
| Deadline urgency (rank orders up as their deadline nears) | Best setting was "off"; cost up to 3 points |
| ATC-style urgency, scaled by job size | Worse than off at every setting tried |
| Preempting to rescue an order about to walk out | Cost about 4 points on `rush` |
| The same rescue on the single-cook profile only | +0.1, inside the noise; removed |
| Avoiding station bumps | Consistently worse: resuming after a bump is a free switch anyway |

Deadline chasing loses because completion counts orders, not ticks. Rescuing one
60-tick banquet costs the several short orders the same cook time could have served.

## Repository layout

```text
scheduler.py      the scheduler: the whole submission
tools/bench.py    mark over all nine profiles for a scheduler or a reference
tools/diag.py     per-profile component breakdown, side by side with a reference
tools/sweep.py    sweep the scheduler's tuning constants and compare marks
```

## Running it

The course kit (engine, SDK and service profiles) is not included here: it comes
from the course site and is the course's to distribute.

1. Download and unzip the kit **for your platform**. A Linux-only kit will not
   load on Windows.
2. Copy `scheduler.py` to `my-scheduler/scheduler.py` inside the kit.
3. Copy the three files in `tools/` into the kit's root folder.
4. Open a terminal in the kit's root folder and run the setup check once. It
   copies the compiled engine into place:

```bash
./start.sh doctor            # macOS and Linux
.\START.cmd doctor           # Windows PowerShell
```

Then:

```bash
./start.sh check my-scheduler                                   # the marker's acceptance checks
python3 bench.py my-scheduler/scheduler.py --seeds 3000..3012     # mark over all nine profiles
python3 diag.py my-scheduler/scheduler.py --vs gordon_ramsay      # component breakdown
python3 sweep.py my-scheduler/scheduler.py --set GAMMA=0.5,0.75,1.0 --detail
```

The scripts must sit in the kit's root folder: they find the kit's SDK next to
themselves. On Windows, use `python` instead of `python3` and `.\START.cmd`
instead of `./start.sh`.

If Python reports *"cannot import name '_engine' from partially initialized module
'kitchen'"*, the compiled engine isn't in place. Run the `doctor` step and check it
reports a build for your platform.
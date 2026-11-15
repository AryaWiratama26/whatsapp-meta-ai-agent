"""The loop: ask the brain, run what it says, feed the results back."""

from .actions import parse
from .config import MAX_BAD_FORMAT, MAX_STEPS, SANDBOX
from .executor import execute
from .prompts import PROTOCOL, REMINDER


def run(brain, task):
    msg = PROTOCOL + task
    bad = 0
    for step in range(1, MAX_STEPS + 1):
        print(f"\n===== step {step} =====")
        reply = brain.ask(msg)
        print(f"[meta]\n{reply[:800]}")
        actions = parse(reply)
        if not actions:
            bad += 1
            if bad >= MAX_BAD_FORMAT:
                print("Meta AI keeps replying in the wrong format, stopping.")
                return
            msg = "Wrong format." + REMINDER
            continue
        bad = 0
        results, done = [], None
        for a in actions:
            if a.kind == "done":
                done = a.arg
                break
            try:
                results.append(execute(a))
            except Exception as e:
                results.append(f"ERROR: {e}")
        if done is not None:
            print("\n".join(results))
            print(f"\nDONE: {done}\nOutput is in: {SANDBOX}")
            return
        msg = "RESULTS:\n" + "\n\n".join(results) + "\n\nNext action?" + REMINDER
    print("Hit MAX_STEPS, stopping.")

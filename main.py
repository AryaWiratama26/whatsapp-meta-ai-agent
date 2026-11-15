"""Usage: python main.py "make a guess-the-number game in index.html"
See README.md for setup."""

import sys

from waagent.agent import run
from waagent.brain import WhatsAppBrain
from waagent.config import SANDBOX


def main():
    task = " ".join(sys.argv[1:]) or input("Task: ")
    SANDBOX.mkdir(exist_ok=True)
    brain = WhatsAppBrain()
    try:
        run(brain, task)
    finally:
        input("\nPress Enter to close the browser...")
        brain.close()


if __name__ == "__main__":
    main()

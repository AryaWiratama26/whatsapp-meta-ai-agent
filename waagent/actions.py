"""Turns a raw reply into a list of actions."""

import re
from typing import NamedTuple

ACTION_RE = re.compile(
    r"<bash>(?P<bash>.*?)</bash>"
    r"|<write\s+path=[\"'](?P<path>[^\"']+)[\"']\s*>\n?(?P<content>.*?)</write>"
    r"|<done>(?P<done>.*?)</done>",
    re.S,
)


class Action(NamedTuple):
    kind: str            # "bash" | "write" | "done"
    arg: str             # command, file path, or summary
    content: str = ""    # file contents (write only)


def parse(reply):
    actions = []
    for m in ACTION_RE.finditer(reply):
        if m.group("bash") is not None:
            actions.append(Action("bash", m.group("bash").strip()))
        elif m.group("path") is not None:
            actions.append(Action("write", m.group("path").strip(), m.group("content")))
        else:
            actions.append(Action("done", m.group("done").strip()))
    return actions

from pathlib import Path

CONTACT_NAME = "Meta AI"          # chat name as it appears in your chat list
PROFILE_DIR = Path("wa_profile").resolve()
SANDBOX = Path("sandbox").resolve()

MAX_STEPS = 15
MAX_BAD_FORMAT = 3                # stop after this many malformed replies in a row
REPLY_TIMEOUT = 120               # seconds to wait for a reply to start
POLL = 0.5                        # polling interval (seconds)
HISTORY_SETTLE = 2               # seconds the message list must stay unchanged before we send
STABLE_SECONDS = 3                # reply is "done" once its text stops changing this long

CONFIRM_COMMANDS = True           # ask before running each command
COMMAND_TIMEOUT = 60              # seconds
OUTPUT_LIMIT = 1500               # chars of command output sent back

SELECTORS = {
    "logged_in": "div#pane-side",
    "meta_ai_button": "button[aria-label='Meta AI']",
    "search_box": "input[role='textbox']",
    "compose_box": "footer div[contenteditable='true']",
    "message": "[data-testid^='conv-msg-']",
}

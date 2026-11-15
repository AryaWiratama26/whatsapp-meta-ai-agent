"""The model side: talks to Meta AI through WhatsApp Web. Anything with the same
ask(text) -> str and close() methods can replace it."""

import os
import shutil
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .config import (CONTACT_NAME, HISTORY_SETTLE, POLL, PROFILE_DIR, REPLY_TIMEOUT, SELECTORS,
                     STABLE_SECONDS)


# innerText collapses leading spaces (the bubbles use white-space: nowrap), which wrecks
# indentation. Walk the nodes instead: keep text nodes as they are, break lines at
# block elements, and skip the timestamp / read-receipt metadata.
READ_MESSAGES_JS = """
const skip = "[data-testid='msg-meta'], [aria-hidden='true'], svg, button";
const block = /^(DIV|P|LI|UL|OL|PRE|BR)$/;
function text(n) {
  if (n.nodeType === 3) return n.nodeValue;
  if (n.nodeType !== 1 || n.matches(skip)) return "";
  let out = "";
  for (const c of n.childNodes) out += text(c);
  if (block.test(n.tagName) && !out.endsWith("\\n")) out += "\\n";
  return out;
}
return Array.from(document.querySelectorAll(arguments[0]))
  .map(e => [e.dataset.id, text(e).replace(/^\\n+|\\n+$/g, "")]);
"""


def ignore_path_chromedriver():
    """Drop PATH entries holding a chromedriver, so Selenium Manager fetches one matching Chrome."""
    keep = [d for d in os.environ.get("PATH", "").split(os.pathsep)
            if not shutil.which("chromedriver", path=d)]
    os.environ["PATH"] = os.pathsep.join(keep)


class WhatsAppBrain:
    def __init__(self):
        ignore_path_chromedriver()
        opts = webdriver.ChromeOptions()
        opts.add_argument(f"--user-data-dir={PROFILE_DIR}")
        self.d = webdriver.Chrome(options=opts)
        self.d.get("https://web.whatsapp.com")
        print("[brain] waiting for login (scan the QR if it appears)...")
        WebDriverWait(self.d, 300).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["logged_in"])))
        self._open_chat()

    def _wait_clickable(self, key, timeout=30):
        return WebDriverWait(self.d, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS[key])))

    def _debug_dump(self):
        shot = Path("debug.png").resolve()
        self.d.save_screenshot(str(shot))
        found = self.d.execute_script(
            "return Array.from(document.querySelectorAll('input, [contenteditable]'))"
            ".map(e => e.outerHTML.slice(0, 200));")
        print(f"[debug] screenshot: {shot}")
        for html in found:
            print("[debug] input:", html)

    def _open_chat(self):
        try:
            if CONTACT_NAME == "Meta AI":
                # the sidebar has a dedicated Meta AI button; no search needed
                btn = self._wait_clickable("meta_ai_button")
                time.sleep(1)
                btn.click()
            else:
                box = self._wait_clickable("search_box")
                box.click()
                box.send_keys(CONTACT_NAME)
                time.sleep(2)
                box.send_keys(Keys.ENTER)
            WebDriverWait(self.d, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["compose_box"])))
        except TimeoutException:
            self._debug_dump()
            raise
        print(f"[brain] chat '{CONTACT_NAME}' is open")

    def _messages(self):
        """[(id, text)] for every message in the DOM, in order. WhatsApp virtualizes the
        list: off-screen messages keep their id but have empty text until rendered."""
        return self.d.execute_script(READ_MESSAGES_JS, SELECTORS["message"])

    def _snapshot_ids(self):
        """Ids of all messages once the history has finished loading. Right after the chat
        opens the DOM holds only a few messages; the rest arrive a moment later."""
        count, since = -1, time.time()
        while time.time() - since < HISTORY_SETTLE:
            ids = {m[0] for m in self._messages()}
            if len(ids) != count:
                count, since = len(ids), time.time()
            time.sleep(POLL)
        return ids

    def _replies(self, seen):
        """Texts of messages whose id is not in `seen`, minus the first new one, which is
        the message we just sent. Unrendered (empty) messages are skipped for now."""
        new = [m for m in self._messages() if m[0] not in seen]
        return [text for _, text in new[1:] if text]

    def _type(self, text):
        box = self.d.find_element(By.CSS_SELECTOR, SELECTORS["compose_box"])
        box.click()
        # insertText handles newlines and emoji better than send_keys
        ok = self.d.execute_script(
            "return document.execCommand('insertText', false, arguments[0]);", text)
        if not ok:  # fallback: type line by line with Shift+Enter
            for i, line in enumerate(text.split("\n")):
                if i:
                    box.send_keys(Keys.SHIFT, Keys.ENTER)
                box.send_keys(line)
        time.sleep(0.5)
        box.send_keys(Keys.ENTER)

    def ask(self, text):
        seen = self._snapshot_ids()
        self._type(text)
        end = time.time() + REPLY_TIMEOUT
        while not self._replies(seen):
            if time.time() > end:
                raise TimeoutError("Meta AI did not reply")
            time.sleep(POLL)
        # Meta AI streams/edits its reply -> wait until the text stops changing
        last, stable_since = "", time.time()
        while time.time() - stable_since < STABLE_SECONDS:
            cur = "\n".join(self._replies(seen))
            if cur != last:
                last, stable_since = cur, time.time()
            time.sleep(POLL)
        return last

    def close(self):
        self.d.quit()

"""
Keeps the Discord "updates" forum in sync with the changelog JSON files.

One forum post per script ("Cylex Apex Garage"): its first message is a short
intro card, every version is one message below it (oldest first). The state
file discord-state.json remembers, per script, the post and per version the
message id plus a hash of the entry:

  version not posted yet  -> new message (also how the old changelogs get posted)
  entry changed (same version pushed again with more lines) -> the message is edited
  unchanged               -> nothing

Usage:
  discord_changelog.py push <before-sha> <after-sha>   sync the scripts whose JSON changed in a push
  discord_changelog.py sync [resource ...]             sync these scripts, or every script
Environment:
  DISCORD_WEBHOOK   webhook URL of the forum channel (repo secret)
  DRY_RUN=1         print what would be sent, send nothing, keep the state file
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_FILE = os.path.join(ROOT, "discord-state.json")
SKIP = {"index.json", "discord-state.json"}

SITE = "https://cylexdev.com"
BRAND = "Cylex Development"
# Square logo for the author line / intro card; empty = none
BRAND_ICON = ""

# Embed colour by the most important kind of change in the release
COLOR_NEW = 0x00E5B0
COLOR_FIX = 0xFFB547
COLOR_PERF = 0x6CC6FF
COLOR_INTRO = 0x1E2229

SECTIONS = [
    ("add", "New"),
    ("change", "Changed"),
    ("fix", "Fixed"),
    ("perf", "Performance"),
    ("remove", "Removed"),
]
FIELD_LIMIT = 1024          # Discord: characters per field value
MESSAGE_LIMIT = 5800        # Discord: 6000 characters over all embeds of a message
GALLERY = 4                 # images shown as a grid under the card


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def changed_files(before, after):
    if not before or set(before) == {"0"}:
        cmd = ["git", "show", "--pretty=", "--name-only", after]
    else:
        cmd = ["git", "diff", "--name-only", before, after]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8")
    return [p[:-5] for p in out.split() if p.endswith(".json") and "/" not in p and p not in SKIP]


def all_resources():
    return sorted(p[:-5] for p in os.listdir(ROOT) if p.endswith(".json") and p not in SKIP)


def package_info(resource):
    for p in load_json(os.path.join(ROOT, "index.json"), {}).get("packages", []):
        if p.get("key") == resource:
            return p
    return {}


def entry_hash(entry):
    return hashlib.sha1(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


# --------------------------------------------------------------------------
# Messages
# --------------------------------------------------------------------------
def links(resource):
    out = [f"[Full changelog]({SITE}/changelog/{resource})"]
    pkg = package_info(resource).get("packageId")
    if pkg:
        out.append(f"[Store page]({SITE}/package/{pkg})")
    return " · ".join(out)


def author():
    a = {"name": BRAND, "url": SITE}
    if BRAND_ICON:
        a["icon_url"] = BRAND_ICON
    return a


def iso_date(date):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d").replace(hour=12).isoformat() + "Z"
    except (TypeError, ValueError):
        return None


def chunk_lines(lines, limit):
    """Lines packed into blocks of at most `limit` characters (a too long line is cut)"""
    blocks, cur = [], ""
    for line in lines:
        if len(line) > limit:
            line = line[: limit - 1] + "…"
        if cur and len(cur) + 1 + len(line) > limit:
            blocks.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        blocks.append(cur)
    return blocks


def release_color(entry):
    kinds = {c.get("type") for c in entry.get("changes", [])}
    if "add" in kinds or "change" in kinds:
        return COLOR_NEW
    if "fix" in kinds or "remove" in kinds:
        return COLOR_FIX
    return COLOR_PERF


def version_message(resource, name, entry, edited=False):
    changes = entry.get("changes", [])
    counts = []
    fields = []
    for kind, label in SECTIONS:
        lines = [f"▸ {c.get('text', '').strip()}" for c in changes if c.get("type") == kind]
        if not lines:
            continue
        counts.append(f"{len(lines)} {label.lower()}")
        blocks = chunk_lines(lines, FIELD_LIMIT)
        for i, block in enumerate(blocks):
            title = label if i == 0 else f"{label} (cont.)"
            fields.append({"name": title, "value": block, "inline": False})

    desc = []
    if entry.get("title"):
        desc.append(f"**{entry['title']}**")
    if counts:
        desc.append("`" + " · ".join(counts) + "`")

    files = entry.get("files")
    if files:
        fields.append({"name": "Changed files", "value": "```\n" + "\n".join(files)[: FIELD_LIMIT - 8] + "\n```", "inline": False})
    fields.append({"name": "​", "value": links(resource), "inline": False})

    embed = {
        "author": author(),
        "title": f"{name}  ·  v{entry['version']}",
        "url": f"{SITE}/changelog/{resource}",
        "description": "\n".join(desc) or None,
        "color": release_color(entry),
        "fields": fields,
        "footer": {"text": f"{BRAND}  ·  {'Updated' if edited else 'Released'}"},
    }
    stamp = iso_date(entry.get("date"))
    if stamp:
        embed["timestamp"] = stamp
    if embed["description"] is None:
        del embed["description"]

    # Too long for one message: the last sections give way to the changelog link
    while size(embed) > MESSAGE_LIMIT and len(embed["fields"]) > 2:
        embed["fields"].pop(-2)
        embed["fields"][-1]["value"] = "Some lines did not fit here. " + links(resource)

    embeds = [embed]
    images = (entry.get("images") or [])[:GALLERY]
    if images:
        embed["image"] = {"url": images[0]}
        # embeds with the same url show as one picture grid
        for url in images[1:]:
            embeds.append({"url": embed["url"], "image": {"url": url}})
    return {"embeds": embeds, "allowed_mentions": {"parse": []}}


def intro_message(resource, name):
    info = package_info(resource)
    lines = [
        f"Every update of **{name}** is posted in this thread, newest at the bottom.",
        "Follow the post to get a notification when a new version is out.",
        "",
        links(resource),
    ]
    embed = {
        "author": author(),
        "title": name,
        "url": f"{SITE}/package/{info['packageId']}" if info.get("packageId") else f"{SITE}/changelog/{resource}",
        "description": "\n".join(lines),
        "color": COLOR_INTRO,
        "footer": {"text": BRAND},
    }
    if BRAND_ICON:
        embed["thumbnail"] = {"url": BRAND_ICON}
    return {"embeds": [embed], "allowed_mentions": {"parse": []}}


def size(embed):
    n = len(embed.get("title", "")) + len(embed.get("description", "") or "")
    n += len(embed.get("footer", {}).get("text", "")) + len(embed.get("author", {}).get("name", ""))
    for f in embed.get("fields", []):
        n += len(f["name"]) + len(f["value"])
    return n


# --------------------------------------------------------------------------
# Discord
# --------------------------------------------------------------------------
class Gone(Exception):
    """The post or message no longer exists"""


def request(method, url, payload):
    body = json.dumps(payload).encode("utf-8")
    for _ in range(8):
        req = urllib.request.Request(url, data=body, method=method,
                                     headers={"Content-Type": "application/json", "User-Agent": "cylex-changelog (github action)"})
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                remaining = res.headers.get("X-RateLimit-Remaining")
                reset = res.headers.get("X-RateLimit-Reset-After")
                data = res.read().decode("utf-8")
                if remaining == "0" and reset:
                    time.sleep(float(reset) + 0.2)
                return json.loads(data) if data else {}
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            if e.code == 429:
                try:
                    wait = float(json.loads(text).get("retry_after", 2))
                except ValueError:
                    wait = 2
                time.sleep(wait + 0.3)
                continue
            if e.code == 404 or "Unknown Channel" in text or "Unknown Message" in text:
                raise Gone(text)
            raise SystemExit(f"Discord error {e.code} on {method}: {text}")
    raise SystemExit("Discord kept rate limiting, giving up")


class Discord:
    def __init__(self, webhook, dry):
        self.webhook = webhook.split("?")[0].rstrip("/")
        self.dry = dry
        self.fake = 0

    def _fake_id(self):
        self.fake += 1
        return f"dry-{self.fake}"

    def create_post(self, title, payload):
        if self.dry:
            print(f"  [new forum post] {title}")
            return self._fake_id(), self._fake_id()
        msg = request("POST", f"{self.webhook}?wait=true", dict(payload, thread_name=title[:100]))
        return msg["channel_id"], msg["id"]

    def send(self, thread, payload):
        if self.dry:
            print(f"  [send] {payload['embeds'][0].get('title')}")
            return self._fake_id()
        return request("POST", f"{self.webhook}?wait=true&thread_id={thread}", payload)["id"]

    def edit(self, thread, message, payload):
        if self.dry:
            print(f"  [edit] {payload['embeds'][0].get('title')}")
            return
        request("PATCH", f"{self.webhook}/messages/{message}?thread_id={thread}", payload)


# --------------------------------------------------------------------------
# Sync
# --------------------------------------------------------------------------
def sync(resource, state, discord):
    data = load_json(os.path.join(ROOT, resource + ".json"), None)
    if not data:
        return
    entries = [e for e in data.get("entries", []) if e.get("version") and e.get("changes")]
    if not entries:
        print(f"{resource}: no versions with changes, skipped")
        return
    name = data.get("package") or package_info(resource).get("name") or resource
    s = state.setdefault(resource, {"thread": None, "messages": {}})

    def open_post():
        thread, intro = discord.create_post(name, intro_message(resource, name))
        s["thread"], s["intro"], s["messages"] = thread, intro, {}
        if not discord.dry:
            save_state(state)

    if not s.get("thread"):
        open_post()

    # oldest first, so the post reads in release order
    for entry in reversed(entries):
        version = entry["version"]
        digest = entry_hash(entry)
        known = s["messages"].get(version)
        try:
            if not known:
                mid = discord.send(s["thread"], version_message(resource, name, entry))
                s["messages"][version] = {"id": mid, "hash": digest}
                print(f"{resource} {version}: posted")
            elif known.get("hash") != digest:
                discord.edit(s["thread"], known["id"], version_message(resource, name, entry, edited=True))
                known["hash"] = digest
                print(f"{resource} {version}: edited")
            else:
                continue
        except Gone as gone:
            if "10008" in str(gone) or "Unknown Message" in str(gone):
                # only this message was deleted: post it again
                mid = discord.send(s["thread"], version_message(resource, name, entry))
                s["messages"][version] = {"id": mid, "hash": digest}
                print(f"{resource} {version}: message was deleted, posted again")
            else:
                # the whole post was deleted on Discord: start it again
                print(f"{resource}: post gone, opening a new post")
                open_post()
                return sync(resource, state, discord)
        if not discord.dry:
            save_state(state)
        time.sleep(0.6)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("push", "sync"):
        raise SystemExit(__doc__)
    dry = os.environ.get("DRY_RUN") == "1"
    webhook = os.environ.get("DISCORD_WEBHOOK", "").strip()
    if not webhook and not dry:
        raise SystemExit("DISCORD_WEBHOOK is not set")

    if sys.argv[1] == "push":
        if len(sys.argv) < 4:
            raise SystemExit(__doc__)
        resources = changed_files(sys.argv[2], sys.argv[3])
    else:
        resources = sys.argv[2:] or all_resources()

    state = load_json(STATE_FILE, {})
    discord = Discord(webhook or "https://discord.invalid/dry", dry)
    for resource in resources:
        sync(resource, state, discord)
    if not resources:
        print("no changelog changed")


if __name__ == "__main__":
    main()

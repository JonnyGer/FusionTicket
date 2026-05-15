import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
FORUM_URL = "https://forum.fusion-festival.de/viewforum.php?f=82"
SEEN_POSTS_FILE = "seen_posts.json"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Nur benachrichtigen wenn Titel eines dieser Wörter enthält (Verkauf)
SELL_KEYWORDS = [
    "verkaufe", "verkauf", "vk", "abzugeben", "abgabe",
    "biete", "gebe ab", "zu verkaufen", "ticket ab",
    "spare ticket", "spare", "übrig", "übrige",
]

# Nie benachrichtigen wenn Titel eines dieser Wörter enthält (Gesuche)
BUY_KEYWORDS = [
    "suche", "gesucht", "wtb", "kaufe", "kaufen",
    "brauche", "benötige", "wer hat", "wer verkauft",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ─────────────────────────────────────────────
#  STATE MANAGEMENT
# ─────────────────────────────────────────────
def load_seen_posts() -> set:
    try:
        with open(SEEN_POSTS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_seen_posts(seen: set) -> None:
    with open(SEEN_POSTS_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)


# ─────────────────────────────────────────────
#  FORUM SCRAPER
# ─────────────────────────────────────────────
def fetch_topics() -> list[dict]:
    response = requests.get(FORUM_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    topics = []

    # phpBB3: topic titles are <a class="topictitle">
    for link in soup.select("a.topictitle"):
        href = link.get("href", "")

        # Extract topic ID from URL (e.g. ./viewtopic.php?f=82&t=12345)
        if "t=" not in href:
            continue
        topic_id = href.split("t=")[-1].split("&")[0].strip()
        if not topic_id.isdigit():
            continue

        # Build clean absolute URL
        clean_href = href.lstrip("./")
        full_url = f"https://forum.fusion-festival.de/{clean_href}"

        topics.append({
            "id": topic_id,
            "title": link.get_text(strip=True),
            "url": full_url,
        })

    return topics


# ─────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────
def send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID fehlt!")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram-Fehler: {e}")
        return False


# ─────────────────────────────────────────────
#  KEYWORD FILTER
# ─────────────────────────────────────────────
def is_selling(title: str) -> bool:
    """Gibt True zurück wenn der Thread ein Ticket-Angebot ist (kein Gesuch)."""
    t = title.lower()

    # Explizite Gesuche → immer ignorieren
    if any(kw in t for kw in BUY_KEYWORDS):
        return False

    # Verkaufs-Keywords → benachrichtigen
    if any(kw in t for kw in SELL_KEYWORDS):
        return True

    # Kein eindeutiges Keyword → trotzdem benachrichtigen
    # (lieber zu viel als ein Angebot verpassen)
    return True


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starte Forum-Check...")

    seen = load_seen_posts()

    try:
        topics = fetch_topics()
    except Exception as e:
        print(f"FEHLER beim Abrufen des Forums: {e}")
        sys.exit(1)

    print(f"  Gefunden: {len(topics)} Threads | Bereits bekannt: {len(seen)}")

    new_topics = [t for t in topics if t["id"] not in seen]

    if not new_topics:
        print("  Keine neuen Threads.")
    else:
        for topic in new_topics:
            # Bereits als gesehen markieren (unabhängig vom Filter)
            seen.add(topic["id"])

            if not is_selling(topic["title"]):
                print(f"  ⏭ Gesuch übersprungen: {topic['title']}")
                continue

            msg = (
                f"🎪 <b>Ticket-Angebot auf Fusion Forum!</b>\n\n"
                f"📌 <b>{topic['title']}</b>\n"
                f"🔗 <a href=\"{topic['url']}\">Zum Thread</a>"
            )
            if send_telegram(msg):
                print(f"  ✓ Benachrichtigt: {topic['title']}")
            else:
                print(f"  ✗ Benachrichtigung fehlgeschlagen: {topic['title']}")

    save_seen_posts(seen)
    print("  Fertig.")


if __name__ == "__main__":
    main()

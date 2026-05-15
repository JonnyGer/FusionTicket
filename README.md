# 🎪 Fusion Ticket Watcher

Überwacht automatisch das [Fusion Festival Ticket-Forum](https://forum.fusion-festival.de/viewforum.php?f=82) und sendet bei neuen Threads sofort eine **Telegram-Benachrichtigung**.

**Kosten: 0 €** — GitHub Actions (kostenlos für public Repos) + Telegram Bot (kostenlos)

---

## Architektur

```
GitHub Actions (alle 5 Min)
    → checker.py läuft
    → Forum wird gescrapt
    → Neue Threads werden gefunden
    → Telegram-Nachricht gesendet
    → seen_posts.json wird committed
```

---

## Schritt-für-Schritt Setup

### Schritt 1: Telegram Bot erstellen (5 Min)

1. Öffne Telegram und suche nach **@BotFather**
2. Schreibe `/newbot`
3. Gib dem Bot einen Namen, z.B. `FusionWatcher`
4. Gib dem Bot einen Username, z.B. `fusion_watcher_bot`
5. **Kopiere den API Token** → sieht aus wie `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

**Deine Chat-ID herausfinden:**
1. Schreibe deinem neuen Bot irgendwas in Telegram
2. Öffne diese URL im Browser (Token ersetzen):
   ```
   https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates
   ```
3. In der JSON-Antwort steht `"chat": {"id": 123456789}` → das ist deine **Chat-ID**

---

### Schritt 2: GitHub Repository anlegen

1. Gehe auf [github.com](https://github.com) und logge dich ein
2. Klicke auf **New Repository**
3. Name: `fusion-ticket-watcher`
4. Wichtig: **Public** auswählen (damit GitHub Actions kostenlos sind)
5. Repository erstellen

---

### Schritt 3: Projektdateien hochladen

Option A – via GitHub Web UI (einfacher):
1. Alle Dateien dieses Projekts einzeln über "Add file → Upload files" hochladen
2. Reihenfolge egal, aber Ordnerstruktur beachten:
   ```
   fusion-ticket-watcher/
   ├── .github/
   │   └── workflows/
   │       └── check_tickets.yml
   ├── checker.py
   ├── requirements.txt
   └── seen_posts.json
   ```

Option B – via Terminal (schneller):
```bash
cd fusion-ticket-watcher
git init
git remote add origin https://github.com/DEIN_USERNAME/fusion-ticket-watcher.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

---

### Schritt 4: GitHub Secrets setzen

1. Im Repository: **Settings → Secrets and variables → Actions**
2. Klicke **New repository secret**
3. Füge hinzu:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | Dein Bot-Token aus Schritt 1 |
| `TELEGRAM_CHAT_ID` | Deine Chat-ID aus Schritt 1 |

---

### Schritt 5: Actions aktivieren

1. Im Repository auf **Actions** klicken
2. Falls GitHub fragt: **"I understand my workflows, go ahead and enable them"** bestätigen
3. Klicke auf **Fusion Ticket Watcher** → **Run workflow** → testen!

---

### Schritt 6: Erster manueller Test

1. Gehe zu **Actions → Fusion Ticket Watcher → Run workflow**
2. Klicke **Run workflow**
3. Warte ~30 Sekunden
4. Klicke auf den Run und prüfe die Logs
5. Du solltest eine Telegram-Nachricht bekommen (wenn neue Threads vorhanden sind)

---

## Claude Code Prompts

Diese Prompts kannst du direkt in **Claude Code** (Terminal: `claude`) eingeben um das Projekt zu bauen, debuggen oder erweitern:

### Initiales Setup
```
Erstelle ein Python-Script checker.py das das phpBB-Forum 
https://forum.fusion-festival.de/viewforum.php?f=82 überwacht.
Es soll alle Threads scrapen (a.topictitle Selektor), neue mit 
seen_posts.json vergleichen, und neue Threads per Telegram Bot senden.
Token aus ENV TELEGRAM_BOT_TOKEN, Chat-ID aus TELEGRAM_CHAT_ID.
```

### Debugging wenn kein Output kommt
```
Das Script checker.py sendet keine Telegram-Nachrichten obwohl 
neue Threads vorhanden sind. Füge detailliertes Debug-Logging hinzu 
und prüfe ob der CSS-Selektor "a.topictitle" für das phpBB-Forum 
korrekt ist. Gib mir auch einen Test-Modus der alle gefundenen 
Threads ausgibt ohne seen_posts.json zu verändern.
```

### Debug-Modus aktivieren
```
Füge checker.py einen --debug Flag hinzu. Im Debug-Modus:
1. Alle gefundenen Threads ausgeben (Titel + URL + ID)
2. Den rohen HTML-Quelltext der ersten 2000 Zeichen loggen
3. KEINE Telegram-Nachricht senden
4. seen_posts.json NICHT verändern
```

### Keyword-Filter hinzufügen
```
Erweitere checker.py um einen optionalen Keyword-Filter.
Benachrichtige nur wenn der Thread-Titel eines dieser Wörter enthält 
(case-insensitive): "ticket", "karte", "vvk", "abgabe", "verkauf", "suche".
Filter soll per Umgebungsvariable KEYWORDS (kommagetrennt) konfigurierbar sein.
Wenn KEYWORDS leer ist, alle Threads melden.
```

### Telegram-Nachricht anpassen
```
Ändere das Telegram-Nachrichtenformat in checker.py.
Neue Nachricht soll enthalten:
- Emoji 🎪
- "FUSION TICKET ALERT" fett
- Thread-Titel
- Direktlink zum Thread
- Zeitstempel wann gefunden (deutsche Zeitzone)
```

### Auf Email umstellen (optional)
```
Füge checker.py alternativ Email-Support hinzu via smtplib.
Konfigurierbar über ENV-Variablen: SMTP_HOST, SMTP_PORT, 
SMTP_USER, SMTP_PASS, NOTIFY_EMAIL.
Wenn TELEGRAM_BOT_TOKEN gesetzt → Telegram. 
Wenn NOTIFY_EMAIL gesetzt → Email. Beides möglich.
```

---

## Troubleshooting

**Actions laufen nicht:**
- Repo muss Public sein ODER du hast noch freie Action-Minuten
- Actions müssen im Repository aktiviert sein (Settings → Actions)

**Keine Telegram-Nachricht:**
1. Debug-Modus laufen lassen: `python checker.py --debug`
2. Secrets korrekt gesetzt? (Settings → Secrets)
3. Chat-ID korrekt? (Du musst dem Bot zuerst eine Nachricht geschickt haben)

**seen_posts.json wird nicht committed:**
- Workflow braucht `permissions: contents: write` (bereits gesetzt)
- Prüfe ob Branch-Schutzregeln aktiv sind

**Forum blockiert Requests:**
- User-Agent Header ist bereits gesetzt
- Bei hartnäckigen Blocks: Script schläft 3-5 Sek vor Request (`time.sleep(random.uniform(3,5))`)

---

## Reset (alles neu scannen)

Wenn du den Watcher zurücksetzen willst:
```bash
echo "[]" > seen_posts.json
git add seen_posts.json
git commit -m "reset: clear seen posts"
git push
```

---

## Kosten-Übersicht

| Service | Kosten |
|---------|--------|
| GitHub (public repo) | 0 € |
| GitHub Actions (public repo) | 0 € unlimitiert |
| Telegram Bot | 0 € |
| **Gesamt** | **0 €** |

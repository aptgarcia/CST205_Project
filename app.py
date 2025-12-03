from flask import Flask, render_template, jsonify, abort
import requests
import random
import json
from pathlib import Path
from bs4 import BeautifulSoup  # python -m pip install  beautifulsoup4 into your venv before running

app = Flask(__name__)

# === Load celebrity data from JSON ===
ROOT = Path(__file__).parent
with open(ROOT / "celebrities.json", "r", encoding="utf-8") as f:
    CELEBS = json.load(f)

GENIUS_API_URL = "https://api.genius.com"
GENIUS_TOKEN = "ZIAi4fLqPeoMefSqzipUPYK9ryLD-wbcN81CvWy9m4xbKzDlXB7SAx4QPJ9VwbRO"


def genius_get(path, **params):  # using genius API examples
    headers = {"Authorization": f"Bearer {GENIUS_TOKEN}"}
    resp = requests.get(f"{GENIUS_API_URL}{path}", headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def resolve_artist_id(artist_name: str):
    data = genius_get("/search", q=artist_name)
    hits = data.get("response", {}).get("hits", [])
    for h in hits:
        pa = h["result"].get("primary_artist")
        if pa and pa.get("name", "").lower() == artist_name.lower():
            return pa.get("id")
    if hits:
        return hits[0]["result"]["primary_artist"]["id"]
    return None


def get_artist_songs(artist_id: int, pages: int = 3):
    #Fetch songs from Genius for this artist id.
    #Filter so we only keep songs where this artist is the PRIMARY artist, not just "featuring" on someone else's song or an archive/compilation.
    songs = []
    for page in range(1, pages + 1):
        try:
            data = genius_get(f"/artists/{artist_id}/songs", per_page=50, page=page)
            part = data.get("response", {}).get("songs", [])
            if not part:
                break

            for s in part:
                primary = s.get("primary_artist") or {}
                if primary.get("id") == artist_id:
                    #Only keep true primary-artist songs
                    songs.append(s)
        except Exception:
            break
    return songs



def scrape_two_lyric_lines(song_url: str): 
    #Extract two consecutive lyric lines from the actual song lyrics only.
    #Uses Genius lyric containers (<div data-lyrics-container="true">)
    #Skips section headers like [Chorus], [Verse 1], and very short filler lines.
    try:
        #Step 1: request the Genius song webpage
        #The "User-Agent" makes our request look like a normal browser, so Genius will return the real lyrics page instead of blocking us.
        page = requests.get(
            song_url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (CST205 student project)"}
        )

        #Stop if Genius returns an error (404, 403, etc.)
        page.raise_for_status()

        #Convert the HTML into a structured format so we can search it
        soup = BeautifulSoup(page.text, "html.parser")

        #Fetch only the lyric containers (avoids the 'About' panel and other sidebar text)
        containers = soup.select('div[data-lyrics-container="true"]')
        if not containers:
            print("No lyric containers found")
            return None, None

        #Flatten all text inside lyric containers into a list of raw lines
        raw_lines = []
        for c in containers:
            for ln in c.stripped_strings:
                ln = ln.strip()
                if ln:
                    raw_lines.append(ln)

        if not raw_lines:
            return None, None

        #The ABOUT section appears before the first section header.
        #Real lyrics begin after headers like [Intro], [Verse], [Chorus]
        start_idx = 0
        for i, ln in enumerate(raw_lines):
            if ln.startswith("[") and ln.endswith("]"):
                start_idx = i + 1
                break

        #Build the final clean list of lyric lines
        lines = []
        for ln in raw_lines[start_idx:]:
            #Skip section headers like [Chorus], [Verse], etc.
            if ln.startswith("[") and ln.endswith("]"):
                continue
            #Skip very short filler lines like "yeah", "oh"
            if len(ln) < 4:
                continue
            lines.append(ln)

        if len(lines) < 2:
            return None, None

        #Pick a random index that still leaves room for the next line
        idx = random.randint(0, len(lines) - 2)
        line1 = lines[idx]
        line2 = lines[idx + 1]

        return line1, line2

    except Exception as e:
        print("Lyric scrape error:", e)
        return None, None


def fetch_song_quote(artist_name: str) -> dict:
    try:
        artist_id = resolve_artist_id(artist_name)
        if not artist_id:
            return {"content": "No songs found for this artist.", "author": artist_name}

        songs = get_artist_songs(artist_id)
        if not songs:
            return {"content": "No songs available for this artist.", "author": artist_name}

        song = random.choice(songs)
        song_title = song.get("title", "Unknown Song")
        song_url = song.get("url", "")

        line1, line2 = scrape_two_lyric_lines(song_url)

        if line1 and line2:
            content = f"{line1}<br>{line2}"
        elif line1:
            content = line1
        else:
            content = f"A line from “{song_title}”." #sometimes it defaults to this for some songs

        return {
            "content": content,
            "author": artist_name,
            "song": song_title,
            "url": song_url
        }
    except Exception:
        return {"content": "No lyric available.", "author": artist_name}


@app.route("/")
def index():
    #No data passed – index.html is static
    return render_template("index.html")


@app.route("/celebrity/<slug>")
def celebrity(slug):
    celeb = CELEBS.get(slug)
    if not celeb:
        abort(404)
    quote = fetch_song_quote(celeb["quotable_author"])
    return render_template("celebrity.html", celeb=celeb, quote=quote)


@app.route("/api/quote/<slug>")
def api_quote(slug):
    celeb = CELEBS.get(slug)
    if not celeb:
        return jsonify({"ok": False}), 404
    q = fetch_song_quote(celeb["quotable_author"])
    return jsonify({"ok": True, "quote": q})


if __name__ == "__main__":
    app.run(debug=True)

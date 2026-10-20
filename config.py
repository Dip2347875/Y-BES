"""Central settings. Everything secret comes from environment variables / GitHub Secrets."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK, OUT = ROOT / "work", ROOT / "output"
ASSETS = ROOT / "assets"
FONTS, MUSIC = ASSETS / "fonts", ASSETS / "music"
STATE_FILE = ROOT / "state" / "state.json"
for _p in (WORK, OUT, FONTS, MUSIC, STATE_FILE.parent):
    _p.mkdir(parents=True, exist_ok=True)


def env(name, default=""):
    return os.getenv(name, default).strip()


# ---- sources -------------------------------------------------------------
RSS_FEEDS = [u.strip() for u in env(
    "BOOK_RSS_FEEDS",
    "https://rss.nytimes.com/services/xml/rss/nyt/Books.xml,"
    "https://www.theguardian.com/books/rss,"
    "https://www.goodreads.com/blog/list_rss.xml").split(",") if u.strip()]
PEXELS_KEY, PIXABAY_KEY = env("PEXELS_API_KEY"), env("PIXABAY_API_KEY")
PEXELS_BUDGET = int(env("PEXELS_BUDGET", "150"))        # Pexels allows ~200 requests / hour

# ---- voice ---------------------------------------------------------------
VOICE = env("EDGE_VOICE", "en-US-AndrewNeural")
RATE, PITCH = env("TTS_RATE", "-4%"), env("TTS_PITCH", "-2Hz")

# ---- video formats -------------------------------------------------------
LONG = dict(W=1920, H=1080, fps=24, chunk_words=34, max_words=48)
MIN_WORDS_LONG = int(env("MIN_WORDS_LONG", "2200"))   # skip books that do not have enough free material
SHORT = dict(W=1080, H=1920, fps=30, target_seconds=55, chunk_words=12, max_words=18)
RENDER_WORKERS = int(env("RENDER_WORKERS", "2"))
FFMPEG_THREADS = env("FFMPEG_THREADS", "2")

# ---- schedule (local hour of your audience / yourself) -------------------
SLOT_TZ_OFFSET = float(env("SLOT_TZ_OFFSET", "6"))      # 6 = Bangladesh (UTC+6)
SHORT_SLOTS = (6, 18)                                    # 6 AM, 6 PM
LONG_SLOTS = (0, 12)                                     # 12 AM, 12 PM

CATEGORIES = ["Self-Improvement", "Business & Money", "Psychology & Mind", "Productivity & Habits",
              "Leadership & Management", "History & Politics", "Science & Technology",
              "Philosophy & Wisdom", "Health & Wellness", "Biography & Memoir",
              "Fiction & Literature", "Relationships & Communication", "Parenting & Education",
              "Spirituality"]

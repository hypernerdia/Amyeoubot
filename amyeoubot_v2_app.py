# AmyeouBot v2 — Optimized for Streamlit Cloud
import streamlit as st
import sqlite3
from datetime import datetime
import random
import io

# Optional imports
HF_AVAILABLE = True
try:
    from transformers import pipeline
except Exception:
    HF_AVAILABLE = False

# TTS
TTS_AVAILABLE = True
try:
    from gtts import gTTS
except Exception:
    TTS_AVAILABLE = False

# ---------- Config ----------
DB_PATH = "amyeoubot_v2.db"
MODEL_NAME = "typeform/distilbert-base-uncased-mnli"  # lighter model for Streamlit Cloud

# ---------- Data ----------
LESSONS = [
    {
        "id": 1,
        "level": "Beginner",
        "title": "Greetings & Introductions",
        "phrases": [
            {"ko": "안녕하세요", "roman": "Annyeonghaseyo", "en": "Hello (formal)"},
            {"ko": "안녕", "roman": "Annyeong", "en": "Hi / Hello (informal)"},
            {"ko": "감사합니다", "roman": "Gamsahamnida", "en": "Thank you"},
            {"ko": "죄송합니다", "roman": "Joesonghamnida", "en": "I'm sorry"},
            {"ko": "제 이름은 ... 입니다", "roman": "Je ireumeun ... imnida", "en": "My name is ..."},
        ]
    },
    {
        "id": 2,
        "level": "Beginner",
        "title": "Daily Expressions & Politeness",
        "phrases": [
            {"ko": "잘 자요", "roman": "Jal jayo", "en": "Good night (polite)"},
            {"ko": "잘 지내요?", "roman": "Jal jinaeyo?", "en": "How are you? (polite)"},
            {"ko": "네 / 아니요", "roman": "Ne / Aniyo", "en": "Yes / No"},
            {"ko": "실례합니다", "roman": "Sillyehamnida", "en": "Excuse me"},
        ]
    },
    {
        "id": 3,
        "level": "Intermediate",
        "title": "Encouragement & Comfort",
        "phrases": [
            {"ko": "힘내세요", "roman": "Himnaeseyo", "en": "Cheer up / Stay strong"},
            {"ko": "괜찮아요", "roman": "Gwaenchanayo", "en": "It's okay / I'm okay"},
            {"ko": "천천히 하세요", "roman": "Cheoncheonhi haseyo", "en": "Take it slow"},
            {"ko": "잘하고 있어요", "roman": "Jalhago isseoyo", "en": "You're doing well"},
        ]
    }
]

QUIZ_BANK = [
    {"category": "vocab", "q": "How do you say 'Thank you' in Korean?", "options": ["안녕", "감사합니다", "잘자요"], "answer": "감사합니다", "level": "Beginner"},
    {"category": "vocab", "q": "What does '힘내세요' mean?", "options": ["Cheer up", "Goodbye", "Thank you"], "answer": "Cheer up", "level": "Intermediate"},
    {"category": "vocab", "q": "Translate to English: '안녕하세요'", "options": ["Goodbye", "Hello (formal)", "See you"], "answer": "Hello (formal)", "level": "Beginner"},
    {"category": "vocab", "q": "What is '안녕' in English?", "options": ["Hello (informal)", "Thank you", "Excuse me"], "answer": "Hello (informal)", "level": "Beginner"},
    {"category": "culture", "q": "Which bow is generally used for formal greetings in Korea?", "options": ["Slight bow", "Deep bow", "Side bow"], "answer": "Deep bow", "level": "Intermediate"},
    {"category": "grammar", "q": "Which particle often marks the subject in Korean (informal)?", "options": ["은/는", "이/가", "를/을"], "answer": "이/가", "level": "Intermediate"},
    {"category": "vocab", "q": "How do you say 'I'm sorry' politely in Korean?", "options": ["미안", "미안해요", "죄송합니다"], "answer": "죄송합니다", "level": "Beginner"},
    {"category": "vocab", "q": "What does '괜찮아요' mean?", "options": ["It's okay", "Thank you", "Goodbye"], "answer": "It's okay", "level": "Beginner"},
    {"category": "phrases", "q": "How to say 'Take it slow' in Korean?", "options": ["힘내세요", "천천히 하세요", "잘 지내요"], "answer": "천천히 하세요", "level": "Intermediate"},
]

MOTIVATION_QUOTES = [
    "Small steps every day lead to big changes. Keep going.",
    "You are capable of more than you think. Take one tiny action today.",
    "Progress, not perfection. Celebrate small wins.",
    "Setbacks are setups for comebacks. You've got this."
]
INSPIRATION_PROMPTS = [
    "Name one thing you're grateful for today.",
    "What is one small goal you can complete in 30 minutes?",
    "Who inspires you and why?"
]
AFFIRMATIONS = [
    "I am learning and improving every day.",
    "I deserve rest and progress in equal measure.",
    "I am capable of overcoming hard things."
]
COPING_STRATEGIES = [
    "Try box breathing: inhale 4s — hold 4s — exhale 4s — hold 4s. Repeat 4 times.",
    "Take a 5-minute walk outside and notice your surroundings.",
    "Write down one thing you did well today, however small."
]

# ---------- Database helpers ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    created_at TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    quiz_category TEXT,
                    score INTEGER,
                    created_at TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS mood_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    mood_text TEXT,
                    mood_score INTEGER,
                    created_at TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    entry_text TEXT,
                    created_at TEXT
                )""")
    conn.commit()
    conn.close()

def ensure_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (username, created_at) VALUES (?, ?)", (username, datetime.utcnow().isoformat()))
        conn.commit()
    conn.close()

def save_quiz_result(username, category, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO progress (username, quiz_category, score, created_at) VALUES (?, ?, ?, ?)", (username, category, score, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def save_mood(username, text, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO mood_entries (username, mood_text, mood_score, created_at) VALUES (?, ?, ?, ?)", (username, text, score, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def save_journal(username, text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO journal (username, entry_text, created_at) VALUES (?, ?, ?)", (username, text, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_progress(username, limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT quiz_category, score, created_at FROM progress WHERE username = ? ORDER BY id DESC LIMIT ?", (username, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_mood_history(username, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT mood_text, mood_score, created_at FROM mood_entries WHERE username = ? ORDER BY id DESC LIMIT ?", (username, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_journal_entries(username, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT entry_text, created_at FROM journal WHERE username = ? ORDER BY id DESC LIMIT ?", (username, limit))
    rows = c.fetchall()
    conn.close()
    return rows

# ---------- Intent recognition ----------
INTENTS = ["greeting", "learn_korean", "quiz", "wellness", "motivation", "inspiration", "journal", "smalltalk", "unknown"]

classifier = None
if HF_AVAILABLE:
    try:
        classifier = pipeline("zero-shot-classification", model=MODEL_NAME)
    except Exception:
        classifier = None

def hf_intent(text):
    if not classifier:
        return None
    try:
        res = classifier(text, INTENTS)
        return res['labels'][0]
    except Exception:
        return None

def keyword_intent(text):
    t = text.lower()
    if any(x in t for x in ["hi", "hello", "안녕", "안녕하세요"]):
        return "greeting"
    if any(x in t for x in ["teach", "learn", "korean", "phrase", "한국어", "말"]):
        return "learn_korean"
    if any(x in t for x in ["quiz", "test", "practice", "question"]):
        return "quiz"
    if any(x in t for x in ["sad", "stressed", "anxious", "depressed", "tired", "lonely", "i feel", "i'm feeling"]):
        return "wellness"
    if any(x in t for x in ["motivate", "motivation", "inspire", "inspiration", "encourage"]):
        return "motivation"
    if any(x in t for x in ["journal", "diary", "write", "reflect"]):
        return "journal"
    return "smalltalk"

def predict_intent(text):
    hf = hf_intent(text) if HF_AVAILABLE else None
    if hf:
        return hf
    return keyword_intent(text)

# ---------- Sentiment ----------
POS = {"good","happy","well","great","fine","better","excited","calm","relaxed","okay","ok","motivated"}
NEG = {"sad","stressed","depressed","anxious","tired","angry","upset","lonely","worry","worried","burnout","overwhelmed"}

def sentiment_score(text):
    words = [w.strip(".,!?;:()[]").lower() for w in text.split()]
    s = 0
    for w in words:
        if w in POS: s += 1
        if w in NEG: s -= 1
    if s > 5: s = 5
    if s < -5: s = -5
    return s

# ---------- TTS ----------
def tts_bytes(text, lang="ko"):
    if not TTS_AVAILABLE:
        return None
    try:
        tts = gTTS(text, lang=lang)
        bio = io.BytesIO()
        tts.write_to_fp(bio)
        bio.seek(0)
        return bio.read()
    except Exception:
        return None

@st.cache_data
def cached_tts(text, lang="ko"):
    return tts_bytes(text, lang)

# ---------- UI ----------
def show_header():
    st.title("🦊 AmyeouBot v2 — Korean Learning + Wellness")
    st.write("안녕하세요! AmyeouBot helps you learn Korean and supports your wellbeing.")

def sidebar_user():
    st.sidebar.header("User")
    username = st.sidebar.text_input("Enter your name (or nickname):", value="guest")
    if st.sidebar.button("Set User"):
        ensure_user(username)
        st.sidebar.success(f"User set to '{username}'")
    return username

def lessons_page(username):
    st.header("🇰🇷 Lessons")
    for lesson in LESSONS:
        st.subheader(f"{lesson['level']} — {lesson['title']}")
        for p in lesson["phrases"]:
            cols = st.columns([3,1])
            cols[0].markdown(f"**{p['ko']}** — {p['roman']} — {p['en']}")
            if TTS_AVAILABLE and cols[1].button("🔊", key=f"tts_{p['ko']}"):
                audio = cached_tts(p['ko'], lang="ko")
                if audio:
                    st.audio(audio, format="audio/mp3")

def quiz_page(username):
    st.header("📝 Korean Quizzes")
    level = st.selectbox("Level", ["Beginner","Intermediate","All"])
    category = st.selectbox("Category", ["Any","vocab","phrases","grammar","culture"])
    num = st.slider("Number of questions", 3, 10, 5)

    if st.button("Generate Quiz"):
        pool = [q for q in QUIZ_BANK if (level=="All" or q.get("level","Beginner")==level)]
        if category != "Any":
            pool = [q for q in pool if q.get("category")==category]
        if not pool:
            st.warning("No questions available for this selection.")
            return

        questions = random.sample(pool, min(len(pool), num))

        with st.form("quiz_form"):
            score = 0
            answers = {}
            for i,q in enumerate(questions):
                ans = st.radio(f"Q{i+1}. {q['q']}", q["options"], key=f"quiz_{i}")
                answers[i] = (ans, q["answer"])
            submitted = st.form_submit_button("Submit Quiz")
            if submitted:
                for _, (ans, correct) in answers.items():
                    if ans == correct:
                        score += 1
                pct = int(score/len(questions)*100)
                st.write(f"Score: {score}/{len(questions)} — {pct}%")
                save_quiz_result(username, category if category!="Any" else "mixed", pct)
                st.success("Quiz result saved!")

def wellness_page(username):
    st.header("💙 Wellness & Mental Health")
    mood = st.text_area("How are you feeling right now?")
    if st.button("Submit Mood"):
        if mood.strip():
            score = sentiment_score(mood)
            save_mood(username, mood, score)
            if score < 0:
                st.error("I'm sorry you're feeling this way 💙")
                st.write(random.choice(COPING_STRATEGIES))
            elif score == 0:
                st.info("Thanks for sharing. Maybe try a quiz or a breathing exercise.")
            else:
                st.success("I'm glad you're feeling good! 🌸")
    st.subheader("Mood history")
    for r in get_mood_history(username, 5):
        st.write(f"- [{r[2]}] Score: {r[1]} — {r[0]}")

def motivation_page(username):
    st.header("✨ Motivation & Inspiration")
    if st.button("Get Motivation"):
        st.write(random.choice(MOTIVATION_QUOTES))
    if st.button("Get Affirmation"):
        st.write(random.choice(AFFIRMATIONS))
    if st.button("Inspiration Prompt"):
        st.write(random.choice(INSPIRATION_PROMPTS))

def journal_page(username):
    st.header("📓 Journal / Reflection")
    entry = st.text_area("Write a short reflection (private):")
    if st.button("Save Entry"):
        if entry.strip():
            save_journal(username, entry)
            st.success("Reflection saved.")
    st.subheader("Recent entries")
    for r in get_journal_entries(username, 5):
        st.write(f"- [{r[1]}] {r[0]}")

def chat_page(username):
    st.header("💬 Chat with AmyeouBot")
    user_input = st.text_input("You:")
    if st.button("Send"):
        if user_input.strip():
            intent = predict_intent(user_input)
            st.write(f"**Intent detected:** {intent}")
            if intent == "greeting":
                st.write("안녕하세요! (Annyeonghaseyo) — Hi!")
            elif intent == "learn_korean":
                phrase = random.choice(random.choice(LESSONS)["phrases"])
                st.write(f"{phrase['ko']} ({phrase['roman']}) — {phrase['en']}")
            elif intent == "quiz":
                st.write("Try the 'Quizzes' page for practice questions.")
            elif intent == "wellness":
                st.write("Thanks for sharing. 💙")
            elif intent == "motivation":
                st.write(random.choice(MOTIVATION_QUOTES))
            elif intent == "inspiration":
                st.write(random.choice(INSPIRATION_PROMPTS))
            elif intent == "journal":
                save_journal(username, user_input)
                st.write("Reflection saved.")
            else:
                st.write("Hmm, try asking me to teach Korean or give motivation.")

def progress_page(username):
    st.header("📊 Progress & History")
    st.subheader("Quiz results")
    for r in get_progress(username, 5):
        st.write(f"- [{r[2]}] {r[0]} — {r[1]}%")

# ---------- Main ----------
def main():
    init_db()
    show_header()
    username = sidebar_user()
    st.sidebar.header("Navigate")
    page = st.sidebar.radio("Choose a page:", ["Home","Lessons","Quizzes","Wellness","Motivation","Chat","Journal","Progress"])
    if page == "Lessons": lessons_page(username)
    elif page == "Quizzes": quiz_page(username)
    elif page == "Wellness": wellness_page(username)
    elif page == "Motivation": motivation_page(username)
    elif page == "Chat": chat_page(username)
    elif page == "Journal": journal_page(username)
    elif page == "Progress": progress_page(username)
    else:
        st.subheader("Welcome!")
        st.write("Explore lessons, quizzes, wellness, and chat in the sidebar.")

if __name__ == "__main__":
    main()

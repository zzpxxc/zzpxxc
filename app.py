import streamlit as st
import datetime
import calendar
import random
import json
import os
import pandas as pd
import time
# --- Mood Elf Game Imports ---
from PIL import Image
import base64 
import io

# -------------------- 0. Mood Elf Helper Functions (for Pet Game) --------------------

@st.cache_data
def get_base64_image(image_path, cache_identifier): 
    """Converts image to Base64 for CSS background, uses cache_identifier to force reload."""
    try:
        # Uses relative path to the image
        full_path = image_path 
        with open(full_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

@st.cache_data
def load_pet_image(image_path):
    """Loads pet images using PIL (for robustness)."""
    try:
        return Image.open(image_path)
    except FileNotFoundError:
        return None

# -------------------- 1. GLOBAL CONSTANTS AND MAPPINGS --------------------

POINTS_PER_ENTRY = 10 
MAX_DAILY_POTION_ENTRIES = 5 # Max potions granted per day

st.set_page_config(page_title="🌸 Personalized Mood Journal Pro", layout="centered")

# --- Global Lists (English) ---
ACTIVITY_TAGS = [
    "Work 💻", "Exercise 🏋️", "Socializing 👥", "Food 🍕",
    "Family ❤️", "Hobbies 🎨", "Rest 🛋️", "Study 📚", "Travel ✈️", "Nature 🏞️", "Money 💰"
]

MOOD_MAPPING = {
    "Happy": "😀", "Sad": "😢", "Angry": "😡", "Calm": "😌", 
    "Excited": "🤩", "Tired": "😴", "Anxious": "😥",
}
MOOD_SCORES = {
    "😀": 5, "🤩": 4, "😌": 3, "😴": 2, "😢": 1, "😡": 1, "😥": 1
}

# --- Mood Elf Game Mappings ---
ELF_EVOLUTION_THRESHOLD = 30 # Pet evolution threshold
ELF_INITIAL_POTIONS = 5 # User request: 5 potions initially
ELF_IMAGE_DIR = "images"

# Potion name to file path mapping (lowercase)
POTION_MAPPING = {
    "happy": os.path.join(ELF_IMAGE_DIR, "potion_happy.png"),
    "sad": os.path.join(ELF_IMAGE_DIR, "potion_sad.png"),
    "angry": os.path.join(ELF_IMAGE_DIR, "potion_angry.png"),
    "calm": os.path.join(ELF_IMAGE_DIR, "potion_calm.png"),
    "excited": os.path.join(ELF_IMAGE_DIR, "potion_excited.png"),
    "tired": os.path.join(ELF_IMAGE_DIR, "potion_tired.png"),
    "anxious": os.path.join(ELF_IMAGE_DIR, "potion_anxious.png"),
}

# Pet evolution image paths (Capitalized)
PET_MAPPING = {
    "EGG": os.path.join(ELF_IMAGE_DIR, "egg.png"), # Unevolved pet
    "Happy": os.path.join(ELF_IMAGE_DIR, "pet_happy.png"),
    "Sad": os.path.join(ELF_IMAGE_DIR, "pet_sad.png"),
    "Angry": os.path.join(ELF_IMAGE_DIR, "pet_angry.png"),
    "Calm": os.path.join(ELF_IMAGE_DIR, "pet_calm.png"),
    "Excited": os.path.join(ELF_IMAGE_DIR, "pet_excited.png"),
    "Tired": os.path.join(ELF_IMAGE_DIR, "pet_tired.png"),
    "Anxious": os.path.join(ELF_IMAGE_DIR, "pet_anxious.png"),
}

# Helper: Emoji to internal pet name (lowercase)
EMOJI_TO_ELF_NAME = {
    "😀": "happy", "😢": "sad", "😡": "angry", "😌": "calm", 
    "🤩": "excited", "😴": "tired", "😥": "anxious",
}

# --- Response Texts (English) ---
EMOTION_RESPONSES = {
    "tired": "You sound tired 😴. Rest is productive too — take time to recharge.",
    "bored": "Boredom might mean your heart craves something new 🎨. Try doing something creative today!",
    "calm": "That’s wonderful 🌿. Calmness is peace speaking softly to your soul.",
    "guilty": "Guilt shows you care 🌱. Reflect gently and forgive yourself.",
    "anxious": "Anxiety can be heavy 😥. Breathe slowly — you’re safe and doing your best.",
    "happy": "Yay! So happy for you! 😄🎈 Let your joy shine and share your smile today!",
    "sad": f"It’s okay to feel sad 💧. Emotions flow and fade — here’s a little cheer-up joke for you:\n\n**{random.choice(['Why did the scarecrow win an award? Because he was outstanding in his field 🌾', 'I told my computer I felt sad — it gave me a byte of comfort 💻', 'Did you hear about the depressed coffee? It got mugged ☕'])}**",
    "lonely": "Loneliness is heavy 🫶. You’re not alone — I’m here listening.",
    "angry": "It’s alright to feel upset 😔. Let it out — expression is healing.",
}

GENERAL_RESPONSES = [
    "Thank you for sharing your entry ✍️. Remember, small steps lead to big changes.",
    "Your feelings are valid. Take a moment to focus on your breath and find peace. 🌬️",
    "It takes courage to write down your thoughts. We're here to listen to your journey! 🫂",
    "Keep up the habit of reflection! Every day is a new story waiting to unfold. 🌿",
    "Well done on making an entry today! You are prioritizing your well-being. 😊",
]

DAILY_PROMPTS = [
    "What is one thing that made you feel proud or accomplished today?",
    "If you could give yesterday's self one piece of advice, what would it be?",
    "Describe three sounds, smells, or sights you encountered today.",
    "Did you express gratitude to anyone today, or did someone make you feel grateful?",
    "What is one small thing you can do tomorrow to make it better?",
    "What is a new thing you learned today, no matter how small?",
]

SURPRISE_FACTS = [
    "Did you know a group of flamingos is called a 'flamboyance'? Stay flamboyant! 💖",
    "Fun Fact: Honey never spoils. Keep your good memories preserved like honey! 🍯",
    "Quick Riddle: What has to be broken before you can use it? An egg! Break those barriers!🥚",
    "A moment of wonder: There are more trees on Earth than stars in the Milky Way. Keep growing! 🌳",
    "Your lucky number today is 7! May your day be seven times brighter! ✨",
]

FORTUNE_SLIPS = (
    # Supreme Luck (大吉 - 5 slips)
    [("Supreme Luck", "🌟", "A day of profound clarity and happiness awaits. Trust your highest vision; your energy is magnetic today.")] * 2 +
    [("Supreme Luck", "🌟", "All relationships are blessed today. Reach out and share your good fortune; it will return tenfold.")] +
    [("Supreme Luck", "🌟", "An obstacle you faced yesterday dissolves today. Unexpected success finds you when you stay open.")] +
    [("Supreme Luck", "🌟", "Inner peace is your greatest asset. Use this calm to make powerful, confident decisions.")] +
    
    # Excellent Luck (吉 - 15 slips)
    [("Excellent Luck", "✨", "Your mind is sharp and ideas flow. Write down new goals; you have the power to achieve them.")] * 3 +
    [("Excellent Luck", "✨", "Take a risk today, especially in creative endeavors. Joy follows bold action.")] * 3 +
    [("Excellent Luck", "✨", "Unexpected kindness comes from a stranger or colleague. Pay it forward and brighten someone else's day.")] * 3 +
    [("Excellent Luck", "✨", "A lingering doubt is resolved easily. Feel lighter and move forward with purpose.")] * 3 +
    [("Excellent Luck", "✨", "The path to self-improvement is wide open. Commit to a healthy habit today.")] * 3 +

    # Good Prospect (中吉 - 15 slips)
    [("Good Prospect", "🍀", "A feeling of balance settles in. Trust the rhythm of your day and avoid unnecessary rushing.")] * 3 +
    [("Good Prospect", "🍀", "Someone needs your support. Offering a listening ear will deepen your connection.")] * 3 +
    [("Good Prospect", "🍀", "Your emotional well-being requires gentle attention. Focus on rest and simple pleasures.")] * 3 +
    [("Good Prospect", "🍀", "A small personal victory is on the horizon. Acknowledge and reward your efforts.")] * 3 +
    [("Good Prospect", "🍀", "Change is coming, but it is manageable. Prepare your mind for gentle adjustments.")] * 3 +

    # Moderate Fortune (小吉 - 10 slips)
    [("Moderate Fortune", "🌤️", "It is a day for careful planning. Avoid spontaneity and stick to your schedule for best results.")] * 2 +
    [("Moderate Fortune", "🌤️", "Energy levels are moderate. Conserve your efforts for what truly matters by saying 'no' when needed.")] * 2 +
    [("Moderate Fortune", "🌤️", "A minor misunderstanding may occur. Approach conversations with patience and seek clarity.")] * 2 +
    [("Moderate Fortune", "🌤️", "Don't dwell on perfection. Good enough is perfect for today; accept progress over flawless execution.")] * 2 +
    [("Moderate Fortune", "🌤️", "Neutral energy surrounds you. Use this quiet day for thoughtful reflection in your journal.")] * 2 +

    # Minor Challenge (凶 - 5 slips)
    [("Minor Challenge", "⚠️", "Frustration is possible. Use this as a signal to step away and seek immediate stress relief.")] +
    [("Minor Challenge", "⚠️", "A feeling of heaviness may arise. Be extra gentle with yourself and prioritize basic self-care.")] +
    [("Minor Challenge", "⚠️", "Be mindful of unnecessary spending or overcommitment. Your boundaries need protection today.")] +
    [("Minor Challenge", "⚠️", "Doubt may creep in. Remember your core strengths and seek external encouragement if needed.")] +
    [("Minor Challenge", "⚠️", "Communication requires extra effort. Write down your thoughts before speaking to avoid conflict.")]
)

# -------------------- 2. HELPER FUNCTIONS (Data & Streak) --------------------

def get_user_data_file(user_name):
    """Generates a unique file name based on user name."""
    if not user_name:
        return None
    safe_name = user_name.strip().lower().replace(" ", "_")
    return f"diary_{safe_name}.json"

def create_initial_elf_state():
    """Initializes the Mood Elf state for a new user or on first run (MODIFIED)."""
    mood_keys = POTION_MAPPING.keys()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    return {
        # Initial potion count is 5 for each (user request)
        'available_potions': {e: ELF_INITIAL_POTIONS for e in mood_keys}, 
        # Evolution counts start at 0
        'emotion_counts': {e: 0 for e in mood_keys},
        'total_feeds': 0,
        'evolution_threshold': ELF_EVOLUTION_THRESHOLD,
        'evolved': False,
        # Daily potion logging
        'daily_potion_count': 0, 
        'last_potion_date': today_str
    }

def load_diary(user_name):
    """Loads diary data for the specified user."""
    data_file = get_user_data_file(user_name)
    if not data_file: return
    
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.diary = data.get("diary", {})
                st.session_state.total_points = data.get("total_points", 0)
                
                loaded_date = data.get("fortune_date")
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                
                if loaded_date == today_str:
                    st.session_state.fortune_drawn = True
                    st.session_state.fortune_result = data.get("fortune_result", None)
                else:
                    st.session_state.fortune_drawn = False
                    st.session_state.fortune_result = None
            # --- Mood Elf Game State Loading (Initialization) ---
            st.session_state.elf_state = data.get("elf_state", None)
            if not st.session_state.elf_state:
                st.session_state.elf_state = create_initial_elf_state()
            
            # --- Check and reset daily potion limit ---
            last_potion_date = st.session_state.elf_state.get('last_potion_date', '1900-01-01')
            if last_potion_date != datetime.date.today().strftime("%Y-%m-%d"):
                st.session_state.elf_state['daily_potion_count'] = 0
                st.session_state.elf_state['last_potion_date'] = datetime.date.today().strftime("%Y-%m-%d")
                
        except json.JSONDecodeError:
            st.session_state.diary = {}
            st.session_state.elf_state = create_initial_elf_state()
    else:
        st.session_state.diary = {}
        st.session_state.elf_state = create_initial_elf_state()

def save_diary():
    """Saves diary and state data for the current user."""
    user_name = st.session_state.get("user_name")
    data_file = get_user_data_file(user_name)
    if not data_file: return

    data_to_save = {
        "diary": st.session_state.diary,
        "total_points": st.session_state.total_points,
        "user_name": user_name,
        "fortune_drawn": st.session_state.get("fortune_drawn", False),
        "fortune_result": st.session_state.get("fortune_result", None),
        "fortune_date": datetime.date.today().strftime("%Y-%m-%d"),
        # --- Mood Elf Game State Saving ---
        "elf_state": st.session_state.elf_state
    }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

def calculate_streak(diary):
    """Calculates the current consecutive logging streak."""
    if not diary: return 0
    logged_dates = set(
        datetime.datetime.strptime(d, "%Y-%m-%d").date() 
        for d in diary.keys()
    )
    today = datetime.date.today()
    streak = 0
    day_to_check = today
    if day_to_check in logged_dates:
        streak = 1
        day_to_check -= datetime.timedelta(days=1)
    elif (day_to_check - datetime.timedelta(days=1)) in logged_dates:
        streak = 1
        day_to_check -= datetime.timedelta(days=2) 
    else:
        return 0
    while day_to_check in logged_dates:
        streak += 1
        day_to_check -= datetime.timedelta(days=1)
    return streak

def get_diary_response(text):
    """Generates response based on keywords or random general."""
    text_lower = text.lower()
    for keyword, reply in EMOTION_RESPONSES.items():
        if keyword in text_lower:
            return reply
    return random.choice(GENERAL_RESPONSES)

def analyze_recent_mood_for_advice(diary):
    # ... (Mood advice logic remains the same - English only texts are fine)
    if not diary:
        return "👋 Time to start your first entry and unlock personalized advice!"
    today = datetime.date.today()
    one_week_ago = today - datetime.timedelta(days=7)
    recent_scores = []
    for date_str, entry in diary.items():
        entry_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if one_week_ago <= entry_date < today:
            recent_scores.append(entry.get('score', 3))
    if not recent_scores:
        return "🤔 Need a week of data for personalized advice. Keep logging!"
    df = pd.Series(recent_scores)
    avg_score = df.mean()
    if avg_score <= 2.5:
        low_moods = [entry['mood'] for date_str, entry in diary.items() 
                     if one_week_ago <= datetime.datetime.strptime(date_str, "%Y-%m-%d").date() < today and entry.get('score', 3) <= 2]
        if low_moods:
            most_common_low_mood = pd.Series(low_moods).mode()[0]
            if most_common_low_mood in ["😢", "😥"]:
                return f"😥 Recent Mood Alert: You've often felt sad/anxious. **Challenge:** Try a 10-minute mindfulness exercise today."
            elif most_common_low_mood in ["😴"]:
                return f"😴 Recent Mood Alert: You've often felt tired. **Challenge:** Aim for 30 minutes of light physical activity today."
            elif most_common_low_mood in ["😡"]:
                return f"😡 Recent Mood Alert: You've often felt angry. **Challenge:** Write down 3 things you are grateful for before bed."
            else:
                return f"📉 Recent Mood Alert: Your average mood score is low. **Challenge:** Reach out to a friend or loved one today."
    elif avg_score >= 4.0:
        return "✨ Great Job! Your recent mood trend is excellent! **Advice:** Share your joy—compliment someone today!"
    else:
        return "⚖️ Your mood is balanced. **Advice:** Keep exploring your activities! Try adding one new tag today."


# -------------------- 3. MOOD ELF GAME LOGIC (Integrated - MODIFIED) --------------------

def get_elf_evolution_type():
    """Determines the pet's evolution type based on the most fed potion (MODIFIED)."""
    elf_state = st.session_state.elf_state
    
    if not elf_state['evolved']:
        return "EGG"

    # Find the emotion with the maximum feed count
    max_feed_count = -1
    evolution_type = "Happy" # Default Pet Type

    for emotion, count in elf_state['emotion_counts'].items():
        if count > max_feed_count:
            max_feed_count = count
            # Convert lowercase emotion name to Capitalized name for image lookup
            evolution_type = emotion.capitalize() 
    
    # If all counts are 0, it should be EGG, but this function only runs if evolved is True.
    # We keep a default pet for safety if the evolved flag is somehow wrongly set.
    if max_feed_count == 0:
        return "Happy" 
        
    return evolution_type


def feed_mood_elf(emotion):
    """Core logic to feed the elf and check for evolution (MODIFIED)."""
    elf_state = st.session_state.elf_state
    
    if elf_state['evolved']:
        st.toast('The Mood Elf has already evolved! No more feeding allowed.', icon="✨")
        return

    # Ensure emotion name is lowercase for dictionary lookup
    emotion_name = emotion.lower()
    
    if elf_state['available_potions'][emotion_name] > 0:
        elf_state['available_potions'][emotion_name] -= 1
        elf_state['emotion_counts'][emotion_name] += 1
        elf_state['total_feeds'] += 1
        st.toast(f"Successfully fed {emotion_name.capitalize()} Potion! 🧪", icon="😋")
    else:
        st.toast(f"❌ {emotion_name.capitalize()} Potion ran out! Log your mood to get more.", icon="😔")
        
    if elf_state['total_feeds'] >= elf_state['evolution_threshold']:
        elf_state['evolved'] = True
        st.balloons()
        
    st.session_state.elf_state = elf_state
    save_diary() # Save the updated elf state

def grant_mood_potion(mood_emoji):
    """Grants a potion based on mood, checks daily limit (NEW FUNCTIONALITY)."""
    elf_state = st.session_state.elf_state
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # Daily reset check (safety)
    if elf_state.get('last_potion_date') != today_str:
        elf_state['daily_potion_count'] = 0
        elf_state['last_potion_date'] = today_str

    if elf_state['daily_potion_count'] < MAX_DAILY_POTION_ENTRIES:
        mood_name = EMOJI_TO_ELF_NAME.get(mood_emoji)
        if mood_name:
            elf_state['available_potions'][mood_name] += 1
            elf_state['daily_potion_count'] += 1
            st.session_state.potion_granted_today = True # Mark as granted
            return mood_name.capitalize(), True
    
    return None, False

def reset_mood_elf():
    """Resets the Mood Elf's evolution state only (NEW FUNCTION)."""
    elf_state = st.session_state.elf_state
    
    # Preserve potion counts, but reset feed counts
    emotion_keys = POTION_MAPPING.keys()
    
    st.session_state.elf_state.update({
        'emotion_counts': {e: 0 for e in emotion_keys},
        'total_feeds': 0,
        'evolved': False,
    })
    
    st.toast("Mood Elf has been reset to an Egg! Potions remain the same.", icon="🥚")
    save_diary()


# -------------------- 4. INITIALIZATION --------------------

def initialize_session_state():
    if "user_name" not in st.session_state:
        st.session_state.page = "onboarding"
    elif "page" not in st.session_state:
        st.session_state.page = "fortune_draw"
        
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.date.today()
    if "selected_mood_emoji" not in st.session_state:
        st.session_state.selected_mood_emoji = None
    
    if "diary" not in st.session_state:
        st.session_state.diary = {}
    if "total_points" not in st.session_state:
        st.session_state.total_points = 0
        
    if "fortune_drawn" not in st.session_state:
        st.session_state.fortune_drawn = False
        st.session_state.fortune_result = None
        
    # --- Mood Elf Game State Initialization ---
    if "elf_state" not in st.session_state:
        st.session_state.elf_state = create_initial_elf_state()
    
    if "potion_granted_today" not in st.session_state:
        st.session_state.potion_granted_today = False

    # Ensure daily count is reset on a new day
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    if st.session_state.elf_state.get('last_potion_date') != today_str:
        st.session_state.elf_state['daily_potion_count'] = 0
        st.session_state.elf_state['last_potion_date'] = today_str

initialize_session_state() 

# -------------------- 5. STYLES (Retained from Journal Pro) --------------------

FIXED_THEME_COLOR = "#c9b9a8" 
FIXED_ACCENT_COLOR = "#4b3f37" 

st.markdown(f"""
    <style>
        /* Journal Pro Styles */
        .title {{
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: {FIXED_ACCENT_COLOR}; 
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            font-size: 18px;
            color: #6d5f56;
            margin-bottom: 25px;
        }}
        .fortune-result-box {{
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            text-align: center;
            background-color: #fff8e1; /* Light yellow background */
            margin-top: 20px;
        }}
        .fortune-level {{
            font-size: 40px;
            font-weight: bold;
            color: {FIXED_ACCENT_COLOR};
        }}
        .fortune-emoji {{
            font-size: 60px;
            margin: 10px 0;
        }}
        .fortune-description {{
            font-size: 18px;
            font-style: italic;
            color: #6d5f56;
        }}
        .shaking-container {{
            text-align: center;
            margin: 40px auto;
            max-width: 300px;
        }}
        .shaking-icon {{
            font-size: 100px;
            display: inline-block;
        }}
        /* --- Mood Elf Game Styles (Minimal, for the pet image animation) --- */
        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-15px); }}
        }}

        .pet-image-animated {{
            animation: bounce 2s infinite ease-in-out;
        }}
    </style>
""", unsafe_allow_html=True)


# -------------------- 6. PAGE FUNCTIONS (English) --------------------

def render_onboarding_page():
    st.markdown("<div class='title'>Welcome to Your Mood Journal!</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Let's start by entering your name to load your journal.</div>", unsafe_allow_html=True)

    with st.container():
        name = st.text_input("Enter your name:", key="name_input")
        
        if st.button("Start Journaling 🚀", use_container_width=True):
            if name:
                st.session_state.user_name = name.strip()
                load_diary(st.session_state.user_name)
                st.session_state.page = "fortune_draw"
                st.rerun() 
            else:
                st.warning("Please enter your name to proceed.")


def render_fortune_draw_page():
    user = st.session_state.user_name
    st.markdown(f"<div class='title'>⛩️ Daily Fortune Draw</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>Welcome back, {user}! Draw your fortune to guide your day.</div>", unsafe_allow_html=True)
    
    draw_container = st.empty()
    
    if not st.session_state.fortune_drawn:
        draw_container.markdown(
            f"<div class='shaking-container'><div class='shaking-icon'>🎋</div></div>", unsafe_allow_html=True
        )
        
        if st.button("🥠 Draw Your Destiny! (Daily Draw)", use_container_width=True):
            for i in range(5):
                icon = "🎍" if i % 2 == 0 else "🎋"
                draw_container.markdown(
                    f"<div class='shaking-container'><div class='shaking-icon'>{icon}</div></div>", 
                    unsafe_allow_html=True
                )
                time.sleep(0.05) 

            fortune = random.choice(FORTUNE_SLIPS)
            st.session_state.fortune_result = fortune
            st.session_state.fortune_drawn = True
            save_diary()
            st.balloons()
            st.rerun() 
        
    
    if st.session_state.fortune_drawn and st.session_state.fortune_result:
        level, emoji, description = st.session_state.fortune_result
        
        draw_container.empty()
        
        st.markdown("---")
        st.markdown(f"### ✨ Your Daily Guidance for {datetime.date.today().strftime('%Y-%m-%d')}")
        
        st.markdown("<div class='fortune-result-box'>", unsafe_allow_html=True)
        st.markdown(f"<div class='fortune-level'>{level}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='fortune-emoji'>{emoji}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='fortune-description'>{description}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("Start Journaling for Today 📝", use_container_width=True):
            st.session_state.page = "date"
            st.rerun()

    elif st.session_state.fortune_drawn:
        st.info("You have already drawn your fortune for today. Please start journaling!")
        if st.button("Go to Journal 📝", use_container_width=True):
            st.session_state.page = "date"
            st.rerun()


def render_date_page():
    user = st.session_state.user_name
    points = st.session_state.total_points
    current_streak = calculate_streak(st.session_state.diary) 
    
    st.markdown(f"<div class='title'>🌸 Hi, {user}!</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>🔥 **Streak:** {current_streak} days | ⭐ **Mood Points:** {points} | Select a date to begin your entry.</div>", unsafe_allow_html=True)
    
    if st.session_state.fortune_result:
        level, emoji, _ = st.session_state.fortune_result
        st.success(f"🔮 Today's Fortune: **{level} {emoji}** - Use this guidance for your entry!")

    advice = analyze_recent_mood_for_advice(st.session_state.diary)
    st.markdown(f"<div class='advice-box'>💡 **Today's Insight:** {advice}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    selected_date = st.date_input("📅 Choose a date:", value=st.session_state.selected_date, key="date_picker")
    st.session_state.selected_date = selected_date
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4) 
    date_key = selected_date.strftime("%Y-%m-%d")
    is_logged = date_key in st.session_state.diary
    button_text = "Next ➜ Edit/Choose Mood" if is_logged else "Next ➜ Choose Mood"
    
    if col1.button(button_text, use_container_width=True):
        st.session_state.page = "mood"
        st.rerun()
    if col2.button("📆 View Monthly Calendar", use_container_width=True):
        st.session_state.page = "calendar"
        st.rerun()
    if col3.button("🔮 View Fun Insights", use_container_width=True):
        st.session_state.page = "insight"
        st.rerun()
    if col4.button("🥚 Mood Elf Game", use_container_width=True):
        st.session_state.page = "mood_elf"
        st.rerun()


def render_mood_page():
    date_key = st.session_state.selected_date.strftime("%Y-%m-%d")
    st.markdown("<div class='title'>How do you feel, today?</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{date_key}</div>", unsafe_allow_html=True)
    current_mood = st.session_state.diary.get(date_key, {}).get("mood", None)
    if current_mood and st.session_state.selected_mood_emoji is None:
        st.session_state.selected_mood_emoji = current_mood
    cols = st.columns(len(MOOD_MAPPING))
    for i, (mood_name, emoji) in enumerate(MOOD_MAPPING.items()):
        is_selected = (emoji == st.session_state.selected_mood_emoji)
        if cols[i].button(f"{emoji} {mood_name} {'(Selected)' if is_selected else ''}", key=mood_name, use_container_width=True):
             st.session_state.selected_mood_emoji = emoji
             st.session_state.page = "journal"
             st.rerun()
    st.markdown("---")
    if st.button("⬅ Back to Date"):
        st.session_state.page = "date"
        st.rerun()

def render_journal_page():
    date_key = st.session_state.selected_date.strftime("%Y-%m-%d")
    mood_icon = st.session_state.selected_mood_emoji
    existing_entry = st.session_state.diary.get(date_key, {})
    initial_text = existing_entry.get("text", "")
    initial_tags = existing_entry.get("tags", [])
    st.markdown(f"<div class='title'>📝 Journal Entry for {date_key}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>Your mood: {mood_icon}</div>", unsafe_allow_html=True)
    prompt_seed = st.session_state.selected_date.toordinal()
    random.seed(prompt_seed)
    daily_prompt = random.choice(DAILY_PROMPTS)
    random.seed() 
    st.info(f"✨ **Today's Prompt:** {daily_prompt}")
    selected_tags = st.multiselect(
        "🏷️ **Select relevant activities/causes:** (Optional)", 
        options=ACTIVITY_TAGS, 
        default=initial_tags,
        key="activity_tags"
    )
    diary_text = st.text_area("Write about your day:", value=initial_text, height=200, key="diary_text_area")
    col1, col2 = st.columns(2)
    if col1.button("💾 Save & Get Reflection", use_container_width=True):
        response = get_diary_response(diary_text)
        reward_points = 0
        is_new_entry = date_key not in st.session_state.diary
        
        # Check and grant potion
        potion_reward_name, is_granted = grant_mood_potion(mood_icon)
        
        if is_new_entry:
            reward_points = POINTS_PER_ENTRY
            st.session_state.total_points += reward_points
            
        st.session_state.diary[date_key] = {
            "mood": mood_icon, 
            "text": diary_text, 
            "response": response,
            "score": MOOD_SCORES.get(mood_icon, 3),
            "tags": selected_tags
        }
        save_diary()
        
        st.session_state.page = "action_page"
        st.session_state.last_response = response
        st.session_state.reward_points = reward_points
        st.session_state.potion_reward_name = potion_reward_name
        st.session_state.potion_is_granted = is_granted
        st.rerun()
        
    if col2.button("⬅ Back to Mood", use_container_width=True):
        st.session_state.page = "mood"
        st.rerun()
    if 'response' in existing_entry:
        st.markdown(f"---")
        st.markdown(f"### 💬 Last Reflection:\n*{existing_entry['response']}*")

def render_action_page():
    st.markdown("<div class='title'>Entry Saved Successfully!</div>", unsafe_allow_html=True)
    
    # Display potion grant message
    if st.session_state.potion_is_granted:
        st.success(f"🧪 Potion Reward! You earned one **{st.session_state.potion_reward_name}** Potion!\n\n**Today's Potion Count:** {st.session_state.elf_state.get('daily_potion_count', 0)} / {MAX_DAILY_POTION_ENTRIES}")
    else:
        st.info(f"😔 Daily potion limit reached (Max: {MAX_DAILY_POTION_ENTRIES} potions). Try again tomorrow!")
        
    if st.session_state.reward_points > 0:
        st.balloons()
        st.success(f"🎉 **Reward!** You earned **{st.session_state.reward_points} Mood Points** for your first entry today!")
        
    st.markdown(f"### 🌈 Today's Reflection:\n*{st.session_state.last_response}*")
    
    if random.random() < 0.25: 
        st.markdown("---")
        st.markdown("### 🔮 Daily Surprise:")
        st.warning(random.choice(SURPRISE_FACTS))
        
    st.markdown("---")
    st.markdown("### What would you like to do next?")
    col1, col2, col3, col4 = st.columns(4)
    if col1.button("🔮 View Fun Insights", use_container_width=True):
        st.session_state.page = "insight"
        st.rerun()
    if col2.button("📆 Go to Calendar", use_container_width=True):
        st.session_state.page = "calendar"
        st.rerun()
    if col3.button("📝 Start New Entry", use_container_width=True):
        st.session_state.selected_date = datetime.date.today()
        st.session_state.selected_mood_emoji = None
        st.session_state.page = "date"
        st.rerun()
    if col4.button("🥚 Play Mood Elf", use_container_width=True):
        st.session_state.page = "mood_elf"
        st.rerun()

def render_calendar_page():
    year, month = st.session_state.selected_date.year, st.session_state.selected_date.month
    st.markdown("<div class='title'>📅 Monthly Mood Overview</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{calendar.month_name[month]} {year}</div>", unsafe_allow_html=True)
    cal = calendar.monthcalendar(year, month)
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    col_w = st.columns(7)
    for i, d in enumerate(weekdays):
        col_w[i].markdown(f"<div style='text-align:center; font-weight:bold; color:#6d5f56;'>{d}</div>", unsafe_allow_html=True)
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                mood = st.session_state.diary.get(date_str, {}).get("mood", "")
                display_day = day
                display_mood = mood or "•"
                if cols[i].button("", key=f"cal_day_{date_str}", use_container_width=True):
                    st.session_state.selected_date = datetime.date(year, month, day)
                    st.session_state.selected_mood_emoji = mood
                    st.session_state.page = "journal"
                    st.rerun()
                cols[i].markdown(
                    f"""<div style='text-align:center; padding: 5px; border: 1px solid #ccc; border-radius: 5px; margin: 2px;'>
                        {display_day}<br>
                        <span style='font-size: 1.5em;'>{display_mood}</span>
                    </div>""", unsafe_allow_html=True
                )
            else:
                cols[i].markdown("<div style='width: 45px; height: 45px; margin: 2px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("⬅ Back to Date Selection", use_container_width=True):
        st.session_state.page = "date"
        st.rerun()

def render_insight_page():
    user = st.session_state.user_name
    st.markdown(f"<div class='title'>🔮 {user}'s Fun Insights!</div>", unsafe_allow_html=True)
    
    if not st.session_state.diary:
        st.warning("You need at least one entry to unlock your insights!")
        if st.button("Start Journaling Now", use_container_width=True):
            st.session_state.page = "date"
            st.rerun()
        return

    all_dates = list(st.session_state.diary.keys())
    
    first_entry_date = min(all_dates)
    total_entries = len(all_dates)
    st.markdown("---")
    st.markdown(f"### 🎉 Your Journaling Milestones")
    st.markdown(f"**Total Entries:** **{total_entries}** 🥳")
    st.markdown(f"**First Entry:** You started your journey on **{first_entry_date}**!")

    mood_list = [entry['mood'] for entry in st.session_state.diary.values()]
    top_mood_emoji = pd.Series(mood_list).mode()[0]
    top_mood_name = next(name for name, emoji in MOOD_MAPPING.items() if emoji == top_mood_emoji)
    st.markdown("---")
    st.markdown(f"### 🥇 Your Top Mood")
    st.markdown(f"Your most common mood so far is **{top_mood_name} {top_mood_emoji}**! Keep exploring your emotions.")

    all_tags = []
    happy_tags = []
    for entry in st.session_state.diary.values():
        tags = entry.get('tags', [])
        all_tags.extend(tags)
        if entry.get('mood') == '😀':
            happy_tags.extend(tags)
            
    st.markdown("---")
    
    if all_tags:
        top_tags = pd.Series(all_tags).value_counts().head(3)
        st.markdown(f"### 🏷️ Top Activities Logged")
        for tag, count in top_tags.items():
            st.markdown(f"**{tag}** logged **{count}** times.")
    
    if happy_tags:
        st.markdown(f"---")
        st.markdown(f"### 🤩 What Makes You Happy?")
        if happy_tags:
            happy_tag_counts = pd.Series(happy_tags).value_counts().head(3)
            for tag, count in happy_tag_counts.items():
                 st.markdown(f"🎉 **{tag}** made you happy **{count}** times!")
        else:
            st.info("Need more happy entries to analyze!")

    st.markdown("---")
    if st.button("⬅ Back to Date Selection", use_container_width=True):
        st.session_state.page = "date"
        st.rerun()

def render_mood_elf_page():
    """Renders the Mood Elf Game page (NEW PAGE)."""
    st.markdown("<div class='title'>🥚 Mood Elf Pet Game</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>Feed the pet with potions to evolve it into your dominant emotion type!</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    elf_state = st.session_state.elf_state
    
    col_pet, col_info = st.columns([1, 2])
    
    # --- Left Column: Pet Image and Status ---
    with col_pet:
        pet_type = get_elf_evolution_type()
        image_path = PET_MAPPING.get(pet_type)
        
        st.markdown(f"### Status: **{pet_type}**")
        
        image_pil = load_pet_image(image_path)
        if image_pil:
            st.image(image_pil, caption=f"Total Feeds: {elf_state['total_feeds']}/{elf_state['evolution_threshold']}", width=250)
            
        # Progress bar
        total_feeds = elf_state['total_feeds']
        progress_percent = min(total_feeds / ELF_EVOLUTION_THRESHOLD, 1.0)
        
        if not elf_state['evolved']:
            st.progress(progress_percent)
            st.caption(f"Feeds remaining until evolution: **{ELF_EVOLUTION_THRESHOLD - total_feeds}**")
        else:
            st.success("✨ Your Mood Elf has successfully evolved!")
            
        st.markdown("---")
        
        # Reset Button (NEW)
        if st.button("🔄 Reset Pet to Egg", use_container_width=True, help="Resets the pet's evolution status but keeps your potions."):
            reset_mood_elf()
            st.rerun()


    # --- Right Column: Potion Inventory and Feed Buttons ---
    with col_info:
        st.markdown("### 🧪 Your Potion Inventory")
        
        # Display potion status in a DataFrame
        df_potions = pd.DataFrame({
            "Potion Type": [e.capitalize() for e in POTION_MAPPING.keys()],
            "Stock": [elf_state['available_potions'][e] for e in POTION_MAPPING.keys()],
            "Times Fed": [elf_state['emotion_counts'][e] for e in POTION_MAPPING.keys()],
        }).set_index('Potion Type')
        
        st.dataframe(df_potions, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🍴 Select Potion to Feed")

        # Display potion image and feed button
        for emotion in sorted(POTION_MAPPING.keys()):
            col_img, col_btn = st.columns([0.2, 1])
            
            potion_path = POTION_MAPPING.get(emotion)
            potion_count = elf_state['available_potions'][emotion]
            
            with col_img:
                potion_image = load_pet_image(potion_path) 
                if potion_image:
                    st.image(potion_image, width=50)

            with col_btn:
                st.button(
                    f"Feed {emotion.capitalize()} Potion ({potion_count} in stock)", 
                    key=f"feed_{emotion}", 
                    on_click=feed_mood_elf, 
                    args=(emotion,), 
                    disabled=(potion_count == 0 or elf_state['evolved'])
                )

    st.markdown("---")
    if st.button("⬅ Back to Journal Home", use_container_width=True):
        st.session_state.page = "date"
        st.rerun()

# -------------------- 7. MAIN APP FLOW --------------------

if __name__ == "__main__":
    if st.session_state.page == "onboarding":
        render_onboarding_page()
    elif st.session_state.page == "fortune_draw":
        render_fortune_draw_page()
    elif st.session_state.page == "date":
        render_date_page()
    elif st.session_state.page == "mood":
        render_mood_page()
    elif st.session_state.page == "journal":
        render_journal_page()
    elif st.session_state.page == "action_page":
        render_action_page()
    elif st.session_state.page == "calendar":
        render_calendar_page()
    elif st.session_state.page == "insight":
        render_insight_page()
    elif st.session_state.page == "mood_elf":
        render_mood_elf_page()
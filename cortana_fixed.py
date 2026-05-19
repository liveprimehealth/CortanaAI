import os
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from anthropic import Anthropic
# from elevenlabs.client import ElevenLabs
# from elevenlabs.play import play

load_dotenv(".env")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

if not ANTHROPIC_API_KEY:
    print("Missing ANTHROPIC_API_KEY in .env")
    exit()

client = Anthropic(api_key=ANTHROPIC_API_KEY)
client_voice = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None

BASE_SYSTEM = """
You are Cortana, Master Raulerson's elite AI business operator.
You are loyal, direct, strategic, and focused on growing Live Prime Health.
You help with content, sales, funnels, lead generation, and revenue execution.
"""


def speak(text):
    if not client_voice:
        return

    if not text:
        return

    try:
        audio = client_voice.text_to_speech.convert(
            voice_id=os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
            model_id="eleven_multilingual_v2",
            text=str(text)[:500],
            voice_settings={
                "stability": 0.45,
                "similarity_boost": 0.75,
                "style": 0.35,
                "use_speaker_boost": True
            }
        )
        play(audio)
    except Exception as e:
        print(f"[Voice error: {e}]")

def cortana_speech_summary(text):
    text = str(text)
    if len(text) > 400:
        return "Output complete, Master Raulerson. I generated the full response on screen."
    return text


def call_claude(system_prompt, messages, max_tokens=1500):
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=messages
    )
    return response.content[0].text

def reels_builder_mode():
    try:
        with open("prompts/reels_builder_prompt.txt", "r") as f:
            builder_prompt = f.read()
    except FileNotFoundError:
        print("Missing prompts/reels_builder_prompt.txt")
        return

    system_prompt = BASE_SYSTEM + """

You are now in REELS BUILDER MODE for Master Raulerson.

Rules:
- Stay in Reels Builder Mode until user types exit.
- Ask one question at a time.
- Wait for user input after each question.
- Do not revert to default command mode.
- Do not say there is a mix-up.
- You are still Cortana. This is one of your business-building modes.
- Build the Reels Writing System for Live Prime Health.
- When enough information is collected, output the final completed Reels Writing System.
""" + "\n\n" + builder_prompt

    messages = [
        {
            "role": "user",
            "content": "Start the Live Prime Health Reels Writing System interview. Ask the first question only."
        }
    ]

    print("\n--- REELS BUILDER MODE ---")
    print("Type 'exit' to leave.\n")

    first = call_claude(system_prompt, messages)
    print("\n--- BUILDER OUTPUT ---\n")
    print(first)
    print("\n----------------------\n")

    messages.append({"role": "assistant", "content": first})

    while True:
        user_reply = input("Builder: ").strip()

        if user_reply.lower() in ["exit", "quit"]:
            print("Exiting Reels Builder Mode.")
            break

        messages.append({"role": "user", "content": user_reply})

        output = call_claude(system_prompt, messages)
        print("\n--- BUILDER OUTPUT ---\n")
        print(output)
        print("\n----------------------\n")

        messages.append({"role": "assistant", "content": output})

def reels_mode():
    try:
        with open("memory/reels_system_prompt.txt", "r") as f:
            reels_prompt = f.read()
    except FileNotFoundError:
        print("Missing memory/reels_system_prompt.txt")
        return

    topic = input("Topic: ").strip()

    system_prompt = BASE_SYSTEM + "\n\n" + reels_prompt

    messages = [
        {
            "role": "user",
            "content": f"Write 5 viral Instagram reels about: {topic}"
        }
    ]

    output = call_claude(system_prompt, messages, max_tokens=2000)
    print("\n--- REELS OUTPUT ---\n")
    print(output)
    print("\n----------------------\n")



def get_today_pillar():
    from datetime import datetime

    day = datetime.now().strftime("%A").upper()

    try:
        with open("content_calendar.txt", "r") as f:
            lines = f.readlines()
    except:
        return day, "General Health"

    calendar = {}

    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            calendar[k.strip().upper()] = v.strip()

    return day, calendar.get(day, "General Health")


def dailycontent_mode():

    try:
        with open("memory/reels_system_prompt.txt", "r") as f:
            reels_prompt = f.read()
    except:
        print("Missing reels system prompt.")
        return

    day, pillar = get_today_pillar()

    system_prompt = BASE_SYSTEM + "\n\n" + reels_prompt

    prompt = f"""
Today is {day}.
Today's content pillar is: {pillar}.

Generate:
1. One controversial reel
2. One relatable reel
3. One educational reel
4. One story reel
5. One conversion CTA reel

For EACH include:
- Hook
- Full script
- Visual ideas
- On-screen text
- CTA

Use Live Prime Health voice.
"""

    output = call_claude(
        system_prompt,
        [{"role": "user", "content": prompt}],
        max_tokens=3000
    )

    print(f"\n--- DAILY CONTENT ({day} / {pillar}) ---\n")
    print(output)
    print("\n----------------------\n")

    speak("Daily content batch complete, Master Raulerson.")





def get_google_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    gc = gspread.authorize(creds)

    sheet = gc.open("Cortana Leads").sheet1
    return sheet


def get_sheet_leads():
    try:
        sheet = get_google_sheet()
        records = sheet.get_all_records()
        return records
    except Exception as e:
        print(f"Google Sheets error: {e}")
        return []


def add_lead_to_sheet(name, handle, status, goal, pain, last_contact, notes):
    sheet = get_google_sheet()

    row = [
        name,
        handle,
        status,
        last_contact,
        notes,
        "Manual Cortana",
        "",
        goal
    ]

    sheet.append_row(row)

def money_mode():

    records = get_sheet_leads()

    if not records:
        print("No leads found in Google Sheets.")
        return

    hot = []
    followup = []
    new = []

    for r in records:
        name = str(r.get("Name", "")).strip()
        handle = str(r.get("Contact", "") or r.get("IG Handle", "")).strip()
        status = str(r.get("Status", "")).strip().lower()
        goal = str(r.get("Goal", "")).strip()
        pain = str(r.get("Pain Point", "")).strip()
        last_contact = str(r.get("Last Contact", "")).strip()
        notes = str(r.get("Notes", "")).strip()

        if not name:
            continue

        lead = {
            "name": name,
            "handle": handle,
            "goal": goal,
            "pain": pain,
            "last_contact": last_contact,
            "notes": notes
        }

        if status == "hot":
            hot.append(lead)
        elif status in ["followup", "follow up", "contacted"]:
            followup.append(lead)
        elif status in ["new", ""]:
            new.append(lead)

    day, pillar = get_today_pillar()

    print(f"""
🔥 DAILY MONEY REPORT — LIVE PRIME HEALTH

TODAY'S CONTENT PILLAR:
{pillar}

HOT LEADS:
{hot if hot else "None"}

FOLLOW UPS:
{followup if followup else "None"}

NEW LEADS:
{new if new else "None"}

TOP PRIORITIES:
1. Message all hot leads first
2. Follow up with all follow-up leads
3. Qualify new leads
4. Post today's content pillar: {pillar}
5. Push calls aggressively

GOAL:
Book at least 2 calls today.
""")

    speak("Money report ready, Master Raulerson.")

def addlead_mode():
    print("\n--- ADD LEAD ---")
    name = input("Name: ").strip()
    handle = input("IG Handle: ").strip()
    status = input("Status (new/followup/hot): ").strip().lower()
    goal = input("Goal: ").strip()
    pain = input("Pain Point: ").strip()
    last_contact = input("Last Contact (today/yesterday/etc): ").strip()
    notes = input("Notes: ").strip()

    if not name:
        print("Lead not added. Name is required.")
        return

    line = f"{name} | {handle} | {status} | {goal} | {pain} | {last_contact} | {notes}\n"

    lead_file = Path("leads.txt")

    if not lead_file.exists():
        lead_file.write_text("Name | IG Handle | Status | Goal | Pain Point | Last Contact | Notes\n")

    with open("leads.txt", "a") as f:
        f.write(line)

    try:
        add_lead_to_sheet(name, handle, status, goal, pain, last_contact, notes)
        print(f"\nLead added to Google Sheets: {name}")
    except Exception as e:
        print(f"\nLead saved locally, but Google Sheets failed: {e}")

    print(f"\nLead added: {name}")
    speak(f"Lead added. {name} is now in the system.")


def followup_mode():
    print("\n--- FOLLOW UP GENERATOR ---")
    name = input("Name: ").strip()
    goal = input("Their goal: ").strip()
    pain = input("Their pain/objection: ").strip()
    status = input("Status (new/followup/hot): ").strip()

    prompt = f"""
Write 3 short Instagram DM follow-up messages for this lead.

Lead:
Name: {name}
Goal: {goal}
Pain/Objection: {pain}
Status: {status}

Rules:
- Sound like Quinn Raulerson
- Direct, real, helpful
- Not needy
- Not corporate
- Move them toward a 15-minute call
- Keep each message under 60 words
"""

    output = call_claude(BASE_SYSTEM, [{"role": "user", "content": prompt}], max_tokens=1000)

    print("\n--- FOLLOW UP OPTIONS ---\n")
    print(output)
    print("\n----------------------\n")

    speak("Follow up messages generated, Master Raulerson.")


def main():
    print("Cortana Systems Online.")
    speak("Cortana systems online. How may I assist you, Master Raulerson?")
    print("Commands: /reelsbuilder, /reels, /dailycontent, /quit\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["/quit", "quit", "exit"]:
            print("Shutting down.")
            speak("Shutting down. I will be here when you need me.")
            break

        elif user_input.lower() == "/reelsbuilder":
            reels_builder_mode()

        elif user_input.lower() == "/reels":
            reels_mode()

        elif user_input.lower() == "/dailycontent":
            dailycontent_mode()

        elif user_input.lower() == "/money":
            money_mode()

        elif user_input.lower() == "/addlead":
            addlead_mode()

        elif user_input.lower() == "/followup":
            followup_mode()

        else:
            messages = [
                {
                    "role": "user",
                    "content": user_input
                }
            ]

            output = call_claude(BASE_SYSTEM, messages)

            print("\n--- CORTANA OUTPUT ---\n")
            print(output)
            print("\n----------------------\n")

            speak(cortana_speech_summary(output))


if __name__ == "__main__":
    main()

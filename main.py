"""Voice-controlled desktop assistant.

Listens for a spoken command (or reads typed commands with --text), matches it
against a table of commands, and speaks the result.

    python main.py           # voice mode (needs a microphone)
    python main.py --text    # type commands instead
"""
import argparse
import datetime
import os
import random
import smtplib
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Callable, List, Optional

ASSISTANT_NAME = "Nova"
NOTES_FILE = "notes.txt"


# ---------------------------------------------------------------- input/output

class Assistant:
    def __init__(self, text_mode: bool = False):
        self.text_mode = text_mode
        self._engine = None
        self._recognizer = None

    def speak(self, message: str) -> None:
        print(f"{ASSISTANT_NAME}: {message}")
        if self.text_mode:
            return
        if self._engine is None:
            import pyttsx3
            self._engine = pyttsx3.init()
        self._engine.say(message)
        self._engine.runAndWait()

    def listen(self, prompt: str = "Listening...") -> str:
        if self.text_mode:
            try:
                return input("You: ").strip().lower()
            except EOFError:
                return "bye"

        import speech_recognition as sr
        if self._recognizer is None:
            self._recognizer = sr.Recognizer()
            self._recognizer.pause_threshold = 0.7
        with sr.Microphone() as source:
            print(prompt)
            audio = self._recognizer.listen(source)
        try:
            query = self._recognizer.recognize_google(audio, language="en-in")
        except (sr.UnknownValueError, sr.RequestError) as exc:
            print(f"(could not understand: {exc.__class__.__name__})")
            return ""
        print(f"You: {query}")
        return query.strip().lower()


# --------------------------------------------------------------------- actions

def open_site(url: str) -> Callable[["Assistant", str], None]:
    def action(bot: Assistant, _query: str) -> None:
        bot.speak(f"Opening {url}")
        webbrowser.open(url)
    return action


def open_app(command: str, label: str) -> Callable[["Assistant", str], None]:
    def action(bot: Assistant, _query: str) -> None:
        bot.speak(f"Opening {label}")
        try:
            if sys.platform.startswith("win"):
                os.startfile(command)  # type: ignore[attr-defined]
            else:
                subprocess.Popen([command])
        except OSError:
            bot.speak(f"Sorry, I couldn't find {label} on this computer")
    return action


def reply(text: str) -> Callable[["Assistant", str], None]:
    return lambda bot, _query: bot.speak(text)


def tell_time(bot: Assistant, _query: str) -> None:
    bot.speak(datetime.datetime.now().strftime("It's %I:%M %p"))


def tell_day(bot: Assistant, _query: str) -> None:
    bot.speak(datetime.datetime.now().strftime("Today is %A, %B %d"))


def wikipedia_summary(bot: Assistant, query: str) -> None:
    import wikipedia
    topic = strip_trigger(query, ("wikipedia", "search", "who is", "tell me about"))
    if not topic:
        bot.speak("What should I look up?")
        return
    bot.speak(f"Searching Wikipedia for {topic}")
    try:
        bot.speak(wikipedia.summary(topic, sentences=2, auto_suggest=False))
    except wikipedia.DisambiguationError as exc:
        bot.speak(f"That's ambiguous. Did you mean {', '.join(exc.options[:3])}?")
    except (wikipedia.PageError, wikipedia.WikipediaException):
        bot.speak(f"I couldn't find a page for {topic}")


def tell_joke(bot: Assistant, _query: str) -> None:
    import pyjokes
    bot.speak(pyjokes.get_joke())


def flip_coin(bot: Assistant, _query: str) -> None:
    bot.speak(f"It's {random.choice(['heads', 'tails'])}")


def take_note(bot: Assistant, _query: str) -> None:
    bot.speak("What should I write down?")
    note = bot.listen("Dictate your note...")
    if not note:
        bot.speak("I didn't catch that, so no note was saved")
        return
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M}] {note}\n")
    bot.speak(f"Saved to {NOTES_FILE}")


def send_email(bot: Assistant, _query: str) -> None:
    """Credentials come from the environment, never from code:
    ASSISTANT_EMAIL, ASSISTANT_EMAIL_APP_PASSWORD (a Gmail app password)."""
    sender = os.environ.get("ASSISTANT_EMAIL")
    password = os.environ.get("ASSISTANT_EMAIL_APP_PASSWORD")
    if not sender or not password:
        bot.speak("Email isn't set up. Set ASSISTANT_EMAIL and ASSISTANT_EMAIL_APP_PASSWORD first")
        return
    bot.speak("Who should I send it to? Please type or say the address")
    to = bot.listen("Recipient...").replace(" at ", "@").replace(" dot ", ".").replace(" ", "")
    if "@" not in to:
        bot.speak("That doesn't look like an email address")
        return
    bot.speak("What should the message say?")
    body = bot.listen("Message...")
    if not body:
        bot.speak("Empty message, cancelled")
        return

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, to, f"Message from {ASSISTANT_NAME}"
    msg.set_content(body)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        bot.speak("Email sent")
    except (smtplib.SMTPException, OSError) as exc:
        bot.speak(f"Sorry, the email failed: {exc.__class__.__name__}")


# ------------------------------------------------------------- command table

@dataclass
class Command:
    triggers: List[str]
    action: Callable[[Assistant, str], None]
    help: str


COMMANDS: List[Command] = [
    Command(["time"], tell_time, "what time is it"),
    Command(["day", "date"], tell_day, "what day is it"),
    Command(["wikipedia", "who is", "tell me about"], wikipedia_summary,
            "tell me about <topic> / wikipedia <topic>"),
    Command(["joke"], tell_joke, "tell me a joke"),
    Command(["flip a coin", "coin"], flip_coin, "flip a coin"),
    Command(["take a note", "take note", "note"], take_note, "take a note"),
    Command(["send email", "send an email", "email"], send_email, "send an email"),
    Command(["open youtube"], open_site("https://www.youtube.com"), "open youtube"),
    Command(["open google"], open_site("https://www.google.com"), "open google"),
    Command(["open stackoverflow", "open stack overflow"], open_site("https://stackoverflow.com"),
            "open stack overflow"),
    Command(["open github"], open_site("https://github.com"), "open github"),
    Command(["open whatsapp"], open_site("https://web.whatsapp.com"), "open whatsapp"),
    Command(["open chrome"], open_app("chrome", "Chrome"), "open chrome"),
    Command(["open code", "open vs code"], open_app("code", "VS Code"), "open vs code"),
    Command(["open calculator"], open_app("calc", "the calculator"), "open calculator"),
    Command(["your name", "who are you"], reply(f"I'm {ASSISTANT_NAME}, your desktop assistant"),
            "what's your name"),
    Command(["how are you"], reply("Doing great, thanks for asking!"), "how are you"),
]

EXIT_WORDS = ("bye", "exit", "quit", "shutdown", "stop")


def strip_trigger(query: str, triggers) -> str:
    for t in sorted(triggers, key=len, reverse=True):
        query = query.replace(t, " ")
    return " ".join(w for w in query.split() if w not in {"on", "from", "about", "me", "the"})


def match_command(query: str) -> Optional[Command]:
    """Longest matching trigger wins, so 'open google' beats a bare 'google'."""
    best, best_len = None, 0
    for cmd in COMMANDS:
        for t in cmd.triggers:
            if t in query and len(t) > best_len:
                best, best_len = cmd, len(t)
    return best


def is_exit(query: str) -> bool:
    return any(query == w or query.startswith(w + " ") for w in EXIT_WORDS)


def show_help(bot: Assistant) -> None:
    bot.speak("Here's what I can do:")
    for cmd in COMMANDS:
        print(f"  - {cmd.help}")


# ------------------------------------------------------------------------ main

def run(bot: Assistant) -> None:
    hour = datetime.datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    bot.speak(f"{greeting}! I'm {ASSISTANT_NAME}. Say 'help' to hear what I can do.")
    while True:
        query = bot.listen()
        if not query:
            continue
        if is_exit(query):
            bot.speak("Goodbye!")
            return
        if "help" in query:
            show_help(bot)
            continue
        cmd = match_command(query)
        if cmd is None:
            bot.speak("Sorry, I don't know that one yet. Say 'help' for a list.")
            continue
        try:
            cmd.action(bot, query)
        except Exception as exc:  # keep the assistant alive if one command breaks
            bot.speak(f"Something went wrong: {exc.__class__.__name__}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Voice-controlled desktop assistant")
    parser.add_argument("--text", action="store_true", help="type commands instead of speaking")
    run(Assistant(text_mode=parser.parse_args().text))

# Desktop Voice Assistant

A Python voice assistant ("Nova") that listens for spoken commands, matches them against a
command table and answers out loud. It can tell the time, look things up on Wikipedia, take
notes, send email, open websites and apps, and more. It also has a text mode for typing
commands, so you can run it without a microphone.

```
$ python main.py --text
Nova: Good afternoon! I'm Nova. Say 'help' to hear what I can do.
You: tell me about alan turing
Nova: Searching Wikipedia for alan turing
Nova: Alan Mathison Turing (23 June 1912 – 7 June 1954) was an English mathematician and logician ...
You: flip a coin
Nova: It's heads
You: bye
Nova: Goodbye!
```

## Commands

| Say | What happens |
|---|---|
| "what time is it" / "what day is it" | Speaks the current time or date |
| "tell me about *topic*" / "wikipedia *topic*" | Reads a 2-sentence Wikipedia summary, and handles ambiguous topics |
| "take a note" | Dictate a note; it's appended with a timestamp to `notes.txt` |
| "send an email" | Asks for the recipient and message, then sends via Gmail SMTP |
| "open youtube / google / github / stack overflow / whatsapp" | Opens the site in your browser |
| "open chrome / vs code / calculator" | Launches the app |
| "tell me a joke", "flip a coin", "how are you" | Small talk |
| "help" | Lists all commands |
| "bye" / "exit" | Quits |

## How it works

- **Command table.** Each command is a `Command(triggers, action, help)` entry. The
  longest matching trigger wins, so "open google" is never mistaken for a shorter
  overlapping phrase. To add a command, add one line to `COMMANDS`.
- **Speech in and out.** Google Speech Recognition (via `SpeechRecognition`) handles
  listening, and `pyttsx3` speaks offline. Both are loaded lazily, so text mode needs neither.
- **Fault tolerant.** A failing command (no network, app not installed) is reported out
  loud instead of crashing the assistant.

## Setup

```bash
pip install -r requirements.txt     # PyAudio is needed for the microphone
python main.py                      # voice mode
python main.py --text               # keyboard mode
python -m pytest                    # run the tests
```

### Email (optional)

Credentials are read from environment variables and are never stored in code. Use a
[Gmail app password](https://support.google.com/accounts/answer/185833), not your real password:

```bash
export ASSISTANT_EMAIL="you@gmail.com"
export ASSISTANT_EMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
```

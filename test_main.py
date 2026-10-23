import main


def name_of(query):
    cmd = main.match_command(query)
    return cmd.help if cmd else None


def test_matches_basic_commands():
    assert name_of("what time is it") == "what time is it"
    assert name_of("flip a coin please") == "flip a coin"
    assert name_of("open stackoverflow") == "open stack overflow"


def test_longest_trigger_wins():
    # "open google" must not be swallowed by a shorter overlapping trigger
    assert name_of("open google") == "open google"
    assert name_of("send an email to my friend") == "send an email"


def test_unknown_command():
    assert main.match_command("make me a sandwich") is None


def test_exit_words():
    assert main.is_exit("bye")
    assert main.is_exit("quit now")
    assert not main.is_exit("tell me about the byelection")


def test_strip_trigger_extracts_topic():
    assert main.strip_trigger("tell me about alan turing", ["tell me about"]) == "alan turing"
    assert main.strip_trigger("wikipedia python programming", ["wikipedia"]) == "python programming"


def test_time_reply(capsys):
    main.tell_time(main.Assistant(text_mode=True), "time")
    assert "It's" in capsys.readouterr().out


def test_email_refuses_without_env(monkeypatch, capsys):
    monkeypatch.delenv("ASSISTANT_EMAIL", raising=False)
    monkeypatch.delenv("ASSISTANT_EMAIL_APP_PASSWORD", raising=False)
    main.send_email(main.Assistant(text_mode=True), "send email")
    assert "isn't set up" in capsys.readouterr().out


def test_date_question_is_not_a_wikipedia_search():
    assert name_of("what is the date") == "what day is it"

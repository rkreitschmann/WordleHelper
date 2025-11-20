import sqlite3
import pytest

from Wordle_helper import WordleHelper, graceful_exit


@pytest.fixture
def helper(tmp_path):
    db_file = tmp_path / "test_words.db"
    h = WordleHelper(str(db_file))
    yield h
    try:
        h.close()
    except Exception:
        pass


def test_database_creation_and_load(helper):
    cur = helper.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
    assert cur.fetchone() is not None

    # loading words should populate the DB (uses JSON if present, otherwise fallback)
    helper.load_words()
    cur.execute('SELECT COUNT(*) FROM words')
    assert cur.fetchone()[0] > 0


def test_filter_known_wrong_and_yellow(helper):
    words = ["ALONE", "BANAL", "CRANE", "BRAVE", "ABODE"]
    cur = helper.conn.cursor()
    cur.executemany('INSERT OR IGNORE INTO words (word, length) VALUES (?, ?)',
                    [(w, len(w)) for w in words])
    helper.conn.commit()

    # known pattern: first letter A
    res = helper.filter_words(word_length=5, known_letters="A____")
    assert {"ALONE", "ABODE"}.issubset(set(res))

    # wrong letters: exclude words containing B
    res2 = helper.filter_words(word_length=5, wrong_letters="B")
    assert "BRAVE" not in res2 and "BANAL" not in res2

    # yellow: letter A exists somewhere but not at position 1
    res3 = helper.filter_words(word_length=5, wrong_positions=[(1, 'A')])
    assert "BANAL" in res3 and "ALONE" not in res3


def test_letter_frequency_db_and_direct(helper):
    words = ["APPLE", "ALERT", "ANGLE"]
    cur = helper.conn.cursor()
    cur.executemany('INSERT OR IGNORE INTO words (word, length) VALUES (?, ?)',
                    [(w, len(w)) for w in words])
    helper.conn.commit()

    freq_db = helper.get_letter_frequency(None, word_length=5)
    assert freq_db.get('A', 0) >= 1
    assert freq_db.get('L', 0) >= 2

    freq_direct = helper.get_letter_frequency(words, word_length=5)
    assert freq_direct['A'] == 3


def test_scoring_exact_values_and_suggestions(helper):
    words = ["SLATE", "CRONY", "AUDIO", "AEIOU"]
    cur = helper.conn.cursor()
    cur.executemany('INSERT OR IGNORE INTO words (word, length) VALUES (?, ?)',
                    [(w, len(w)) for w in words])
    helper.conn.commit()

    freq = helper.get_letter_frequency(words, word_length=5)
    score_audio = helper.calculate_word_score("AUDIO", freq)
    score_aeiou = helper.calculate_word_score("AEIOU", freq)
    # exact expected values computed from the algorithm and given frequency
    # AUDIO: position_score=11.8, vowel_bonus capped=1500, start_bonus=300 -> 11.8+1500+300 = 1811.8
    # AEIOU: position_score=12.6, vowel_bonus capped=1500, start_bonus=300 -> 12.6+1500+300 = 1812.6
    assert score_audio == pytest.approx(1811.8, rel=1e-6)
    assert score_aeiou == pytest.approx(1812.6, rel=1e-6)

    suggested = helper.suggest_best_words(words, top_n=3)
    assert isinstance(suggested, list) and len(suggested) <= 3


def test_graceful_exit_closes_connection(helper):
    with pytest.raises(SystemExit) as se:
        graceful_exit(helper, "bye")
    assert se.value.code == 0

    with pytest.raises(sqlite3.ProgrammingError):
        helper.conn.cursor()


def test_constraints_and_ranking(helper):
    words = [
        "CRANE", "CRANK", "CRAZY", "ALONE", "BANAL", "BRAVE",
        "ABODE", "AUDIO", "AEIOU", "LLAMA", "PUPPY"
    ]
    cur = helper.conn.cursor()
    cur.executemany('INSERT OR IGNORE INTO words (word, length) VALUES (?, ?)',
                    [(w, len(w)) for w in words])
    helper.conn.commit()

    # 1) Filter: second letter A, exclude R,S,T
    filtered = helper.filter_words(word_length=5, known_letters="_A___", wrong_letters="RST")
    # Every returned word must have 'A' in position 2 and must not contain R, S, or T
    for w in filtered:
        assert len(w) == 5
        assert w[1] == 'A'
        assert all(ch not in w for ch in list("RST"))

    # 2) Suggestions should be subset of filtered
    suggestions = helper.suggest_best_words(filtered, top_n=5)
    assert set(suggestions).issubset(set(filtered))

    # 3) Yellow letter: letter A exists but not at position 1
    yellow_res = helper.filter_words(word_length=5, wrong_positions=[(1, 'A')])
    for w in yellow_res:
        assert 'A' in w
        assert w[0] != 'A'

    # 4) Repeat penalty: PUPPY should score less than CRAZY given same frequency base
    freq = helper.get_letter_frequency(words, word_length=5)
    score_puppy = helper.calculate_word_score('PUPPY', freq)
    score_crazy = helper.calculate_word_score('CRAZY', freq)
    assert score_puppy < score_crazy

    # 5) Letter frequency counts: ensure at least some expected counts
    freq_all = helper.get_letter_frequency(words, word_length=5)
    assert freq_all.get('A', 0) >= 4  # many words contain A

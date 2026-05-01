import pytest
from qa_bot.text_utils import clean_answer, truncate_at_word, format_score


class TestCleanAnswer:
    def test_removes_all_linebreaks(self):
        assert clean_answer("line\nbreak") == "line break"
        assert clean_answer("multiple\n\nbreaks") == "multiple breaks"

    def test_collapses_multiple_spaces(self):
        assert clean_answer("word    word") == "word word"

    def test_fixes_missing_space_after_period(self):
        assert clean_answer("Kalenderjahr.Hinweis") == "Kalenderjahr. Hinweis"

    def test_fixes_missing_space_after_exclamation(self):
        assert clean_answer("Achtung!Gefahr") == "Achtung! Gefahr"

    def test_fixes_missing_space_after_colon(self):
        assert clean_answer("Hinweis:Der") == "Hinweis: Der"

    def test_fixes_number_dot_uppercase(self):
        result = clean_answer("Bearbeitung.2.1.Ist ein Test")
        assert "2.1. Ist" in result

    def test_fixes_concatenated_words(self):
        assert clean_answer("AuszahlungFremdkunde") == "Auszahlung Fremdkunde"
        assert clean_answer("AZuB") == "AZuB"

    def test_strips_whitespace(self):
        assert clean_answer("  text  ") == "text"


class TestTruncateAtWord:
    def test_no_truncation_when_short(self):
        assert truncate_at_word("short text", 100) == "short text"

    def test_truncates_at_word_boundary(self):
        result = truncate_at_word("one two three four five", 15)
        assert result.startswith("one two")
        assert result.endswith(" ...")


class TestFormatScore:
    def test_score_labels(self):
        assert "sehr relevant" in format_score(10.0)
        assert "wenig relevant" in format_score(2.0)

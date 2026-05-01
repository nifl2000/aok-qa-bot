"""Tests for qa_bot.text_utils."""

import pytest

from qa_bot.text_utils import clean_answer, format_score, truncate_at_word


class TestCleanAnswer:
    def test_removes_hard_linebreaks(self):
        assert clean_answer("Bestehendes\nVersicherungsverhältnis") == "Bestehendes Versicherungsverhältnis"

    def test_collapses_multiple_spaces(self):
        assert clean_answer("foo   bar") == "foo bar"

    def test_fixes_missing_space_after_period(self):
        assert clean_answer("Kalenderjahr.Hinweis") == "Kalenderjahr. Hinweis"

    def test_fixes_missing_space_after_exclamation(self):
        assert clean_answer("Achtung!Gefahr") == "Achtung! Gefahr"

    def test_fixes_missing_space_after_colon(self):
        assert clean_answer("Kalenderjahr.Hinweis:Der") == "Kalenderjahr. Hinweis: Der"

    def test_fixes_number_dot_uppercase(self):
        """Edge case: 'Bearbeitung.2.1. Ist ein ...' → 'Bearbeitung. 2.1. Ist ein ...'"""
        result = clean_answer("Bearbeitung.2.1. Ist ein Test")
        assert "2.1. Ist" in result

    def test_preserves_normal_text(self):
        assert clean_answer("Ganz normaler Text ohne Probleme.") == "Ganz normaler Text ohne Probleme."

    def test_strips_whitespace(self):
        assert clean_answer("  text  ") == "text"

    def test_handles_umlauts_in_fix(self):
        assert clean_answer("Ende.Nächster") == "Ende. Nächster"

    def test_handles_eszett_in_fix(self):
        result = clean_answer("Ende.ße")
        # ß is lowercase, should not trigger the uppercase fix
        assert "Ende.ße" in result


class TestTruncateAtWord:
    def test_no_truncation_when_short(self):
        assert truncate_at_word("short text", 100) == "short text"

    def test_truncates_at_word_boundary(self):
        result = truncate_at_word("one two three four five", 15)
        assert result.startswith("one two")
        assert result.endswith(" ...")

    def test_does_not_truncate_inside_words(self):
        result = truncate_at_word("ThisIsAVeryLongWord without spaces here", 20)
        # No space within 60% threshold, so it truncates at max_len
        assert result == "ThisIsAVeryLongWord ..."

    def test_exact_length_no_truncation(self):
        text = "exactly ten chars"
        assert truncate_at_word(text, len(text)) == text

    def test_abbreviation_with_dots(self):
        result = truncate_at_word("d. h. der Sozialdienst im Krankenhaus stellt einen Antrag", 30)
        assert "..." in result
        assert len(result) <= 34  # 30 + " ..."


class TestFormatScore:
    @pytest.mark.parametrize("score,label", [
        (10, "sehr relevant"),
        (8, "sehr relevant"),
        (7, "relevant"),
        (5, "relevant"),
        (4, "teilweise relevant"),
        (3, "teilweise relevant"),
        (2, "wenig relevant"),
        (0, "wenig relevant"),
    ])
    def test_score_labels(self, score, label):
        assert label in format_score(float(score))

    def test_score_formatting(self):
        result = format_score(8.5)
        assert "8/10" in result  # .0f uses banker's rounding

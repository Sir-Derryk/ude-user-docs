# tests/test_normalizer.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from ude.normalizer import CommentNormalizer


def test_normalize_empty_comment():
    """Verify that empty comments return empty cleaned text and empty metadata."""
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment("")
    assert clean_text == ""
    assert metadata == {
        "params": {},
        "returns": None,
        "author": None,
        "version": None,
    }


def test_normalize_none_comment():
    """Verify that None inputs are handled gracefully."""
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(None)
    assert clean_text == ""
    assert metadata == {
        "params": {},
        "returns": None,
        "author": None,
        "version": None,
    }


def test_normalize_javadoc_format():
    """Verify that Javadoc comments are correctly cleaned and tags are extracted.

    Satisfies TSK-NML-01
    """
    raw_comment = r"""
    /**
     * This is a sample class method.
     * It processes incoming data packets.
     *
     * @param data The raw input byte array.
     * @param offset The starting offset in the buffer.
     * @return The number of bytes successfully written.
     * @author Jane Doe
     * @version 1.0.4
     */
    """
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(raw_comment)

    expected_clean = (
        "This is a sample class method.\n"
        "It processes incoming data packets."
    )
    assert clean_text == expected_clean

    assert metadata["params"] == {
        "data": "The raw input byte array.",
        "offset": "The starting offset in the buffer.",
    }
    assert metadata["returns"] == "The number of bytes successfully written."
    assert metadata["author"] == "Jane Doe"
    assert metadata["version"] == "1.0.4"


def test_normalize_doxygen_format():
    """Verify that Doxygen comments are correctly cleaned and tags are extracted.

    Satisfies TSK-NML-01
    """
    raw_comment = r"""
    /// \brief Main worker function.
    ///
    /// Detailed description of the worker function that handles pipeline execution.
    ///
    /// \param count The number of iterations to perform.
    /// \return True if successful, false otherwise.
    /// \author John Smith
    /// \version 2.1.0
    """
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(raw_comment)

    expected_clean = (
        "Main worker function.\n\n"
        "Detailed description of the worker function that handles pipeline execution."
    )
    assert clean_text == expected_clean

    assert metadata["params"] == {
        "count": "The number of iterations to perform.",
    }
    assert metadata["returns"] == "True if successful, false otherwise."
    assert metadata["author"] == "John Smith"
    assert metadata["version"] == "2.1.0"


def test_normalize_google_style():
    """Verify that Google/Python-style Args and Returns blocks are normalized and extracted."""
    raw_comment = r"""
    Perform calculation on the inputs.

    Args:
        x (int): The horizontal coordinate.
        y (int): The vertical coordinate.

    Returns:
        float: The distance from origin.
    """
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(raw_comment)

    assert "Perform calculation on the inputs." in clean_text
    # Args/Returns blocks should be extracted and stripped from clean_text
    assert "Args:" not in clean_text
    assert "Returns:" not in clean_text

    assert metadata["params"] == {
        "x": "The horizontal coordinate.",
        "y": "The vertical coordinate.",
    }
    assert metadata["returns"] == "float: The distance from origin."


def test_doxygen_alternate_slash_comments():
    """Verify alternate Doxygen comment patterns like //! and /*! are handled."""
    raw_comment = r"""
    /*!
     * \brief Alternating format.
     * \param name Name of the user.
     */
    """
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(raw_comment)

    assert clean_text == "Alternating format."
    assert metadata["params"] == {"name": "Name of the user."}


def test_malformed_tags():
    """Verify robust handling of malformed tags (e.g. empty or only spaces)."""
    raw_comment = r"""
    /**
     * @param
     * @return
     */
    """
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(raw_comment)
    assert clean_text == ""
    assert metadata["params"] == {}
    assert metadata["returns"] is None


def test_single_line_javadoc():
    """Verify that single-line Javadoc block statements are stripped correctly."""
    raw_comment = "/** Single line comment */"
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(raw_comment)
    assert clean_text == "Single line comment"
    assert metadata["params"] == {}


def test_normalize_google_style_no_type():
    """Verify that Google-style Returns block without a type is normalized correctly."""
    raw_comment = r"""
    Perform calculation on the inputs.

    Returns:
        The distance from origin.
    """
    normalizer = CommentNormalizer()
    clean_text, metadata = normalizer.normalize_comment(raw_comment)
    assert metadata["returns"] == "The distance from origin."


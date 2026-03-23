import regex

def find_test_formation_mentions(text: str) -> list[str]:
    """Find mentions of DST/transient tests in combination with known formations.

    Matches any of:
      - DST, mini DST, Drill stem test, transient test
    followed (within ~200 characters) by any of:
      - Tare, Nise, Kvitnos, Lange, Lysing
    or the reverse order (formation then test type).

    Each keyword allows up to 2 spelling mistakes (character substitutions,
    insertions, or deletions) via fuzzy matching ({e<=2}).
    Short 3-letter terms (DST) allow at most 1 error to avoid false positives.

    Returns a list of matched substrings.
    """
    test_types = (
        r"(?:"
        r"(?:mini\s+DST){e<=1}"
        r"|(?:DST){e<=1}"
        r"|(?:drill\s+stem\s+test){e<=1}"
        r"|(?:transient\s+test){e<=1}"
        r")"
    )
    formations = (
        r"(?:"
        r"(?:Tare){e<=1}"
        r"|(?:Nise){e<=1}"
        r"|(?:Kvitnos){e<=1}"
        r"|(?:Lange){e<=1}"
        r"|(?:Lysing){e<=1}"
        r")"
    )
    between = r"[\s\S]{0,200}?"

    pattern = regex.compile(
        rf"(?:{test_types}{between}{formations}|{formations}{between}{test_types})",
        regex.IGNORECASE | regex.BESTMATCH,
    )
    return pattern.findall(text)
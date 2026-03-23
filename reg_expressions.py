import regex

_FORMATION_PATTERN = regex.compile(
    r"(?:Tare|Nise|Kvitnos|Lange|Lysing)",
    regex.IGNORECASE,
)

_TEST_TYPE_PATTERN = regex.compile(
    r"(?:"
    r"(?:mini\s+DST){e<=1}"
    r"|(?:DST){e<=1}"
    r"|(?:drill\s+stem\s+test){e<=1}"
    r"|(?:transient\s+test){e<=1}"
    r")",
    regex.IGNORECASE | regex.BESTMATCH,
)


def find_test_formation_mentions(text: str) -> list[str]:
    """Two-step search: first check the text contains a formation, then find
    any test type within 200 characters of each formation match.

    Step 1 — scan for formations (Tare, Nise, Kvitnos, Lange, Lysing).
    Step 2 — for each formation found, extract a 200-char window around it
              and check whether a test type (DST, mini DST, drill stem test,
              transient test) appears in that window.

    Each keyword allows up to 1 spelling mistake via fuzzy matching ({e<=1}).

    Returns a list of window substrings that contain both a formation and a
    test type, one entry per matching formation occurrence.
    """
    results = []
    for fm in _FORMATION_PATTERN.finditer(text):
        # 200 chars before and after the formation match
        start = max(0, fm.start() - 200)
        end = min(len(text), fm.end() + 200)
        window = text[start:end]
        if _TEST_TYPE_PATTERN.search(window):
            results.append(window.strip())
    return results
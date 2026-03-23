import regex

_FORMATION_PATTERN = regex.compile(
    r"(?:Tare|Nise|Kvitnos|Lange|Lysing)",
    regex.IGNORECASE,
)

_TEST_TYPE_PATTERN = regex.compile(
    r"(?:(?:dst|drill|stem|test|transient)\s)",
    regex.IGNORECASE,
)


def _highlight(window: str) -> str:
    """Wrap formation matches in cyan bold and test type matches in yellow bold."""
    result = _TEST_TYPE_PATTERN.sub(
        lambda m: f"[bold yellow]{m.group()}[/bold yellow]", window
    )
    result = _FORMATION_PATTERN.sub(
        lambda m: f"[bold yellow]{m.group()}[/bold yellow]", result
    )
    return result


def find_test_formation_mentions(text: str) -> list[str]:
    """Two-step search: first check the text contains a formation, then find
    any test type within 200 characters of each formation match.

    Step 1 — scan for formations (Tare, Nise, Kvitnos, Lange, Lysing).
    Step 2 — for each formation found, extract a 200-char window around it
              and check whether a test type (DST, mini DST, drill stem test,
              transient test) appears in that window.

    Returns a list of highlighted window substrings (rich markup).
    """
    results = []
    for fm in _FORMATION_PATTERN.finditer(text):
        # 500 chars before and after the formation match
        start = max(0, fm.start() - 500)
        end = min(len(text), fm.end() + 500)
        window = text[start:end]
        if _TEST_TYPE_PATTERN.search(window):
            results.append(_highlight(window.strip()))
    return results
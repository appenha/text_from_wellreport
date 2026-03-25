import regex

_FORMATION_PATTERN = regex.compile(
    r"(?:\b(?:Tare|Nise|Kvitnos|Lange|Lysing)\b)",
    regex.IGNORECASE,
)

# _TEST_TYPE_PATTERN = regex.compile(
#     r"(?:(?:\bdst)|drill stem test|fluid sample|mini-dst|transient test)",
#     regex.IGNORECASE,
# )


# def _highlight(window: str) -> str:
#     """Wrap formation matches in cyan bold and test type matches in yellow bold."""
#     result = _TEST_TYPE_PATTERN.sub(
#         lambda m: f"[bold yellow]{m.group()}[/bold yellow]", window
#     )
#     result = _FORMATION_PATTERN.sub(
#         lambda m: f"[bold yellow]{m.group()}[/bold yellow]", result
#     )
#     return result


# def find_test_formation_mentions(text: str) -> list[str]:
#     """Two-step search: first check the text contains a formation, then find
#     any test type within 200 characters of each formation match.

#     Step 1 — scan for formations (Tare, Nise, Kvitnos, Lange, Lysing).
#     Step 2 — for each formation found, extract a 200-char window around it
#               and check whether a test type (DST, mini DST, drill stem test,
#               transient test) appears in that window.

#     Returns a list of highlighted window substrings (rich markup).
#     """
#     # Build windows around each formation match, then merge overlapping ones
#     RADIUS = 500
#     intervals: list[tuple[int, int]] = []
#     for fm in _FORMATION_PATTERN.finditer(text):
#         start = max(0, fm.start() - RADIUS)
#         end = min(len(text), fm.end() + RADIUS)
#         if intervals and start <= intervals[-1][1]:
#             # Merge with previous interval
#             intervals[-1] = (intervals[-1][0], max(intervals[-1][1], end))
#         else:
#             intervals.append((start, end))

#     results = []
#     for start, end in intervals:
#         window = text[start:end]
#         if _TEST_TYPE_PATTERN.search(window):
#             results.append(_highlight(window.strip()))
#     return results

def find_formation_mentions(text: str) -> list[str]:
    """Return distinct formation names found in the text."""
    return list(dict.fromkeys(
        m.group() for m in _FORMATION_PATTERN.finditer(text)
    ))
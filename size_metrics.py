import re

def compute_size_metrics(code):
    """
    Estimates simple size metrics from a source file's text.
    Returns a dict with: LOC, SLOC (source lines), CommentLines, BlankLines, AvgLineLength
    """
    if code is None:
        return {}

    lines = code.splitlines()
    loc = len(lines)
    blank_lines = 0
    comment_lines = 0
    total_len = 0

    # rough block comment handling
    in_block = False
    for line in lines:
        stripped = line.strip()
        total_len += len(line)
        if not stripped:
            blank_lines += 1
            continue

        # check block comment start/end
        if in_block:
            comment_lines += 1
            if '*/' in stripped:
                in_block = False
            continue

        if stripped.startswith('//'):
            comment_lines += 1
            continue

        if stripped.startswith('/*'):
            comment_lines += 1
            if '*/' not in stripped:
                in_block = True
            continue

    sloc = loc - comment_lines - blank_lines
    avg_len = (total_len / loc) if loc > 0 else 0

    return {
        'LOC': loc,
        'SLOC': sloc,
        'CommentLines': comment_lines,
        'BlankLines': blank_lines,
        'AvgLineLength': avg_len,
    }

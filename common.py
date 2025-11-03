import os
import re
import esprima

def get_js_files(root_dir):
    """
    Recursively finds all JS/TS/JSX/TSX files in a directory,
    skipping common build/dependency folders.
    """
    js_files = []
    for root, dirs, files in os.walk(root_dir):
        # Prune search by modifying dirs in-place
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'dist', 'build', '.next', '.git']]
        
        for f in files:
            if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                js_files.append(os.path.join(root, f))
    return js_files


def extract_tokens(file_path):
    """
    Tokenizes a file using esprima, with a regex fallback
    for files that fail parsing (e.g., complex TS syntax).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        # Note: esprima may fail on TypeScript syntax.
        tokens = esprima.tokenize(code)
        return [{"type": t.type, "value": t.value} for t in tokens]
    except Exception:
        # Fallback for non-standard JS or TypeScript
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        pattern = r"[A-Za-z_][A-Za-z0-9_]|==|!=|<=|>=|=>|[+\-/=<>!&|^%]"
        fake_tokens = re.findall(pattern, code)
        return [{"type": "Punctuator" if re.match(r'\W', t) else "Identifier", "value": t} for t in fake_tokens]


def classify_tokens(tokens):
    """Classifies tokens into operators and operands."""
    operators, operands = [], []
    for t in tokens:
        if t["type"] in ["Keyword", "Punctuator"]:
            operators.append(t["value"])
        else:
            # Includes Identifier, Numeric, String, etc.
            operands.append(t["value"])
    return operators, operands
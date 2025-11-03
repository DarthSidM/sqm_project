import re
from collections import defaultdict


def _extract_brace_block(code, start_index):
    """Return (body_string, end_index) of the brace block starting at start_index (position of '{').
    This is a simple scanner that skips over string literals and comments to avoid premature brace matches.
    If matching '}' isn't found, returns the rest of the code as body and len(code) as end_index.
    """
    n = len(code)
    i = start_index
    if i >= n or code[i] != '{':
        return '', i

    depth = 0
    i0 = i
    i += 1
    while i < n:
        c = code[i]
        # strings: single, double, template
        if c == '"' or c == "'" or c == '`':
            quote = c
            i += 1
            while i < n:
                if code[i] == '\\':
                    i += 2
                    continue
                if code[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        # block comment
        if code[i:i+2] == '/*':
            j = code.find('*/', i+2)
            if j == -1:
                return code[i0+1:], n
            i = j + 2
            continue
        # line comment
        if code[i:i+2] == '//':
            j = code.find('\n', i+2)
            if j == -1:
                return code[i0+1:], n
            i = j + 1
            continue

        if code[i] == '{':
            depth += 1
        elif code[i] == '}':
            if depth == 0:
                return code[i0+1:i], i + 1
            depth -= 1
        i += 1

    # no matching closing brace found
    return code[i0+1:], n


def compute_fan_in_out(code):
    """Compute an estimated fan-in and fan-out per function in the given JS/TS code.

    Detection heuristics included:
    - function NAME(...) { ... }
    - exports.NAME = async (...) => { ... } (or without async)
    - module.exports.NAME = async (...) => { ... }
    - const|let|var NAME = async (...) => { ... }

    For each detected function we extract its body and look for function call patterns like:
    - name(...)
    - obj.name(...)

    fan_out for a function = number of distinct callees it invokes (excluding itself)
    fan_in for a function = number of other functions that call it

    Returns a dict mapping function_name -> { 'fan_in': int, 'fan_out': int, 'information_flow': int }
    """
    try:
        patterns = [
            r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{',
            r'exports\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{',
            r'module\.exports\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{',
            r'(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{',
        ]

        # find functions and their bodies
        functions = {}
        occupied_ranges = []
        for pat in patterns:
            for m in re.finditer(pat, code):
                name = m.group(1)
                brace_start = m.end() - 1
                body, endpos = _extract_brace_block(code, brace_start)
                # keep earliest occurrence if duplicate
                if name not in functions or m.start() < functions[name][1]:
                    functions[name] = (body, m.start(), endpos)
        # Build a mapping name -> set(callees)
        name_to_callees = defaultdict(set)

        # call regex: captures both obj.method(...) and plainFunction(...)
        method_call_re = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s*\(')
        func_call_re = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(')

        # keywords and common builtins to ignore as callees
        ignore_names = set(["if", "for", "while", "switch", "catch", "return", "new", "console", "Math", "Object", "Array"])

        for name, (body, startpos, endpos) in functions.items():
            # find method calls like obj.method(...)
            for mm in method_call_re.finditer(body):
                callee = mm.group(2)
                if callee != name and callee not in ignore_names:
                    name_to_callees[name].add(callee)
            # find plain function calls
            for fm in func_call_re.finditer(body):
                callee = fm.group(1)
                # exclude language constructs and the function itself
                if callee != name and callee not in ignore_names:
                    name_to_callees[name].add(callee)

        # compute fan_in by counting callers
        fan_in = defaultdict(int)
        fan_out = {}
        for caller, callees in name_to_callees.items():
            fan_out[caller] = len(callees)
            for callee in callees:
                fan_in[callee] += 1

        # ensure functions with no outgoing calls appear with fan_out 0
        for name in functions.keys():
            fan_out.setdefault(name, 0)
            fan_in.setdefault(name, 0)

        # compute information flow metric
        info_flow = {}
        for name in functions.keys():
            fi = fan_in.get(name, 0)
            fo = fan_out.get(name, 0)
            info_flow[name] = {
                'fan_in': fi,
                'fan_out': fo,
                'information_flow': (fi * fo) ** 2
            }

        return info_flow
    except Exception:
        # On any unexpected parsing error, return empty dict rather than crash
        return {}

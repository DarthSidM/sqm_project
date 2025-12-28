import re
from collections import defaultdict

# Reuse the brace block extractor from information_flow for robust class body extraction
from information_flow import _extract_brace_block


def compute_oo_metrics(code):
    """
    Simple OO metrics for JS/TS code.
    Returns a dict with: TotalClasses, TotalMethods, AvgMethodsPerClass, MaxInheritanceDepth
    """
    if not code:
        return {}

    class_re = re.compile(r'class\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+extends\s+([A-Za-z_][A-Za-z0-9_]*))?\s*\{')

    classes = {}
    parents = {}

    for m in class_re.finditer(code):
        name = m.group(1)
        parent = m.group(2)
        brace_start = m.end() - 1
        body, endpos = _extract_brace_block(code, brace_start)

        # method pattern: name(...) {  (this will also match nested functions; it's an approximation)
        method_re = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{')
        methods = set()
        for mm in method_re.finditer(body):
            method_name = mm.group(1)
            # ignore common keywords
            if method_name in ('if', 'for', 'while', 'switch', 'catch', 'return', 'new'):
                continue
            methods.add(method_name)

        classes[name] = {
            'methods_count': len(methods),
            'methods': list(methods)
        }
        if parent:
            parents[name] = parent

    total_classes = len(classes)
    total_methods = sum(c['methods_count'] for c in classes.values())
    avg_methods = (total_methods / total_classes) if total_classes > 0 else 0

    # compute max inheritance depth by walking parent links
    def depth_of(cls, seen=None):
        if seen is None:
            seen = set()
        if cls in seen:
            return 0
        seen.add(cls)
        parent = parents.get(cls)
        if not parent or parent == cls:
            return 1
        return 1 + depth_of(parent, seen)

    max_depth = 0
    for c in classes.keys():
        try:
            d = depth_of(c)
            if d > max_depth:
                max_depth = d
        except Exception:
            continue

    return {
        'TotalClasses': total_classes,
        'TotalMethods': total_methods,
        'AvgMethodsPerClass': avg_methods,
        'MaxInheritanceDepth': max_depth,
    }

import re

def compute_live_vars(code):
    """
    Estimates live variables using the simple regex method
    from the provided base code.
    """
    try:
        # Find declarations
        vars_declared = re.findall(r'\b(?:let|const|var)\s+([A-Za-z_][A-Za-z0-9_]*)', code)
        
        # Find all usages (this is a very broad regex from the base code)
        vars_used = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', code)
    except Exception:
        return 0, 0 # Handle potential regex errors

    unique_vars = set(vars_declared)
    
    # Total unique variables declared in the file
    live_vars = len(unique_vars) 
    
    # Average "liveness" per the base code's logic
    # (Total usages / total unique declarations)
    avg_live = len(vars_used) / max(1, len(unique_vars))
    
    return live_vars, avg_live
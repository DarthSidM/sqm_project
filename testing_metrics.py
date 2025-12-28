import os
import re


def compute_testing_metrics(file_paths):
    """
    Given a list of source file paths, estimate testing metrics:
    - TestFiles: count of files that look like tests
    - SourceFiles: count of non-test source files
    - TestToSourceRatio: test_files / max(1, source_files)
    """
    if not file_paths:
        return {
            'TestFiles': 0,
            'SourceFiles': 0,
            'TestToSourceRatio': 0,
        }

    test_patterns = [r'\.test\.', r'\.spec\.', r'__tests__']

    test_count = 0
    src_count = 0
    for p in file_paths:
        lower = p.lower()
        if any(re.search(pat, lower) for pat in test_patterns):
            test_count += 1
        else:
            src_count += 1

    ratio = test_count / max(1, src_count)
    return {
        'TestFiles': test_count,
        'SourceFiles': src_count,
        'TestToSourceRatio': ratio,
    }

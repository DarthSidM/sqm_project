import math

def halstead_metrics(operators, operands):
    """
    Calculates Halstead complexity metrics from lists of operators and operands.
    """
    n1 = len(set(operators)) # Unique operators
    n2 = len(set(operands)) # Unique operands
    N1 = len(operators)     # Total operators
    N2 = len(operands)     # Total operands

    n = n1 + n2  # Vocabulary
    N = N1 + N2  # Program Length

    if n == 0 or n2 == 0:
        # Avoid division by zero or log(0) if no tokens or operands
        return dict(
            n1=n1, n2=n2, N1=N1, N2=N2,
            Vocabulary=n, ProgramLength=N,
            Volume=0, Difficulty=0, Effort=0,
            BasicInformation=0
        )

    # Volume: V = N * log2(n)
    volume = N * math.log2(n) if n > 1 else 0

    # Difficulty: D = (n1 / 2) * (N2 / n2)
    difficulty = (n1 / 2) * (N2 / n2)

    # Effort: E = D * V
    effort = difficulty * volume

    return dict(
        n1=n1, n2=n2, N1=N1, N2=N2,
        Vocabulary=n, ProgramLength=N,
        Volume=volume, Difficulty=difficulty, Effort=effort,
        BasicInformation=volume  # Using Halstead Volume as the "basic info" metric
    )
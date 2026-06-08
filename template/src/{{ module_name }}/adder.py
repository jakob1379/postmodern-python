def add_two(num: int | float) -> int | float:
    """
    Adds two to the given `num`

    >>> res = add_two(0.5)
    >>> assert res == 2.5

    >>> res = add_two(2)
    >>> assert res == 4
    """
    return num + 2

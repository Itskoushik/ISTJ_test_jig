class TestAbortRequested(Exception):
    """Raised cooperatively when an operator aborts a running self test.
    Never treated as a test failure — caught separately from Exception."""
    pass
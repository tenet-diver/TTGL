"""Local minimal adapter; deliberately never emits exception content."""
def safe_id(error):
    return type(error).__name__


def describe_exception(error):
    return type(error).__name__

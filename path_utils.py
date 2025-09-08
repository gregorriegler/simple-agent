import os

def get_script_dir():
    """Get the directory where the main script is located."""
    return os.path.dirname(os.path.abspath(__file__))

def get_absolute_path(filename):
    """Get absolute path for a file relative to the script directory."""
    return os.path.join(get_script_dir(), filename)

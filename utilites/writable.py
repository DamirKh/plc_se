import os


def is_directory_writable(directory_path):
    """Checks if a directory exists and is writable.

    Args:
        directory_path (str): The path to the directory.

    Returns:
        bool: True if the directory exists and is writable, False otherwise.
    """

    try:
        # Try creating a temporary file in the directory
        temp_file_path = os.path.join(directory_path, "temp_write_test.txt")
        with open(temp_file_path, 'w'):
            pass  # If successful, the file is created
        os.remove(temp_file_path)  # Clean up the temporary file
        return True
    except OSError:
        return False

import os

def is_directory_empty(directory_path):
    """Checks if a directory is empty.

    Args:
        directory_path (str): The path to the directory.

    Returns:
        bool: True if the directory is empty, False otherwise.
    """

    try:
        return len(os.listdir(directory_path)) == 0
    except FileNotFoundError:
        return False  # Handle the case where the directory doesn't exist

# Example usage:
if __name__ == '__main__':
    directory_to_check = "/home/damir/simul/proj1"

    if is_directory_empty(directory_to_check):
        print(f"The directory '{directory_to_check}' is empty.")
    else:
        print(f"The directory '{directory_to_check}' is not empty.")
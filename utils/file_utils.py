import os
import time
import shutil

def delete_file_by_type(path=None, file_type='pdf'):
    """Deletes files of a given type in the provided path.

    Parameters:
    - path (str): The path to delete files from. Defaults to TEMP_PATH. 
    - file_type (str): The file extension/type to delete. Defaults to 'pdf'.
    """
    files = [f for f in os.listdir(path)]
    files = list(filter(lambda f: f.endswith((f'.{file_type}', f'.{file_type.upper()}')),files))
    for i in files:
        os.remove(os.path.join(path, i))

def reset_folder(path=None):
    """Deletes the contents of the provided folder path and recreates the folder.

    Parameters:
    - path (str): The path of the folder to reset. Defaults to TEMP_PATH.
    """
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def is_file_write_complete(file_path, check_interval=1, retries=5):
    """
    Check if a file's write operation is complete by comparing its size over a short interval.

    Parameters:
    - file_path (str): The path to the file.
    - check_interval (int): How long to wait between checks (in seconds).
    - retries (int): How many times to check the file size for changes.

    Returns:
    - bool: True if the file size is stable (write operation likely complete), False otherwise.
    """
    prev_size = -1
    current_size = os.path.getsize(file_path)
    while retries > 0:
        time.sleep(check_interval)
        prev_size = current_size
        current_size = os.path.getsize(file_path)
        if current_size == prev_size:
            return True
        retries -= 1
    return False
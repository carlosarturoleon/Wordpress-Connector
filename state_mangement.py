import os


def read_checkpoint(checkpoint_file):
    """
    Reads a checkpoint file and returns a set of processed file names.

    This function checks if the specified checkpoint file exists. If it does not exist, it returns an empty set.
    If the file exists, it opens the file, reads the contents, and splits the contents into lines, assuming each
    line represents a processed file name. It then returns these names as a set, which helps in ensuring that 
    each file name is unique and allows for efficient membership testing.

    Parameters:
    checkpoint_file (str): The path to the checkpoint file to read from.

    Returns:
    set: A set containing the names of files that have been processed according to the checkpoint file. Returns
         an empty set if the checkpoint file does not exist.
    """
    if not os.path.exists(checkpoint_file):
        return set()
    with open(checkpoint_file, 'r', encoding='utf-8') as cp_file:
        processed_files = cp_file.read().splitlines()
    return set(processed_files)


def update_checkpoint(checkpoint_file, file_name):
    """
    Updates a checkpoint file by appending a new file name to it.

    This function opens a specified checkpoint file in append mode and adds the name of a file
    (typically indicating processing completion) followed by a newline. This is useful for tracking
    progress in batch processes or logging which files have been processed.

    Parameters:
    checkpoint_file (str): The path to the checkpoint file where the file name will be appended.
    file_name (str): The name of the file to append to the checkpoint file.

    Returns:
    None: This function does not return any value but modifies the checkpoint file on disk.
    """
    with open(checkpoint_file, 'a', encoding='utf-8') as cp_file:
        cp_file.write(file_name + "\n")

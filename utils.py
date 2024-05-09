import os, re, requests, csv, chardet
import pandas as pd
from . import read_checkpoint, update_checkpoint
from urllib.parse import urlparse


def detect_encoding(file_path):
    """
    Detects the encoding of the file located at the given file path.

    This function reads the file in binary mode and uses the chardet library to
    detect the encoding. Chardet works by analyzing a sample of the file content
    and estimating the encoding. The function returns the name of the detected
    encoding.

    Note: The accuracy of chardet increases with the size of the sample it can
    analyze. For very small files, the detection might be less reliable.

    :param file_path: Path to the file whose encoding needs to be detected.
    :return: A string representing the name of the detected encoding.
    """
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']


def is_valid_url(url):
    """
    Validates the given URL to check if it is well-formed by parsing it using urlparse.

    This function attempts to parse the URL and checks if it contains both a scheme
    (e.g., 'http', 'https') and a network location part (netloc). If either is missing,
    or if the URL is malformed and cannot be parsed, the function returns False.

    Parameters:
    url (str): The URL string to validate.

    Returns:
    bool: True if the URL is well-formed, False otherwise.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
    

 # TODO: Update function to take a list of URLs to exclude as an input parameter
def extract_urls_from_text(text):
    """
    Extracts unique URLs from a given text string using a regular expression pattern.

    This function searches for URLs that start with 'http' or 'https' within the provided text.
    It uses a regular expression to identify these URLs, explicitly excluding URLs that belong to
    'example.example2.com' or 'example3.org'. It also ensures that the URLs do not end with commas,
    semicolons, or closing parentheses, which are typical delimiters in text. After extracting all
    URLs, it converts the list of URLs to a set and back to a list to remove any duplicate entries.

    Parameters:
    text (str): The text string from which URLs will be extracted.

    Returns:
    list of str: A list containing the unique URLs found in the text, without duplicates.
    """
    # Regular expression to match plain URLs, excluding a closing parenthesis or other delimiters at the end
    pattern = r'https?://(?!example\.example2\.com|example3\.org)[^\s,;)]+'
    urls = re.findall(pattern, text)
    # Convert the list to a set to remove duplicates, then convert back to a list
    unique_urls = list(set(urls))
    return unique_urls


def check_urls(urls):
    """
    Checks a list of URLs by sending an HTTP HEAD request to each and records the status code.

    The function iterates through each URL in the provided list and attempts to make a HEAD request
    to determine if the URL is accessible. It prints the URL along with its HTTP status code.
    URLs that do not return a 200 OK status code are considered failed and are recorded. If an
    exception occurs during the request (e.g., network issues, invalid URL), it is caught, and
    the error is printed. The function keeps track of URLs that fail due to either non-200 status
    codes or exceptions where no response is available from the server.

    Parameters:
    urls (list of str): A list of URL strings to be checked.

    Returns:
    list of dict: Each dictionary contains the 'url' and its corresponding 'status_code'.
    """ 
    failed_links = []

    for url in urls:
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            status_code = response.status_code
            print(f"URL: {url} - Status Code: {status_code}")
            
            if status_code != 200:
                failed_links.append({'url': url, 'status_code': status_code})

        except requests.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                print(f"URL: {url} - Exception Status Code: {status_code}")
                failed_links.append({'url': url, 'status_code': status_code})
            else:
                print(f"URL: {url} - Exception without response attribute")
                failed_links.append({'url': url, 'status_code': None})

    return failed_links


def remove_failing_links_from_file(file_path, failing_urls, error_log_file="decoding_log_errors.txt"):
    """
    Removes all instances of specified failing URLs from a file and optionally logs errors.

    This function reads the content of a given file and iteratively removes each URL provided in the
    'failing_urls' list. It uses regular expressions to safely escape and remove URLs and their associated
    Markdown link syntax if no text remains in the link. If an error occurs during file processing, the error
    details are logged to a specified error log file. If the error log file does not exist, it will be created.

    Parameters:
    file_path (str): The path to the file from which URLs need to be removed.
    failing_urls (list of dict): A list of dictionaries, each containing the 'url' key with the URL to remove.
    error_log_file (str): The path to the log file where errors should be recorded. Defaults to "decoding_log_errors.txt".

    Returns:
    None: This function does not return any value but modifies the content of the specified file and potentially writes to a log file.

    Exceptions:
    This function logs any exceptions that occur during its execution to the 'error_log_file', noting the file affected and the error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        for url in failing_urls:
            # Regex pattern to match the entire URL
            pattern = re.escape(url['url'])  # Escape to handle special characters in URL
            content = re.sub(pattern, '', content)
            link_pattern = re.compile(r'\[([^\]]+)\]\(\s*\)')
            content = re.sub(link_pattern, r'\1', content)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    except Exception as e:
        # If an exception occurs, check if the error log file exists and create it if not
        if not os.path.exists(error_log_file):
            with open(error_log_file, 'w', encoding='utf-8') as log_file:
                log_file.write("Error Log:\n")

        # Append the error to the log file
        with open(error_log_file, 'a', encoding='utf-8') as log_file:
            log_file.write(f"Error in file {file_path}: {str(e)}\n")


def save_failing_urls_to_csv(File, failing_urls_list, output_csv='failing_urls.csv'):
    """
    Save failing URLs to a CSV file.

    Parameters:
    - failing_urls_list: List of tuples containing file path and failing URLs.
    - output_csv: Name of the CSV file to be created. Default is 'failing_urls.csv'.
    """
    header = ['File', 'URL', 'Status Code']
    mode = 'a' if os.path.exists(output_csv) else 'w'
    with open(output_csv, mode, newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        if mode == 'w':
            csv_writer.writerow(header)
        for entry in failing_urls_list:
            csv_writer.writerow([File, entry['url'], entry['status_code']])


def find_failing_links_and_update_csv(directory, batch_size=100):
    """
    Searches for failing links in Markdown files within a given directory and logs them in a CSV file.

    This function recursively traverses a specified directory, processing each Markdown file it finds.
    It extracts URLs from each Markdown file using the extract_urls_from_text function, checks each URL's
    accessibility using the check_urls function, and collects any failing URLs. Every 'batch_size' number
    of files processed, or at the end of the directory traversal, it writes the failing URLs to a CSV file.
    This batch processing helps in managing memory and ensures data is saved periodically in case of interruptions.

    Parameters:
    directory (str): The path to the directory containing the Markdown files to be processed.
    batch_size (int): The number of files to process before updating the CSV file. Defaults to 100.

    Returns:
    None: This function does not return any value but outputs a CSV file named 'failing_links.csv' containing
          the paths to files and the failing URLs found within those files.

    Outputs:
    A CSV file 'failing_links.csv' in the same directory where the script is run. This file includes columns
    for 'File' and 'Failing URL' detailing where each failing link was found.
    """
    failing_links = []
    file_count = 0
    csv_file = 'failing_links.csv'

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                file_count += 1

                print(f"Processing file {file_count}: {file_path}")

                with open(file_path, 'r', encoding='utf-8') as md_file:
                    urls = extract_urls_from_text(md_file.read())
                    for url in urls:
                        if not check_urls(url):
                            failing_links.append([file_path, url])

                # Write to CSV every batch_size files
                if file_count % batch_size == 0:
                    df = pd.DataFrame(failing_links, columns=['File', 'Failing URL'])
                    write_header = not os.path.exists(csv_file)
                    df.to_csv(csv_file, mode='a', index=False, header=write_header)
                    print(f"Updated CSV after processing {file_count} files")
                    failing_links = []  # Reset the list for the next batch

    # Write any remaining links after the last batch
    if failing_links:
        df = pd.DataFrame(failing_links, columns=['File', 'Failing URL'])
        write_header = not os.path.exists(csv_file)
        df.to_csv(csv_file, mode='a', index=False, header=write_header)
        print(f"Updated CSV with final batch after processing {file_count} files")

    print(f"Total Markdown files processed: {file_count}")


def check_and_remove_links(directory, checkpoint_file='checkpoint.txt'):
    """
    Processes Markdown files in a directory, checks for failing links, removes them, and logs processed files.

    This function walks through a directory, identifies Markdown files not previously processed (as recorded in
    a checkpoint file), and processes each for failing URLs. It checks the accessibility of each URL found in
    the content of the Markdown files, records which files have been processed, removes failing links, and
    optionally logs the failing URLs to a CSV file. This helps in maintaining clean Markdown files in large
    repositories or directories.

    Parameters:
    directory (str): The directory path that contains Markdown files to be processed.
    checkpoint_file (str): The file path used to log the processed Markdown files to avoid reprocessing. 
                           Defaults to 'checkpoint.txt'.

    Returns:
    None: This function does not return any value but prints the number of Markdown files processed and modifies
          the files by removing failing links and updating relevant logs.
    
    Side Effects:
    - Modifies the Markdown files by removing failing links.
    - Updates a checkpoint file that tracks processed files.
    - May create or update a CSV file with details of the failing links.
    """
    processed_files = read_checkpoint(checkpoint_file)
    file_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md') and file not in processed_files:
                file_path = os.path.join(root, file)
                file_count += 1
                print(f"Processing file {file_count}: {file_path}")
                encoding = detect_encoding(file_path)

                with open(file_path, 'r', encoding=encoding, errors='ignore') as md_file:
                    content = md_file.read()
                    urls = extract_urls_from_text(content)
                    failing_urls = check_urls(urls)
                    update_checkpoint(checkpoint_file, file)

                if failing_urls:
                    remove_failing_links_from_file(file_path, failing_urls)
                    save_failing_urls_to_csv(file, failing_urls)
                    
    print(f"Total Markdown files processed: {file_count}")


def update_failing_urls(csv_file, data):
    """
    Appends a new row of data about a failing URL to a CSV file or creates a new file if it does not exist.

    This function checks if a specified CSV file exists. If the file does not exist, it will be created and a
    header row will be added. If it exists, the function simply appends a new row of data. The data is expected
    to be a dictionary matching the CSV's column structure, which includes 'File Name', 'URL', and 'Status Code'.
    This approach ensures that the information about failing URLs can be continuously updated in batch operations
    or repeated checks without losing previous data.

    Parameters:
    csv_file (str): The file path to the CSV where data about failing URLs is stored or will be stored.
    data (dict): A dictionary containing the file name, URL, and status code of a failing URL.

    Returns:
    None: This function does not return any value but writes to a CSV file on disk.
    """
    # Check if the CSV file exists
    file_exists = os.path.isfile(csv_file)

    # Open the CSV file in append mode
    with open(csv_file, 'a', newline='') as csvfile:
        fieldnames = ['File Name', 'URL', 'Status Code']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if the file is newly created
        if not file_exists:
            writer.writeheader()

        # Write or update the data
        writer.writerow(data)


def repairing_empty_links(directory, checkpoint_file='checkpoint.txt', error_log_file='decoding_log_errors.txt'):
    """
    Repairs empty Markdown links in files within a specified directory and logs processing details.

    This function traverses a directory, identifying Markdown files that have not been processed
    (as per a checkpoint file). It searches for Markdown link patterns that lack URLs (e.g., [text]())
    and repairs them by removing the empty link syntax, leaving just the text. It updates a checkpoint
    file with the names of processed files to prevent reprocessing on subsequent runs. Errors encountered
    during processing are logged to a specified error log file.

    Parameters:
    directory (str): The directory containing Markdown files to be processed.
    checkpoint_file (str): Path to a file used to track processed files, preventing reprocessing. Defaults to 'checkpoint.txt'.
    error_log_file (str): Path to a file where errors are logged. Defaults to 'decoding_log_errors.txt'.

    Returns:
    None: This function does not return any value but prints the total number of processed Markdown files and modifies files by repairing links.

    Side Effects:
    - Modifies Markdown files by replacing empty links with just the linked text.
    - Updates a checkpoint file to record processed files.
    - Errors encountered during the processing are logged to an error log file.
    """
    # Regex to find Markdown links like [text]()
    link_pattern = re.compile(r'\[([^\]]+)\]\(\s*\)')
    processed_files = read_checkpoint(checkpoint_file)
    file_count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.md') and file not in processed_files:
                file_path = os.path.join(root, file)
                file_name = os.path.basename(file_path)
                file_count += 1
                print(f"Processing file {file_count}: {file_path}")
                encoding = detect_encoding(file_path)
                try:

                    with open(file_path, 'r', encoding=encoding, errors='ignore') as md_file:
                        content = md_file.read()
                        updated_content = re.sub(link_pattern, r'\1', content)
                    # Write the modified content back to the file
                    with open(file_path, 'w', encoding=encoding, errors='ignore') as file:
                        file.write(updated_content)
                        update_checkpoint(checkpoint_file, file_name)

                except Exception as e:
                    # If an exception occurs, check if the error log file exists and create it if not
                    if not os.path.exists(error_log_file):
                        with open(error_log_file, 'w', encoding='utf-8') as log_file:
                            log_file.write("Error Log:\n")

                    # Append the error to the log file
                    with open(error_log_file, 'a', encoding='utf-8') as log_file:
                        log_file.write(f"Error in file {file_path}: {str(e)}\n")
                           
    print(f"Total Markdown files processed: {file_count}")


def find_nested_links_in_file(file_path):
    """
    Reads a Markdown file and finds all nested Markdown links within it.
    
    A nested Markdown link is defined as a Markdown link present within the text of another Markdown link.

    Args:
    file_path (str): The path to the Markdown file.

    Returns:
    list of tuples: Each tuple contains the text and URL of a nested Markdown link found in the file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    # Regex pattern for a Markdown link
    pattern = r'\[(.*?)\]\((.*?)\)'

    # Find all Markdown links in the text
    links = re.findall(pattern, text)

    # Look for nested links
    nested_links = []
    for link_text, link_url in links:
        nested = re.findall(pattern, link_text)
        if nested:
            nested_links.extend([(link_text, link_url)])
    return nested_links

def find_nested_links_in_folder(folder_path):
    """
    Scans all Markdown files in a specified folder (and its subfolders) for nested Markdown links.

    Args:
    folder_path (str): The path to the folder containing Markdown files.

    Returns:
    list of tuples: Each tuple contains the file path, the text, and the URL of each nested Markdown link found.
    """
    nested_links_in_folder = []
    file_count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                nested_links = find_nested_links_in_file(file_path)
                file_count += 1
                print(str(file_count) + " Processed files, Nested links found: " + str(len(nested_links)))
                if nested_links:
                    for link in nested_links:
                        nested_links_in_folder.append((file_path, link[0], link[1]))
    return nested_links_in_folder


def write_to_csv(data, output_file):
    """
    Writes the data about nested Markdown links to a CSV file.

    The CSV file will have three columns: 'File', 'Nested Link Text', and 'Nested Link URL'.
    It will create the file if it does not exist.

    Args:
    data (list of tuples): The data to be written to the CSV file. Each tuple must contain the file path, nested link text, and nested link URL.
    output_file (str): The path where the CSV file will be created.

    Returns:
    bool: True if the file was successfully written, False otherwise.
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['File', 'Nested Link Text', 'Nested Link URL'])
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"An error occurred while writing to CSV: {e}")
        return False


def find_and_export_nested_links(folder_path, output_csv):
    """
    Finds nested Markdown links in all Markdown files within a specified folder and exports the results to a CSV file.

    A nested Markdown link is defined as a Markdown link present within the text of another Markdown link. The function scans all files with a '.md' extension in the specified folder and its subfolders.

    Args:
    folder_path (str): The path to the folder containing Markdown files.
    output_csv (str): The path where the results CSV file will be created.

    Returns:
    None
    """
    # Find nested links in all Markdown files in the folder
    nested_links = find_nested_links_in_folder(folder_path)

    # Write the results to a CSV file
    if write_to_csv(nested_links, output_csv):
        print(f"CSV file successfully created at {output_csv}")
    else:
        print("Failed to create CSV file.")


# Removing failing links
# directory = 'Blog'
# check_and_remove_links(directory)


#Repairing empty links
# repairing_empty_links("Blog", "checkpoint_empty_links.txt")


#Getting Media Items
# media = get_wordpress_media(SITE_ID, ACCESS_TOKEN)
# print(media)


# Finding Links inside another
# folder_path = "New Blogs"
# output_csv = "wrong_links.csv"
# find_and_export_nested_links(folder_path, output_csv)



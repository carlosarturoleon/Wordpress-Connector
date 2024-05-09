import requests, markdown, os, re, json, string, chardet, csv, random
import pandas as pd
from urllib.parse import urlparse



with open('credentials.json', 'r') as config_file:
    credentials = json.load(config_file)

CLIENT_ID = credentials['CLIENT_ID']
REDIRECT_URI = credentials['REDIRECT_URI']
CLIENT_SECRET = credentials['CLIENT_SECRET']
CODE = credentials['CODE']
ACCESS_TOKEN = credentials['ACCESS_TOKEN']
SITE_ID = credentials['SITE_ID']


def get_access_token(client_id, redirect_uri, client_secret, code):
    """
    Function to get an access token from WordPress.

    Args:
    client_id (str): Your application's client ID.
    redirect_uri (str): The redirect URI for your application.
    client_secret (str): Your application's client secret key.
    code (str): The code received from the authorization request.

    Returns:
    dict: A dictionary containing the access token and related information.
    """
    token_url = "https://public-api.wordpress.com/oauth2/token"
    data = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, data=data)
    return response.json()


def get_wordpress_posts(access_token, site_domain):
    """
    Retrieves the list of posts from a WordPress site.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :return: List of posts with their IDs and titles
    """
    # The API endpoint to list posts
    url = f"https://public-api.wordpress.com/rest/v1.2/sites/{site_domain}/posts/"

    # Set up the headers with your access token
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        # Make the GET request
        response = requests.get(url, headers=headers)
        print(response.text)

        # Check if the request was successful
        if response.status_code == 200:
            posts = response.json().get("posts", [])
            return [(post["ID"], post["title"]) for post in posts]
        else:
            return f"Failed to retrieve posts. Status code: {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


def read_markdown(markdown_file_path):
    """
    Read Markdown content from file.

    :param markdown_file_path: Path to the Markdown file with post content.
    :return: The content of the Markdown file or an error message.
    """
    try:
        encoding = detect_encoding(markdown_file_path)
        try:
            with open(markdown_file_path, "r", encoding=encoding) as file:
                markdown_content = file.read()
                return markdown_content
        except UnicodeDecodeError:
            # Try a different encoding or ignore errors
            with open(markdown_file_path, "r", encoding='utf-8', errors='replace') as file:
                markdown_content = file.read()
                return markdown_content
    except IOError as e:
        return f"Error reading Markdown file: {e}"


def simplify_wordpress_response(response):
    """
    Simplifies the response from the WordPress API to include only essential details.

    :param response: The response object from the WordPress API.
    :return: A simplified dictionary containing only the ID, Title, and URL of the post.
    """
    if response.status_code == 200 or response.status_code == 201:
        response_data = response.json()
        simplified_response = {
            "ID": response_data.get("ID"),
            "Title": response_data.get("title"),
            "URL": response_data.get("URL")
        }
        print(simplified_response)
        return simplified_response
    else:
        print(f"Failed to publish post. Status code: {response.status_code}")
        return f"Failed to publish post. Status code: {response.status_code}"



def publish_wordpress_post_from_markdown_file(
    access_token, site_domain, markdown_file_path, post_status="publish", categories="Blog", parent=11
):
    """
    Publishes a post on a WordPress site from a Markdown file.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param markdown_file_path: Path to the Markdown file with post content
    :param post_status: Status of the post (default is 'publish')
    :param categories: Categorie of the post
    :return: Response from the API or error message
    """
    # Read Markdown content from file
    markdown_content = read_markdown(markdown_file_path)
        
    featured_image = random.randint(19328, 19348)

    try:
        # Get the escerpt of the post
        excerpt = re.search(r'post_excerpt:\s*"([^"]+)"', markdown_content).group(1)

    except AttributeError:

        excerpt = None
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"{markdown_file_path}: excerpt not found\n")

    try:
        # Get the title of the post
        post_title = re.search(r'title:\s*"([^"]+)"', markdown_content).group(1)

    except AttributeError:

        post_title = None
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"{markdown_file_path}: title not found\n")

    # Cut the metadata
    markdown_content = re.sub(r"---([\s\S]*?)---", '', markdown_content, count=1)

    # Convert Markdown to HTML
    post_content = markdown.markdown(markdown_content)

    # The API endpoint to create a post
    url = f"https://public-api.wordpress.com/rest/v1.2/sites/{site_domain}/posts/new"

    # Prepare headers and data payload for the POST request
    headers = {"Authorization": f"Bearer {access_token}"}

    data = {
        'title': post_title,
        'content': post_content,
        'status': post_status,
        'categories': categories,
        'author': '',
        'featured_image': featured_image,
        'excerpt': excerpt,
        "type": "page",
        "parent": parent
    }
    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=data)

        # Use the new function to simplify the response
        return simplify_wordpress_response(response)
    except Exception as e:
        return f"An error occurred: {str(e)}"



def update_wordpress_post(access_token, site_domain, post_id, markdown_file_path, post_status="publish", categories="Blog"):
    """
    Updates a post on a WordPress site using content from a Markdown file.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param post_id: ID of the post to be updated
    :param markdown_file_path: Path to the Markdown file with post content
    :param post_status: Status of the post (default is 'publish')
    :param categories: Categorie of the post
    :return: Response from the API or error message
    """

    # Read Markdown content from file
    markdown_content = read_markdown(markdown_file_path)
    
    featured_image = random.randint(19328, 19348)

    try:
        # Get the escerpt of the post
        excerpt = re.search(r'post_excerpt:\s*"([^"]+)"', markdown_content).group(1)

    except AttributeError:

        excerpt = None
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"{markdown_file_path}: excerpt not found\n")

    try:
        # Get the title of the post
        post_title = re.search(r'title:\s*"([^"]+)"', markdown_content).group(1)

    except AttributeError:

        post_title = None
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"{markdown_file_path}: title not found\n")

    # Cut the metadata
    markdown_content = re.sub(r"---([\s\S]*?)---", '', markdown_content, count=1)

    # Get the tilte of the post
    # post_title = get_title(markdown_content)

    # Convert Markdown to HTML
    post_content = markdown.markdown(markdown_content)

    # The API endpoint to update a post
    url = f'https://public-api.wordpress.com/rest/v1.2/sites/{site_domain}/posts/{post_id}/'

    # Prepare headers and data payload for the POST request
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    data = {
        'title': post_title,
        'content': post_content,
        'status': post_status,
        'categories': categories,
        'author': '',
        'featured_image': featured_image,
        'excerpt': excerpt
    }

    try:
        # Make the POST request
        response = requests.post(url, headers=headers, data=data)

        # Use the new function to simplify the response
        return simplify_wordpress_response(response)
    except Exception as e:
        return f"An error occurred: {str(e)}"


def get_title(markdown_text):
    """
    Extracts and formats the title from a Markdown text.

    :param markdown_text: A string containing the Markdown content.
    :return: A string containing the formatted title extracted from the Markdown text. 
             If no title is found, returns "Untitled".
    """

    # Cut the metadata
    markdown_text = re.sub(r"---([\s\S]*?)---", '', markdown_text, count=1)

    # Extract the title using the regular expression
    title = re.match(r"^\s*#.*", markdown_text, re.MULTILINE)
    if title:
        title = title.group()
        title = clean_title(title)
        return title
    else:
        title  = markdown_text.split("\n")[0]
        if title == "":
            title  = markdown_text.split("\n")[1]
            title = clean_title(title)
            return title
        else:
            title = clean_title(title)
            return title


def clean_title(text):
    """
    Cleans a title string by performing multiple text manipulation operations.

    This function sequentially applies several text cleaning operations on the input string:
    1. Removes hash symbols (#) and strips leading/trailing whitespace.
    2. Replaces double quotes (") with single quotes (').
    3. Removes backslashes (\).
    4. Removes encapsulation through the `remove_encapsulation` function.
    5. Removes the phrase 'Comprehensive ' from the start.
    6. Removes all punctuation except colons using `remove_punctuation_except_colons`.
    7. Removes emojis using `remove_emojis`.

    The purpose of this function is to standardize and clean titles, particularly useful for
    formatting titles in data processing or content management systems.

    :param text: The input title string to be cleaned.
    :return: A cleaned and formatted title string.
    """
    title = text.replace('#', '').strip()
    title = title.replace('"', "'")
    title = title.replace('\\', '')
    title = remove_encapsulation(title)
    title = title.replace('Comprehensive ', '')
    # title = remove_punctuation(title)
    # title = remove_punctuation_except_colons(title)
    title = remove_emojis(title).strip()
    return title


def remove_emojis(text):
    """
    Removes emoji characters from a given text string.

    This function uses a regular expression to identify and remove a wide range
    of emoji characters from the input text. It's useful for text processing tasks
    where emojis need to be excluded, such as data cleaning or text analysis.

    :param text: The input text string from which to remove emojis.
    :return: A new string with all emoji characters removed.
    """
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    
    return emoji_pattern.sub(r'', text)


def remove_punctuation(text):
    """
    Removes punctuation from a given text.

    This function uses a regular expression to match and remove any character that is not
    alphanumeric (a-z, A-Z, 0-9) or whitespace.

    :param text: A string from which punctuation is to be removed.
    :return: A string with all punctuation removed.
    """
    pattern = r'[^a-zA-Z0-9\s]'  # Matches any character that is not alphanumeric or whitespace
    cleaned_string = re.sub(pattern, '', text)
    return cleaned_string
    


def remove_encapsulation(text):
    """
    Removes certain Markdown encapsulation syntax from a given text.

    This function targets words or phrases enclosed within 1 to 3 asterisks, backticks, 
    or angle brackets. It uses a regular expression to find and remove these encapsulating 
    characters, leaving the enclosed content intact.

    :param text: A string containing Markdown syntax to be cleaned.
    :return: A string with Markdown encapsulation removed.
    """
    # Define a regular expression pattern to match words/phrases enclosed within 1, 2, or 3 asterisks, backticks, or angle brackets
    pattern = r'([*`<]){1,3}(.*?)([*`>]){1,3}'
    # Use the re.sub() function with a lambda function to remove the encapsulating characters around the matched words/phrases
    result = re.sub(pattern, r'\2', text)
    
    pattern = r'\*\*(.*?)\*\*'
    result = re.sub(pattern, r'\1', result)

    return result



def remove_punctuation_except_colons(text):
    """
    Removes all punctuation from a given text string except for colons (:).

    This function iterates over each character in the input text and constructs
    a new string that excludes any character considered as punctuation, except
    for colons. This is useful for text processing where specific punctuation
    marks need to be retained for semantic or formatting reasons.

    :param text: The input text string from which to remove punctuation.
    :return: A new string with all punctuation removed except for colons.
    """
    # Create a string of all punctuation marks except for the colon
    punctuation = string.punctuation.replace(':', '')

    # Use a list comprehension to remove all punctuation except colons
    return ''.join(char for char in text if char not in punctuation)


def get_wordpress_post_id(access_token, site_domain, search_title):
    """
    Retrieves the post IDs from a WordPress site. Can search for a specific post by title.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param search_title: Optional title to search for a specific post
    :return: List of posts with their IDs or the ID of the searched post
    """
    # The API endpoint to list posts
    url = f'https://public-api.wordpress.com/rest/v1.2/sites/{site_domain}/posts/'

    # Set up the headers with your access token
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    try:
        # Make the GET request
        response = requests.get(url, headers=headers)
        print(response.text)

        # Check if the request was successful
        if response.status_code == 200:
            posts = response.json().get('posts', [])
            if search_title:
                # Search for a post by title
                for post in posts:
                    if post['title'].lower() == search_title.lower():
                        return post['ID']
                return "Post not found"
            else:
                # Return all posts with their IDs
                return [(post['ID'], post['title']) for post in posts]
        else:
            return f"Failed to retrieve posts. Status code: {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


def upload_blog_posts_from_folder(access_token, site_domain, folder_path, post_status="publish", categories="Blog", parent=11):
    """
    Uploads multiple blog posts to a WordPress site from a specified folder containing Markdown files.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param folder_path: Path to the folder containing Markdown files
    :param post_status: Status of the posts (default is 'publish')
    :param categories: Categories of the posts
    :return: A list of responses from the API for each post upload
    """
    responses = []
    count = 0
    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            markdown_file_path = os.path.join(folder_path, filename)
            # markdown_content = read_markdown(markdown_file_path)
            # Get the title of the post
            # post_title = get_title(markdown_content)
            # print(post_title + "***" +filename)
            # continue
            response = publish_wordpress_post_from_markdown_file(
                access_token, site_domain, markdown_file_path, post_status, categories, parent
            )
            count += 1
            print(str(count) + ' blogs uploaded')
            print(response)
            responses.append((filename, response))
    return responses
    

def get_wordpress_posts_by_category(access_token, site_domain, category_name, per_page=100, post_type="post"):
    """
    Retrieves all posts from a WordPress site filtered by a specific category with pagination.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param category_name: Category name to filter posts
    :param per_page: Number of posts per page (max usually 100)
    :param type: Specify the post type. Defaults to 'post', use 'any' to query for both posts and pages
    :return: List of all posts in the specified category
    """
    all_posts = []
    page = 1
    while True:
        url = f"https://public-api.wordpress.com/rest/v1.2/sites/{site_domain}/posts/?category={category_name}&page={page}&number={per_page}&type={post_type}"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                posts = response.json().get("posts", [])
                if not posts:
                    break  # Exit loop if no more posts
                all_posts.extend(posts)
                page += 1
                break
            else:
                print(f"Failed to retrieve posts on page {page}. Status code: {response.status_code}")
                break
        except Exception as e:
            print(f"An error occurred on page {page}: {str(e)}")
            break

    return all_posts


def remove_author_from_posts(access_token, site_domain, posts):
    """
    Removes the author of posts in a given category.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param posts: List of posts from which to remove the author
    :return: Responses from the API for each post update
    """
    responses = []
    for post in posts:
        post_id = post['ID']
        url = f"https://public-api.wordpress.com/rest/v1.2/sites/{site_domain}/posts/{post_id}/"
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {"author": ""}  # This might not be allowed, depending on your WordPress setup

        try:
            response = requests.post(url, headers=headers, data=data)
            symply_response = simplify_wordpress_response(response)
            responses.append((symply_response))
        except Exception as e:
            responses.append((post_id, f"An error occurred: {str(e)}"))

    return responses


def delete_wordpress_posts_from_file(site_url, json_file_path, access_token):
    """
    Delete a bunch of posts from a WordPress site using the WordPress.com REST API based on a JSON file.

    Args:
    - site_url (str): The URL of the WordPress site.
    - json_file_path (str): The path to the JSON file containing post information.
    - access_token (str): An access token with the necessary permissions.

    Returns:
    - bool: True if the posts were deleted successfully, False otherwise.
    """
    # API endpoint URL
    endpoint_url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site_url}/posts/delete/"

    # Create headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # Read the JSON file
        with open(json_file_path, 'r') as json_file:
            post_data = json.load(json_file)

        # Extract post IDs from the JSON data
        post_ids = [post["ID"] for post in post_data]

        # Create the request payload with post IDs
        data = {
            "post_ids": post_ids
        }

        # Send a DELETE request to delete the posts
        response = requests.post(endpoint_url, headers=headers, json=data)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to delete posts. Status code: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def update_blog_posts_from_folder(access_token, site_domain, folder_path, post_status="publish", categories="Blog"):
    """
    Updates multiple blog posts on a WordPress site from a specified folder containing Markdown files.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param folder_path: Path to the folder containing Markdown files
    :param post_status: Status of the posts (default is 'publish')
    :param categories: Categories of the posts
    :return: A list of responses from the API for each post update
    """
    responses = []
    existing_posts = get_wordpress_posts_by_category(access_token, site_domain, categories, post_type="page", per_page=20)
    print(existing_posts)

    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            markdown_file_path = os.path.join(folder_path, filename)
            markdown_content = read_markdown(markdown_file_path)
            post_title = get_title(markdown_content)

            if post_title in existing_posts:
                post_id = existing_posts[post_title]
                response = update_wordpress_post(access_token, site_domain, post_id, markdown_file_path, post_status, categories)
                responses.append((filename, response))
            else:
                print(f"No matching post found for file {filename}")

    return responses


def get_wordpress_posts_by_category_and_write_to_file(access_token, site_domain, category_name, file_path, per_page=100, post_type="post"):
    """
    Retrieves all posts from a WordPress site filtered by a specific category with pagination and writes them to a file.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param category_name: Category name to filter posts
    :param file_path: Path to the file where data will be written
    :param per_page: Number of posts per page (max usually 100)
    :param post_type: Specify the post type. Defaults to 'post', use 'any' to query for both posts and pages
    :return: None
    """
    page = 1
    all_posts = []

    while True:
        url = f"https://public-api.wordpress.com/rest/v1.2/sites/{site_domain}/posts/?category={category_name}&page={page}&number={per_page}&type={post_type}"
        headers = {
            "Authorization": f"Bearer {access_token}"
            }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            posts = response.json().get("posts", [])
            if not posts:
                break  # Exit loop if no more posts
            for post in posts:
                all_posts.append({
                    'ID': post['ID'],
                    'title': post['title'],
                    'URL': post['URL']
                })
            page += 1
            os.system('clear')
            print("Page " + str(page) + " obtained")
        else:
            print(f"Failed to retrieve posts on page {page}. Status code: {response.status_code}")
            break

    # Write the data to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(all_posts, file, indent=4)


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


def update_blog_posts_from_file(access_token, site_domain, json_file_path, markdown_folder_path, post_status="publish", categories="Blog", checkpoint_file="update_checkpoint.txt"):
    """
    Updates multiple blog posts on a WordPress site using titles from local Markdown files and post IDs from a JSON file.

    :param access_token: OAuth2 access token for WordPress API
    :param site_domain: Domain of the WordPress site
    :param json_file_path: Path to the JSON file containing post data
    :param markdown_folder_path: Path to the folder containing Markdown files
    :param post_status: Status of the posts (default is 'publish')
    :param categories: Categories of the posts
    :return: A list of processed files
    """
    errors = []
    found_count = 0
    not_found_count = 0
    processed_files = read_checkpoint(checkpoint_file)

    # Read post data from the JSON file
    with open(json_file_path, 'r') as file:
        post_data = json.load(file)

    # Create a mapping of titles to post IDs
    title_to_id = {post['title']: post['ID'] for post in post_data}
    # title_to_id = {remove_emojis(post['title']).strip(): post['ID'] for post in post_data}
    url_to_id = {post['URL']: post['ID'] for post in post_data}

    # Iterate through Markdown files and update posts
    for filename in os.listdir(markdown_folder_path):
        if categories=="Glossary":
            url = "https://example.org/glossary/" + filename
        else:
            url = "https://example.org/blog/" + filename
        url = url.replace(".md", "/")
        if filename.endswith('.md') and filename not in processed_files:
            markdown_file_path = os.path.join(markdown_folder_path, filename)
            markdown_content = read_markdown(markdown_file_path)
            file_title = re.search(r'title:\s*"([^"]+)"', markdown_content)
            if file_title is None:
                file_title = get_title(markdown_content)
            else:
                file_title = file_title.group(1).strip()
            if file_title in title_to_id:
                post_id = title_to_id[file_title]
                found_count += 1
                # print(file_title, post_id)
                # continue
                response = update_wordpress_post(access_token, site_domain, post_id, markdown_file_path, post_status, categories)
                os.system('clear')
                print(response)
                update_checkpoint(checkpoint_file, filename)
            elif url in url_to_id:
                post_id = url_to_id[url]
                found_count += 1
                # print(file_title, post_id)
                # continue
                response = update_wordpress_post(access_token, site_domain, post_id, markdown_file_path, post_status, categories)
                os.system('clear')
                print(response)
                update_checkpoint(checkpoint_file, filename)
            else:
                not_found_count += 1
                errors.append(f"No matching post found for '{url}' in '{filename}'")
                print(f"No matching post found for '{url}' in '{filename}'")
        print(f'Found: {found_count} Not found: {not_found_count}')
        if errors:
            with open("error_log.txt", "w") as error_file:
                for error in errors:
                    error_file.write(f"{error}\n")

    return processed_files



def extract_post_details(json_data):
    """
    Extracts ID, title, and URL from a JSON response containing WordPress post data.

    :param json_data: JSON data containing post information
    :return: A list of tuples, each containing the ID, title, and URL of a post
    """
    extracted_data = []

    try:
        posts = json.loads(json_data)
        for post in posts:
            post_id = post.get('ID', 'N/A')
            title = post.get('title', 'No Title')
            url = post.get('URL', 'No URL')
            extracted_data.append((post_id, title, url))
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")

    return extracted_data


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
    

def detect_encoding(file_path):
    """
    Detects the encoding of a file based on its content.

    This function opens a file in binary mode, reads its content, and uses the chardet library to
    analyze the bytes to determine the most likely character encoding. It is useful for preparing to
    process files with unknown or varied encodings, especially when dealing with text files that may
    contain non-standard or mixed encodings.

    Parameters:
    file_path (str): The path to the file whose encoding needs to be detected.

    Returns:
    str: The name of the encoding detected (e.g., 'utf-8', 'ascii', 'iso-8859-1'). If no specific encoding
         is confidently detected, the function may return a generic answer like 'Windows-1252' or None.
    """
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']


def get_wordpress_media(site_id, access_token):
    """
    Fetches media items from a WordPress site.

    Args:
    site_id (str): The ID or domain of the WordPress site.
    access_token (str): Access token for authentication.

    Returns:
    dict: Response from the WordPress API.
    """
    url = f"https://public-api.wordpress.com/rest/v1.1/sites/{site_id}/media"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    response = response.json()
    response = json.dumps(response, indent=4)

    with open("media.json", 'w') as file:
        file.write(response)

    return response


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



# Get Access Token
# token = get_access_token(CLIENT_ID, REDIRECT_URI, CLIENT_SECRET, CODE)
# print(token)

# Publish a Post
# response = publish_wordpress_post_from_markdown_file(
#     ACCESS_TOKEN,
#     SITE_ID,
#     "how-long-does-a-discord-account-take-to-delete.md",
# )
# print(response)

# Get Post ID
# posts = get_wordpress_post_id(ACCESS_TOKEN, SITE_ID, "Home")
# print(posts)


# Update a Post
# response = update_wordpress_post(ACCESS_TOKEN, SITE_ID, '53209', "the-ultimate-investors-guide-to-crypto-a-overview.md")
# print(response)


# Posting Folder
# folder_path = 'New Blogs'
# blog_parent = 11 
# glossary_parent = 6430
# responses = upload_blog_posts_from_folder(ACCESS_TOKEN, SITE_ID, folder_path, categories="Glossary", parent=11)
# for filename, response in responses:
#     print(f"{filename}: {response}")


# Remove the author form all Glossary Posts
# posts = get_wordpress_posts_by_category(ACCESS_TOKEN, SITE_ID, "Glossary", per_page=100)
# print(posts)
# remove_author_from_posts(ACCESS_TOKEN, SITE_ID, posts)

# Getting all blogs
file_path = 'all_blogs.json'
get_wordpress_posts_by_category_and_write_to_file(ACCESS_TOKEN, SITE_ID, "", file_path, post_type="page")


# Updating from folder
# file_path = 'all_blogs.json'
# folder_path = 'New Glossary'
# update_blog_posts_from_file(ACCESS_TOKEN, SITE_ID, file_path, folder_path)



# Delete Blogs
# json_file_path = "no_parent.json"  # Replace with the path to your JSON file

# if delete_wordpress_posts_from_file(SITE_ID, json_file_path, ACCESS_TOKEN):
#     print("Posts deleted successfully.")
# else:
#     print("Failed to delete posts.")


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


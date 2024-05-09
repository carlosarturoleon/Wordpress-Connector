import requests, markdown, os, re, json, string, random
from . import read_checkpoint, update_checkpoint, detect_encoding


with open('credentials.json', 'r') as config_file:
    credentials = json.load(config_file)

CLIENT_ID = credentials['CLIENT_ID']
REDIRECT_URI = credentials['REDIRECT_URI']
CLIENT_SECRET = credentials['CLIENT_SECRET']
CODE = credentials['CODE']
ACCESS_TOKEN = credentials['ACCESS_TOKEN']
SITE_ID = credentials['SITE_ID']


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
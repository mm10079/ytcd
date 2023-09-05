#!/usr/bin/env python3
# reference: https://github.com/NicKoehler/mediafire_bulk_downloader
import hashlib
import imghdr
from re import findall
from time import sleep
from requests import get as gt
from gazpacho import get, Soup
from argparse import ArgumentParser
from gazpacho.utils import HTTPError, sanitize
from os import path, makedirs, remove, chdir
from threading import BoundedSemaphore, Thread, Event

import json, urllib.parse, os, subprocess
from typing import Any, Dict, Optional, Union
from urllib.error import HTTPError as UrllibHTTPError
from urllib.parse import urlencode
from urllib.request import build_opener

#from .utils import HTTPError, sanitize

if os.name == 'nt':
    dl_module = f"\"{os.path.join(os.path.join(os.getcwd(), 'plugin'), 'wget.exe')}\""
else:
    dl_module = "wget"
class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

# Clone from gazpacho/get.py
def get_decode(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, Any]] = None,
) -> Union[str, Dict[str, Any]]:
    """Retrive url contents

    Params:

    - url: target page
    - params: GET request payload
    - headers: GET request headers

    Example:

    ```
    get('https://httpbin.org/anything', {'soup': 'gazpacho'})
    ```
    """
    url = sanitize(url)
    opener = build_opener()
    if params:
        url += "?" + urlencode(params)
    if headers:
        for h in headers.items():
            opener.addheaders = [h]
    if (headers and not headers.get("User-Agent")) or not headers:
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:80.0) Gecko/20100101 Firefox/80.0"
        opener.addheaders = [("User-Agent", ua)]
    try:
        with opener.open(url) as response:
            content = response.read().decode("ISO-8859-1") #"ISO-8859-1" / "utf-8"
            if response.headers.get_content_type() == "application/json":
                content = json.loads(content)
    except UrllibHTTPError as e:
        raise HTTPError(e.code, e.msg) from None  # type: ignore
    return content

# Non-alphanumeric (str.isalphanum()) characters allowed in a file or folder name
NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTERS = "-_. "
# What to replace bad characters with.
NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTER_REPLACEMENT = "-"


def hash_file(filename: str):
    # make a hash object
    h = hashlib.sha256()

    # open file for reading in binary mode
    with open(filename, "rb") as file:

        # loop till the end of the file
        chunk = 0
        while chunk != b"":
            # read only 1024 bytes at a time
            chunk = file.read(1024)
            h.update(chunk)

    # return the hex representation of digest
    return h.hexdigest()

def normalize_file_or_folder_name(filename: str):
    # return filename    # uncomment this line to disable file or folder normalizing. 
    return "".join([
        char 
            if (char.isalnum() or char in NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTERS) else
        NON_ALPHANUM_FILE_OR_FOLDER_NAME_CHARACTER_REPLACEMENT
            for char in filename])

def print_error(link: str):
    print(
        f"{bcolors.FAIL}Deleted file or Dangerous File Blocked\n"
        f"{bcolors.WARNING}Take a look if you want to be sure: {link}{bcolors.ENDC}"
    )


def main():

    parser = ArgumentParser(
        "mediafire_bulk_downloader", usage="python mediafire.py <mediafire_url>"
    )
    parser.add_argument(
        "mediafire_url", help="The url of the file or folder to be downloaded"
    )
    parser.add_argument(
        "-o",
        "--output",
        help="The path of the desired output folder",
        required=False,
        default=".",
    )
    parser.add_argument(
        "-t",
        "--threads",
        help="Number of threads to use",
        type=int,
        default=10,
        required=False,
    )

    args = parser.parse_args()

    folder_or_file = findall(
        r"mediafire\.com/(folder|file|view|file_premium)\/([a-zA-Z0-9]+)", args.mediafire_url
    )

    SkipNewFolder = 0
    if not folder_or_file:
        folder_or_file = findall(
            r"app\.mediafire\.com/([a-zA-Z0-9]+)", args.mediafire_url
        )
        if folder_or_file:
            t = "folder"
            key = folder_or_file[0]
            SkipNewFolder = 1

        else:
            print(f"{bcolors.FAIL}Invalid link{bcolors.ENDC}")
            exit(1)
    else:
        t, key = folder_or_file[0]

    #print("output:"+ args.output)
    if t == "file" or  t == "view" or  t == "file_premium":
        print("get_file")
        get_file(key, args.output)
    elif t == "folder":
        print("get_folders")
        if not SkipNewFolder:
            get_folders(key, args.output, args.threads, first=True)
        else:
            get_folders(key, args.output, args.threads, first=False)
    else:
        print(f"{bcolors.FAIL}Invalid link{bcolors.ENDC}")
        exit(1)

    print(f"{bcolors.OKGREEN}{bcolors.BOLD}All downloads completed{bcolors.ENDC}")
    exit(0)


def get_files_or_folders_api_endpoint(filefolder, folder_key, chunk=1, info=False):
    return (
        f"https://www.mediafire.com/api/1.4/folder"
        f"/{'get_info' if info else 'get_content'}.php?r=utga&content_type={filefolder}"
        f"&filter=all&order_by=name&order_direction=asc&chunk={chunk}"
        f"&version=1.5&folder_key={folder_key}&response_format=json"
    )


def get_info_endpoint(file_key: str):
    return f"https://www.mediafire.com/api/file/get_info.php?quick_key={file_key}&response_format=json"


def get_folders(folder_key, folder_name, threads_num, first=False):

    if first:
        folder_name = path.join(
            folder_name,
            normalize_file_or_folder_name(gt(
                get_files_or_folders_api_endpoint("folder", folder_key, info=True)
            ).json()["response"]["folder_info"]["name"]),
        )
    print("folder_name:"+ folder_name)

    # if the folder not exist, create and enter it
    if not path.exists(folder_name):
        makedirs(folder_name)
    chdir(folder_name)

    # downloading all the files in the main folder
    download_folder(folder_key, threads_num)

    # searching for other folders
    folder_content = gt(
        get_files_or_folders_api_endpoint("folders", folder_key)
    ).json()["response"]["folder_content"]

    # downloading other folders
    if "folders" in folder_content:
        for folder in folder_content["folders"]:
            get_folders(folder["folderkey"], folder["name"], threads_num)
            chdir("..")


def download_folder(folder_key, threads_num):

    # getting all the files
    data = []
    chunk = 1
    more_chunks = True

    try:
        # if there are more than 100 files makes another request
        # and append the result to data
        while more_chunks:
            r_json = gt(
                get_files_or_folders_api_endpoint("files", folder_key, chunk=chunk)
            ).json()
            more_chunks = r_json["response"]["folder_content"]["more_chunks"] == "yes"
            data += r_json["response"]["folder_content"]["files"]
            chunk += 1

    except KeyError:
        print("Invalid link")
        return

    event = Event()

    threadLimiter = BoundedSemaphore(threads_num)

    total_threads: list[Thread] = []

    # appending a new thread for downloading every link
    for file in data:
        total_threads.append(
            Thread(
                target=download_file,
                args=(
                    file,
                    event,
                    threadLimiter,
                ),
            )
        )

    # starting all threads
    for thread in total_threads:
        thread.start()

    # handle being interrupted
    try:
        while True:
            if all(not t.is_alive() for t in total_threads):
                break
            sleep(0.01)
    except KeyboardInterrupt:
        print(f"{bcolors.WARNING}Closing all threads{bcolors.ENDC}")
        event.set()
        for thread in total_threads:
            thread.join()
        print(f"{bcolors.WARNING}{bcolors.BOLD}Download interrupted{bcolors.ENDC}")
        exit(0)


def get_file(key: str, output_path: str = None):
    """
    downloads a single file in the main thread
    """

    file_data = gt(get_info_endpoint(key)).json()["response"]["file_info"]
    if output_path:
        chdir(output_path)
    download_file(file_data)


def has_extension(file_path):
    filename = os.path.basename(file_path)
    _, file_extension = os.path.splitext(filename)
    return bool(file_extension)


def add_extension(filename, extension):
    base, _ = os.path.splitext(filename)
    return f"{base}.{extension}"


def is_image(filename):
    image_formats = ['jpeg', 'png']
    file_format = imghdr.what(filename)
    return file_format in image_formats


def wget_mediafire(file, file_link):
    file_name = urllib.parse.unquote(urllib.parse.unquote(urllib.parse.urlparse(file_link).path.split('/')[-2]))
    print(file_name)

    chk_is_img = 0
    if not has_extension(file_name):
        print(f"{bcolors.WARNING}The file path does not have an extension. {bcolors.ENDC}")
        chk_is_img = 1

    if path.exists(file_name):
        if hash_file(file_name) == file["hash"]:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}{file_name}{bcolors.ENDC}{bcolors.WARNING} already exists, skipping{bcolors.ENDC}"
            )
            return
        else:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}{file_name}{bcolors.ENDC}{bcolors.WARNING} already exists but corrupted, downloading again{bcolors.ENDC}"
            )

    global dl_module
    #dlCmd = f"{dl_module} -O \"{file_name}\" \"{file_link}\""
    dlCmd = [dl_module, "-O", file_name, file_link]
    print("dlCmd: ", dlCmd)
    subprocess.run(dlCmd)

    if (chk_is_img):
        if is_image(file_name):
            image_extension = imghdr.what(file_name)
            new_filename = add_extension(file_name, image_extension)
            os.rename(file_name, new_filename)
            print(f"The file is an image. Renamed to {new_filename}")
        else:
            print("The file is not an image.")


def download_file(file: dict, event: Event = None, limiter: BoundedSemaphore = None):
    """
    used to download direct file links
    """
    if limiter:
        limiter.acquire()
    if event:
        if event.is_set():
            limiter.release()
            return

    file_link = file["links"]["normal_download"]

    try:
        html = get_decode(file_link)
    except HTTPError:
        print("HTTPError")
        print_error(file_link)
        limiter.release()
        return

    soup = Soup(html)
    try:
        link = (
            soup.find("div", {"class": "download_link"})
            .find("a", {"class": "input popsok"})
            .attrs["href"]
        )
    except Exception:
        print("Exception")
        print_error(file_link)
        if limiter:
            limiter.release()

        print("Retry and use wget")
        wget_mediafire(file, file_link)
        return

    filename = normalize_file_or_folder_name(file["filename"])

    if path.exists(filename):
        if hash_file(filename) == file["hash"]:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}{filename}{bcolors.ENDC}{bcolors.WARNING} already exists, skipping{bcolors.ENDC}"
            )
            if limiter:
                limiter.release()
            return
        else:
            print(
                f"{bcolors.WARNING}{bcolors.BOLD}{filename}{bcolors.ENDC}{bcolors.WARNING} already exists but corrupted, downloading again{bcolors.ENDC}"
            )

    print(f"{bcolors.OKBLUE}Downloading {bcolors.BOLD}{filename}{bcolors.ENDC}")

    if event:
        if event.is_set():
            limiter.release()
            return

    with gt(link, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=4096):
                if event:
                    if event.is_set():
                        break
                if chunk:
                    f.write(chunk)
    if event:
        if event.is_set():
            remove(filename)
            print(
                f"{bcolors.WARNING}Deteleted partially downloaded {bcolors.BOLD}{filename}{bcolors.ENDC}"
            )
            limiter.release()
            return

    print(
        f"{bcolors.OKGREEN}{bcolors.BOLD}{filename}{bcolors.ENDC}{bcolors.OKGREEN} downloaded{bcolors.ENDC}"
    )
    if limiter:
        limiter.release()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)

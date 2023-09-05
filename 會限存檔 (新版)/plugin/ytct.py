#!/usr/bin/env python3
import argparse
from datetime import datetime
from http import cookiejar
import json
import os
import re
import requests
import sys
import urllib.parse as urlparse
from youtube_community_tab.requests_handler import requests_cache
from youtube_community_tab.post import Post
from youtube_community_tab.community_tab import CommunityTab
from lite import database

POST_REGEX=r"^(?:(?:https?:\/\/)?(?:.*?\.)?(?:youtube\.com\/)((?:channel\/UC[a-zA-Z0-9_-]+\/community\?lb=)|post\/))?(?P<post_id>Ug[a-zA-Z0-9_-]+)(.*)?$"
CHANNEL_REGEX=r"^(?:(?:https?:\/\/)?(?:.*?\.)?(?:youtube\.com\/))((?P<channel_handle>@[a-zA-Z0-9_-]+)|((channel\/)?(?P<channel_id>UC[a-zA-Z0-9_-]+)))(?:\/.*)?$"
HANDLE_TO_ID_REGEX=r"\"header\":\{\"c4TabbedHeaderRenderer\":\{\"channelId\":\"(?P<channel_id>UC[a-zA-Z0-9_-]+)\""
POST_DATE_REGEX=r"^(?P<magnitude>[0-9]{1,2}) (?P<unit>(second|minute|hour|day|week|month|year))s? ago(?P<edited> \(edited\))?$"
CLEAN_FILENAME_KINDA=r"[^\w\-_\. \[\]\(\)]"
BLOCK_SIZE = 1024
TIME_FACTORS={
    "second": 1,
    "minute": 60,
    "hour": 60 * 60,
    "day": 60 * 60 * 24,
    "week": 60 * 60 * 24 * 7, # beyond 28 days it becomes 1 month ago
    "year": 60 * 60 * 24 * 365
}

args = None

def get_arguments():
    parser.add_argument("--cookies", metavar="COOKIES FILE", type=str, help="path to a Netscape format cookies file where cookies will be read from/written to")
    parser.add_argument("-d", "--directory", type=str, help="save directory (defaults to current)", default=os.getcwd())
    parser.add_argument("--write-viewer", action="store_true", help="copy the viewer file and create an index of downloaded posts to be viewed")
    parser.add_argument("--post-archive", metavar="FOLDER", type=str, help="download only posts not listed in the archive file and record the IDs of newly downloaded posts")
    parser.add_argument("--archive-name", metavar="ARCHIVE FILE", type=str, help="use custom name to create archive file")
    parser.add_argument("--author-name", metavar="SQLITE TABLE NAME", type=str, help="create a sqlite new table with custom name")
    parser.add_argument("--dates", action="store_true", help="write as much information about the publishing date as possible, as well as attempting to update dates for prior posts based on new information")
    parser.add_argument("--check-membership", action="store_true", help="get database membership list to check cookies not expired")
    parser.add_argument("links", metavar="CHANNEL", nargs="*", help="youtube channel or community post link/id")
    return parser.parse_args()

def use_cookies(cookie_jar_path):
    cookie_jar = cookiejar.MozillaCookieJar(cookie_jar_path)
    try:
        cookie_jar.load()
        print_log("ytct", f"loaded cookies from {cookie_jar_path}")
    except:
        print_log("ytct", f"failed to load cookies from {cookie_jar_path}, continuing without cookies")
        return
    requests_cache.cookies = cookie_jar

def get_channel_id_from_handle(channel_handle):
    handle_url = f"https://youtube.com/{channel_handle}"
    channel_home_r = requests.get(handle_url)
    if not channel_home_r.ok:
        print_log("ytct", f"failed to convert channel handle to channel id, no response from {handle_url}")
        sys.exit(1)
    channel_home = channel_home_r.text
    channel_id_m = re.search(HANDLE_TO_ID_REGEX, channel_home)
    channel_id = channel_id_m.group("channel_id")
    if not channel_id:
        print_log("ytct", f"failed to convert channel handle to channel id, data format may have changed")
        sys.exit(1)
    return channel_id

def get_post(post_id, post_archive):
    if post_archive:
        with open(post_archive, "r") as archive_file:
            skip_ids = archive_file.read().splitlines()
        if post_id in skip_ids:
            print_log(f"post:{post_id}", f"already recorded in archive")
            return
    post = Post.from_post_id(post_id)
    handle_post(post)
    if post_archive:
        with open(post_archive, "a") as archive_file:
            archive_file.write(f"{post_id}\n")

def get_channel_posts(channel_id, post_archive):
    ct = CommunityTab(channel_id)
    page_count = 1
    print_log("community tab", f"getting posts from community tab (page {page_count})", "\r")
    ct.load_posts(0)
    while(ct.posts_continuation_token):
        page_count += 1
        print_log("community tab", f"getting posts from community tab (page {page_count})", "\r")
        ct.load_posts(0)
    print_log("community tab", f"getting posts from community tab (page {page_count})")
    print_log("community tab", f"found {len(ct.posts)} posts")
    # only read the archive once
    skip_ids = []
    if post_archive:
        with open(post_archive, "r") as archive_file:
            skip_ids = archive_file.read().splitlines()
    for post in ct.posts:
        if len(skip_ids) > 0 and post.post_id in skip_ids:
            print_log(f"post:{post.post_id}", f"already recorded in archive")
            continue
        handle_post(post)
        if post_archive:
            with open(post_archive, "a") as archive_file:
                archive_file.write(f"{post.post_id}\n")

#sqlite版本 post下載
def get_post_lite(post_id, db):
    skip_ids = db.load_all_value()
    if post_id in skip_ids:
        print_log(f"post:{post_id}", f"already recorded in archive")
        return
    post = Post.from_post_id(post_id)
    handle_post(post, db)

#sqlite版本 channel下載
def get_channel_posts_lite(channel_id, db):
    ct = CommunityTab(channel_id)
    page_count = 1
    print_log("community tab", f"getting posts from community tab (page {page_count})", "\r")
    ct.load_posts(0)
    while(ct.posts_continuation_token):
        page_count += 1
        print_log("community tab", f"getting posts from community tab (page {page_count})", "\r")
        ct.load_posts(0)
    print_log("community tab", f"getting posts from community tab (page {page_count})")
    print_log("community tab", f"found {len(ct.posts)} posts")
    # only read the archive once
    if args.check_membership and args.cookies:
        check = False
        memberships = 0
        memberships = len(db.get_specific_list('membership', 1))
    skip_ids = db.load_all_value()
    for post in ct.posts[::-1]:
        if len(skip_ids) > 0 :
            if memberships > 0 and not check:
                if post.as_json()["sponsor_only_badge"]:
                    check = True
            if post.post_id in skip_ids:
                print_log(f"post:{post.post_id}", f"already recorded in archive")
                continue
        handle_post(post, db)
    if args.check_membership and args.cookies and not check:
        print_log("community tab", "posts is fewer than archive maybe cookie has been expired")
    else:
        print_log("community tab", "the cookies have not expired yet and there are search results for membership posts")

def handle_post(post, db=None):
    filters = [
    r'https://www\.dropbox\.com[^,\"\']*(?=[,\"\'])',
    r'https://www\.mediafire\.com[^,\"\']*(?=[,\"\'])',
    r'https://app\.mediafire\.com[^,\"\']*(?=[,\"\'])',
    r'https://yt3\.ggpht\.com[/A-z0-9 _%.?\-,]*' #yt3確保在最後一個，用於辨別桌布貼文是否有附上其他鏈結
    ]
    post_j = post.as_json()
    component = f"post:{post.post_id}"
    post_file_name = f"{post.post_id}"
    post_file_dir = os.path.join(args.directory)
    post_file_path = os.path.join(post_file_dir, post_file_name)
    if db:
        try:
            post_key = db.get_id(f"{post_file_name}.tmp")
        except:
            db.save_new_post(f"{post_file_name}.tmp")
            post_key = db.get_id(f"{post_file_name}.tmp")
    if args.dates:
        timestamp_info = handle_post_timestamp(post, post_file_path)
        post_j["_published"] = timestamp_info
    try:
        if not os.path.isdir(post_file_dir):
            os.makedirs(post_file_dir)
        if os.path.isfile(f"{post_file_path}.json.tmp"):
            os.remove(f"{post_file_path}.json.tmp")
        print_log(component, f"writing {post_file_name}.json")
        with open(f"{post_file_path}.json.tmp", "w", encoding='utf8') as post_file:
            post_data = json.dumps(post_j, ensure_ascii=False)
            if db:
                db.insert_post_data(post_key, 'post_json', post_data)
                db.insert_post_data(post_key, 'post_path', post_file_path)
                if post.as_json()["sponsor_only_badge"]:
                    db.insert_post_data(post_key, 'membership', 1)
                else:
                    db.insert_post_data(post_key, 'membership', 0)
                urls = []
                for filter in filters:
                    if r'yt3\.ggpht\.com' in filter:
                        if urls == []:
                            #緊抓取壁紙的圖片，若需要下載所有圖片可以刪除這段判別式
                            if '壁紙' in post_data or 'llustrat' in post_data:
                                for link in re.findall(filter, str(post_data)):
                                    link = link.split('=')[0] + '=s0-c-fcrop64=1,00000000ffffffff-nd-v1'
                                    if link not in urls:
                                        print(link)
                                        urls.append(link)
                    else:
                        for link in re.findall(filter, str(post_data)):
                            if '...' not in link and link not in urls:
                                print(link)
                                urls.append(link)
                db.insert_post_data(post_key, 'post_links', json.dumps(urls))
            post_file.write(post_data)
        if os.path.isfile(f"{post_file_path}.json"):
            os.remove(f"{post_file_path}.json")
        os.rename(f"{post_file_path}.json.tmp", f"{post_file_path}.json")
        db.insert_post_data(post_key, 'post_id', post_file_name)
    except Exception as e:
        print_log(component, f"failed to write file {post_file_path}")
        print_log(component, str(e))
    if post.backstage_attachment:
        handle_post_attachments(component, post.backstage_attachment, post_file_path)

def handle_post_timestamp(post, path):
    timestamp_obj = {}
    # last updated time
    timestamp_obj["lastUpdatedTimestamp"] = int(datetime.utcnow().timestamp())
    # string as it appears on YouTube
    timestamp_obj["lastPublishedString"] = post.get_published_string()
    # the closest UTC timestamp, and the seconds difference from the furthest UTC timestamp
    diff_to_nearest_possible_date, timestamp_obj["timestampAccuracy"], timestamp_obj["is_edited"] = get_time_diff_from_text(timestamp_obj["lastPublishedString"])
    if diff_to_nearest_possible_date and timestamp_obj["timestampAccuracy"]:
        timestamp_obj["closestTimestamp"] = timestamp_obj["lastUpdatedTimestamp"] - diff_to_nearest_possible_date
        if os.path.isfile(f"{path}.json"):
            try:
                with open(f"{path}.json", "r") as previous_post_file:
                    previous_post_j = json.load(previous_post_file)
                if "_published" in previous_post_j:
                    previous_timestamp_obj = previous_post_j["_published"]
                    diff_since_last_update = timestamp_obj["lastUpdatedTimestamp"] - previous_timestamp_obj["lastUpdatedTimestamp"]
                    if previous_timestamp_obj["lastPublishedString"] == timestamp_obj["lastPublishedString"]:
                        # update accuracy based on time between current and last update
                        timestamp_obj["timestampAccuracy"] = previous_timestamp_obj["timestampAccuracy"] - diff_since_last_update
                    elif diff_since_last_update < previous_timestamp_obj["timestampAccuracy"]:
                        # time between change in update is less than previous accuracy, should be safe to change
                        # i.e. if you save a post 3 days after publish, accuracy is 72-96 hours
                        # if you then update 364 days after publish, and update again 1 year after publish
                        # the diff since last update is 24 hours, which is better than before
                        timestamp_obj["timestampAccuracy"] = diff_since_last_update
                    else:
                        # keep previous accuracy
                        timestamp_obj["timestampAccuracy"] = previous_timestamp_obj["timestampAccuracy"]
                    if previous_timestamp_obj["closestTimestamp"] < timestamp_obj["closestTimestamp"]:
                        # if closest timestamp is not better than previous, keep previous
                        timestamp_obj["closestTimestamp"] = previous_timestamp_obj["closestTimestamp"]
            except Exception as e:
                print_log("community post", f"failed to open previously downloaded post {post.post_id}")
                print_log("community post", str(e))
    return timestamp_obj

def get_time_diff_from_text(published_text):
    post_date_m = re.search(POST_DATE_REGEX, published_text)
    if post_date_m:
        mag = int(post_date_m.group("magnitude"))
        unit = post_date_m.group("unit")
        delta_secs = 0
        accuracy = 0
        if unit == "month":
            # absolute madness beyond this point
            delta_secs += TIME_FACTORS["day"] * 28
            if mag != 1:
                delta_secs += (mag - 1) * TIME_FACTORS["day"] * 30.4
            accuracy = TIME_FACTORS["day"] * 31 - 1
        else:
            delta_secs = mag * TIME_FACTORS[unit]
            accuracy = TIME_FACTORS[unit] - 1
        edited = False
        if post_date_m.group("edited"):
            edited = True
        return (delta_secs, accuracy, edited)
    else:
        print_log("community post:date", f"could not parse '{published_text}', open an issue?")
        return (None, None, None)

def handle_post_attachments(component, attachment, path):
    if "postMultiImageRenderer" in attachment:
        num_images = len(attachment["postMultiImageRenderer"]["images"])
        print_log(component, f"downloading {num_images} attached images")
        for image_i in range(0, num_images):
            handle_post_attachments(component, attachment["postMultiImageRenderer"]["images"][image_i], f"{path}_{image_i}")
    elif "backstageImageRenderer" in attachment:
        print_log(component, f"downloading image")
        image_url = attachment["backstageImageRenderer"]["image"]["thumbnails"][-1]["url"].split("=", 1)[0] + "=s0?imgmax=0"
        image_r = requests.get(image_url, stream=True, allow_redirects=True)
        image_ext = image_r.headers["Content-Type"].split("/", 1)[1].replace("jpeg", "jpg")
        image_path = f"{path}.{image_ext}"
        if not os.path.isfile(image_path):
            if os.path.isfile(f"{image_path}.tmp"):
                os.remove(f"{image_path}.tmp")
            with open(f"{image_path}.tmp", "wb") as image_file:
                for chunk in image_r.iter_content(BLOCK_SIZE):
                    image_file.write(chunk)
            os.rename(f"{image_path}.tmp", image_path)
        else:
            print_log(component, "image already downloaded, skipping")
    elif "videoRenderer" in attachment:
        thumb_url = None
        if "videoId" in attachment["videoRenderer"]:
            video_id = attachment["videoRenderer"]["videoId"]
            thumb_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        elif "thumbnail" in attachment["videoRenderer"]:
            thumb_url = urlparse.urljoin(attachment["videoRenderer"]["thumbnail"]["thumbnails"][-1]["url"], "maxresdefault.jpg")
            print_log(component, "could not get video ID, video may be private or deleted")
        if thumb_url:
            print_log(component, f"downloading thumbnail")
            thumb_r = requests.get(thumb_url, stream=True, allow_redirects=True)
            thumb_ext = thumb_r.headers["Content-Type"].split("/", 1)[1].replace("jpeg", "jpg")
            thumb_path = f"{path}_thumb.{thumb_ext}"
            if not os.path.isfile(thumb_path):
                if os.path.isfile(f"{thumb_path}.tmp"):
                    os.remove(f"{thumb_path}.tmp")
                with open(f"{thumb_path}.tmp", "wb") as thumb_file:
                    for chunk in thumb_r.iter_content(BLOCK_SIZE):
                        thumb_file.write(chunk)
                os.rename(f"{thumb_path}.tmp", thumb_path)
            else:
                print_log(component, "thumbnail already downloaded, skipping")
        else:
            print_log(component, "could not get video thumbnail url for post")

def clean_name(text):
    return re.sub(CLEAN_FILENAME_KINDA, "_", text)

def print_log(component, message, end="\n"):
    print(f"[{component}] {message}", end=end)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = get_arguments()
    # set cookies for retrieving posts that need auth
    if args.cookies:
        if os.path.isfile(args.cookies):
            use_cookies(args.cookies)
        else:
            print_log("ytct", f"could not find cookies file \'{args.cookies}\', continuing without cookies...")
    usable_archive = None
    if args.post_archive:
        try:
            path = os.path.join(args.post_archive, args.archive_name)
            if not args.author_name:
                open(path, "a")
                usable_archive = path
            else:
                if args.author_name:
                    db_table_name = args.author_name
                else:
                    db_table_name = args.archive_name[0:-7]
                print(f"資料庫接連接：{path} | {db_table_name}")
                db = database(path, db_table_name)
                db.create_new_table()
                print("成功讀取資料庫")
                usable_archive = path
        except:
            print_log("ytct", f"cannot write to the archive file {path}, continuing...")
    if not os.path.isdir(args.directory):
        try:
            os.makedirs(args.directory)
        except:
            print_log("ytct", "failed to create output directory")
            sys.exit(1)
    for link in args.links:
        post_id_m = re.search(POST_REGEX, link)
        channel_id_m = re.search(CHANNEL_REGEX, link)
        if post_id_m:
            post_id = post_id_m.group("post_id")
            if args.author_name:
                get_post_lite(post_id, db)
            else:
                get_post(post_id, usable_archive)
        elif channel_id_m:
            channel_handle = channel_id_m.group("channel_handle")
            if channel_handle:
                channel_id = get_channel_id_from_handle(channel_handle)
            else:
                channel_id = channel_id_m.group("channel_id")

            if args.author_name:
                get_channel_posts_lite(channel_id, db)
            else:
                get_channel_posts(channel_id, usable_archive)
        else:
            print_log("ytct", f"could not parse link/id {link}")
    print_log("ytct", "finished")
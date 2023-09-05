import json, os, datetime, subprocess, requests, time, zipfile
from plugin import lite, dataformat
from misskey import Misskey
from urllib.parse import unquote, quote

def upload_to_discord_with_file(file_path:str):
    notify_type = ['all','importent', 'download']
    if now_channel["notify"]["discord"]["enable"]:
        if now_channel["notify"]["discord"]["type"] in notify_type:
            discord_webhook = now_channel["notify"]["discord"]["webhook_url"]
            file_size = os.path.getsize(file_path)
            max_allowed_size = 25 * 1024 * 1024
            if file_size > max_allowed_size:
                print("File size exceeds the maximum allowed size.")
                return
            file_name = file_path.split("\\")[-1] if '\\' in file_path  else file_path.split("/")[-1]
            data = {"content" : f'{now_channel["author_name"]} 下載完成：{file_name}'}
            with open(file_path, 'rb') as file:
                files = {'file': (file_name,file)}
                payload = {'payload_json': (json.dumps(data))}
                try:
                    result = requests.post(discord_webhook, files=files, data=payload)
                    result.raise_for_status()
                    print("Payload delivered successfully, code {}.".format(result.status_code))
                    return True
                except requests.exceptions.HTTPError as err:
                    print(err)
                    return False

def print_log(status, component, message, end='\n'):
    print(f'{component} |【{status}】 {message}',end=end)

def check_file(path, component): 
    if not os.path.exists(path):
        print_log('Error', component, f'路徑檔案不存在\"{path}\"')
        exit(1)

def wget(url, save_path, umask=777):
    wget = f'\"{os.path.join(os.getcwd(), os.path.join("plugin", "wget.exe"))}\"' if os.name == 'nt' else 'wget'
    component = 'Wget'
    file_name = save_path.split("/")[-1]
    if os.path.exists(save_path):
        print_log('Skip', component, f'{file_name} 檔案已存在，跳過下載')
        return 'File Exist'
    umask = str(umask)
    url = quote(url, safe=':/?&=_-')
    #下載器
    print_log('wget', component, f'{file_name} 下載網址：\"{url}\"')
    print_log('wget', component, f'{file_name} 寫入路徑：\"{save_path}\"')
    retry = 0
    while retry < 3:
        if 'zip' in file_name:
            command = f'{wget} --content-disposition -O \"{save_path}\" \"{url}\"'
        else:
            command = f'{wget} -O \"{save_path}\" \"{url}\"'
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        # 檢查返回碼
        if result.returncode == 0:
            print_log('wget', component, f"{file_name} 下載成功")
            notify_type = ['all','importent', 'download']
            if now_channel["notify"]["discord"]["enable"]:
                if now_channel["notify"]["discord"]["type"] in notify_type:
                    upload_to_discord_with_file(save_path)
            print_log('wget', component, f"{file_name} 設置權限：{umask}")
            command = f'chmod -R {umask} \"{save_path}\"' if os.name != 'nt' else f'icacls \"{save_path}\" /grant Everyone:(OI)(CI)F'
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print_log('wget', component, f"{file_name} 設置成功")
            else:
                print_log('wget', component, f"{file_name} 設置權限失敗")
            if 'zip' in file_name:
                try:
                    print_log('zipfile', component, f'正在解壓縮\"{save_path}\"')
                    with zipfile.ZipFile(save_path, 'r') as zip_ref:
                        zip_ref.extractall(os.path.dirname(save_path))
                        print_log('zipfile', component, f'{file_name} 解壓縮完成！')
                        try:
                            os.remove(save_path)
                            print_log('zipfile', component, f'{file_name} 壓縮檔已刪除')
                        except FileNotFoundError:
                            print_log('zipfile', component, f'{file_name} 壓縮檔不存在')
                        except PermissionError:
                            print_log('zipfile', component, f'{file_name} 無法刪除壓縮檔，權限不足')
                        except Exception as e:
                            print_log('zipfile', component, f'{file_name} 刪除壓縮檔時出現錯誤：{e}')
                except Exception as e:
                    print_log('zipfile', component, f'{file_name} 解壓縮發生錯誤，路徑：\"{save_path}\"\n錯誤訊息：{str(e)}')
                    return 'Extract Zip File Failed'
            break
        else:
            retry += 1
            if '404 Not Found' in result.stderr and '302 Found' in result.stderr:
                print_log('Skip', component, f'{file_name} 檔案已被移除，跳過此下載')
                os.remove(save_path)
                return 'File has been remove'
            print_log('Download', component, f'{file_name} Failed 下載失敗: \"{url}\"\n錯誤訊息：\n, {result.stderr}')
            print_log('Download', component, f'{file_name} Retry 第{retry}次 10秒後重新下載')
            time.sleep(10)
    if retry == 3:
        print_log('Error', component, f'{file_name} 下載失敗: \"{url}\"')
        print_log('Error', component, f'{file_name} 下載失敗: \"{save_path}\"')
        print_log('Error', component, f'{file_name} 錯誤訊息：\n{result.stderr}')
        return 'Error'
    return 'Successful'

def get_abs_path(path):
    path = path.replace("/", "\\") if os.name == 'nt' else path.replace("\\", "/")
    path_abs = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
    try:
        if os.name == 'nt':
            os.makedirs(os.path.dirname(path_abs), exist_ok=True) if '.' in path.split('\\')[-1] else os.makedirs(path_abs, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(path_abs), exist_ok=True) if '.' in path.split('/')[-1] else os.makedirs(path_abs, exist_ok=True)
    except:
        print_log('Error','檢測路徑',f'無法建立資料夾路徑 \"{path_abs}\"')
        exit(1)
    return path_abs

def load_channels(folder = os.path.join(os.getcwd(),'channels')):
    component = '讀取清單'
    print_log('Info', component,f'開始匯入頻道列表，路徑：\"{folder}\"')
    channels_list = []
    files = os.listdir(folder)
    for file in files:
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path) and ".json" in file:
            with open(file_path, 'r') as content:
                channel = json.load(content)
                print_log('Info', component,f'匯入：\"{file}\"')
                channel["name"] = file[0:-5]
                channels_list.append(channel)
    print_log('Successful', component,f'匯入結束，匯入 {len(channels_list)}筆資料')
    return channels_list


def call_ytct(ytct = os.path.join(os.path.join(os.getcwd(), 'plugin'), 'ytct.py')):
    component = 'ytct'
    check_file(ytct, component)
    print_log('Info', component, f'開始下載頻道：\"{now_channel["name"]}\"')
    print_log('Info', component, f'頻道網址：\"https://www.youtube.com/channel/{now_channel["channelid"]}/community\"')
    command = f'python "{ytct}" '
    if now_channel["cookies"]["enable"]:
        #Cookies相關
        cookies_path = get_abs_path(now_channel["cookies"]["file_path"])
        print_log('Info',component,f'讀取Cookies：\"{cookies_path}\"')
        check_file(cookies_path, component)
        command += f'--cookies "{cookies_path}" '
    if now_channel["archive"]["enable"]:
        #Archive相關
        archive_path = get_abs_path('archive') if now_channel["archive"]["folder_path"] == "" else get_abs_path(now_channel["archive"]["folder_path"])
        archive_name = now_channel["name"]+'.sqlite' if now_channel["archive"]["file_name"] == "" else now_channel["archive"]["file_name"]
        full_path = os.path.join(archive_path, archive_name) if '.txt' in archive_name or '.sqlite' in archive_name else os.path.join(archive_path, archive_name+'.sqlite')
        print_log('Info',component,f'讀取archive：\"{full_path}\"')
        command += f'--post-archive "{archive_path}" --archive-name "{archive_name}" '
        if '.sqlite' in archive_name:
            command += f'--author-name "{now_channel["author_name"]}" '
    post_save_path = get_abs_path(os.path.join("downloads", now_channel["name"])) if now_channel["post_save_path"] == "" else get_abs_path(now_channel["post_save_path"])
    if now_channel["date_folder"]:
        #年月日資料夾相關
        today = datetime.datetime.now()
        year_month = (today.year%100)*100+today.month
        year_month_day = (year_month + 200000)*100+today.day
        post_save_path = get_abs_path(os.path.join(post_save_path, os.path.join(str(year_month), str(year_month_day))))
    command += f'-d "{post_save_path}" '
    if now_channel["cookies"]["check_cookies"]:
        command += '--check-membership '
    print_log('Info', component, f'貼文儲存位置：\"{now_channel["post_save_path"]}\"')
    #command += '--dates '
    command += f'https://www.youtube.com/channel/{now_channel["channelid"]}'
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        dl_times = 0
        for line in result.stdout.splitlines():
            if 'found' in line and 'posts' in line:
                posts_amount = line.split(' ')[-2]
            elif 'writing'in line and '.json' in line:
                dl_times += 1
                download_post = []
                text = f'下載貼文：\"{line.split(" ")[-1][0:-5]}\"'
                print_log('ytct', component, text)
                if now_channel["notify"]["discord"]["enable"]:
                    notify_type = ['all', 'post']
                    if now_channel["notify"]["discord"]["type"] in notify_type:
                        notify_json = {
                            "content": text
                        }
                        webhook_url = now_channel["upload"]["discord"]["webhook_url"] if now_channel["notify"]["discord"]["webhook_url"] == "" else now_channel["notify"]["discord"]["webhook_url"]
                        discord_webhook(webhook_url, notify_json)
                download_post.append(line.split(" ")[-1])
            elif 'posts is fewer than archive maybe cookie has been expired' in line:
                text = f'設定檔：\"{now_channel["name"]}\" 無法搜索會限貼文，cookies過期了，請檢查：\"{now_channel["cookies"]["file_path"]}\"'
                print_log('Info', component, text)
                if now_channel["notify"]["discord"]["enable"]:
                    notify_type = ['all','importent', 'post']
                    if now_channel["notify"]["discord"]["type"] in notify_type:
                        notify_json = {
                            "content": text
                        }
                        webhook_url = now_channel["upload"]["discord"]["webhook_url"] if now_channel["notify"]["discord"]["webhook_url"] == "" else now_channel["notify"]["discord"]["webhook_url"]
                        discord_webhook(webhook_url, notify_json)
            elif 'the cookies have not expired' in line:
                text = f'搜索到會限貼文，cookies尚未過期'
                print_log('Info', component, text)

        print_log('Successful', component, f'下載完成，索引總貼文數量：\"{posts_amount}\" | 下載貼文數量：\"{dl_times}\"')
    else:
        print_log('Error', component, '程式錯誤，顯示運行訊息：')
        for line in result.stdout.splitlines():
            print(line)
        exit(1)

def discord_webhook(webhook_url, data):
    component = 'Discord'
    result = requests.post(webhook_url, json = data)
    try:
        result.raise_for_status()
        time.sleep(1)
    except requests.exceptions.HTTPError as err:
        print_log('Error', component, f'發送Discord失敗，錯誤訊息：{err}')
    else:
        print_log('Successful', component,f'發送Discord成功, 代碼：{result.status_code}')
        return True

def upload_discord():
    component = 'Discord'
    archive_path = get_abs_path('archive') if now_channel["archive"]["folder_path"] == "" else get_abs_path(now_channel["archive"]["folder_path"])
    archive_name = now_channel["name"]+'.sqlite' if now_channel["archive"]["file_name"] == "" else now_channel["archive"]["file_name"]
    full_path = os.path.join(archive_path, archive_name) if '.txt' in archive_name or '.sqlite' in archive_name else os.path.join(archive_path, archive_name+'.sqlite')
    main_channel = now_channel["main_channel"] if now_channel["main_channel"] != "" else f'https://www.youtube.com/channel/{now_channel["channelid"]}'
    if os.path.isfile(full_path) and '.sqlite' in archive_name:
        db = lite.database(full_path, now_channel["author_name"])
        unupload_posts = db.get_unupload_posts('upload_discord')
        for unupload_post in unupload_posts:
            post_json = dataformat.format_to_json(json.loads(unupload_post[1])).format_to_discord_webhook(now_channel["author_name"], main_channel)
            print_log('Info', component, f'{unupload_post[0]} 準備發送Discord')
            if discord_webhook(now_channel["upload"]["discord"]["webhook_url"], post_json):
                try:
                    db.insert_post_data(db.get_id(unupload_post[0]), 'upload_discord', 1)
                    print_log('Successful', component, f'{unupload_post[0]} 登錄發送成功至記錄檔完成')
                except Exception as e:
                    print_log('Error', component, f'{unupload_post[0]} 登錄發送成功至記錄檔失敗，錯誤訊息：{e}')
    else:
        print_log('Error', component, f'無法使用sqlite記錄檔：\"{full_path}\"')
        
def upload_misskey():
    component = 'Misskey'
    archive_path = get_abs_path('archive') if now_channel["archive"]["folder_path"] == "" else get_abs_path(now_channel["archive"]["folder_path"])
    archive_name = now_channel["name"]+'.sqlite' if now_channel["archive"]["file_name"] == "" else now_channel["archive"]["file_name"]
    full_path = os.path.join(archive_path, archive_name) if '.txt' in archive_name or '.sqlite' in archive_name else os.path.join(archive_path, archive_name+'.sqlite')
    if os.path.isfile(full_path) and '.sqlite' in archive_name:
        db = lite.database(full_path, now_channel["author_name"])
        unupload_posts = db.get_unupload_posts('upload_misskey')
        for unupload_post in unupload_posts:
            print_log('Info', component, f'{unupload_post[0]} 準備發送Misskey')
            post = dataformat.format_to_json(json.loads(unupload_post[1])).format_to_misskey()
            SERVER_HOST = now_channel["upload"]["misskey"]["url"]
            API_TOKEN = now_channel["upload"]["misskey"]["token"]
            try:
                mk = Misskey(SERVER_HOST, i=API_TOKEN)
                mk.notes_create(
                    text=post,
                    visibility='home',
                    )
            except Exception as e:
                print_log('Error', component, f'{unupload_post[0]} 發送失敗，錯誤訊息：{e}')
            else:
                print_log('Successful', component,f'{unupload_post[0]} 發送成功')
                try:
                    db.insert_post_data(db.get_id(unupload_post[0]), 'upload_misskey', 1)
                    print_log('Successful', component, f'{unupload_post[0]} 登錄發送成功至記錄檔成功')
                except Exception as e:
                    print_log('Error', component, f'{unupload_post[0]} 登錄發送成功至記錄檔失敗，錯誤訊息：{e}')
    else:
        print_log('Error', component, f'無法使用sqlite記錄檔：\"{full_path}\"')

def download_post_link(mediafire= os.path.join(os.path.join(os.getcwd(), 'plugin'), 'mediafire.py')):
    #urls: List
    component = 'DownloadPostLink'
    download_path = get_abs_path(os.path.join('downloads', os.path.join(now_channel["name"], 'downloads'))) if now_channel["download_content_link"]["folder_path"] == "" else get_abs_path(now_channel["download_content_link"]["folder_path"])
    archive_path = get_abs_path('archive') if now_channel["archive"]["folder_path"] == "" else get_abs_path(now_channel["archive"]["folder_path"])
    archive_name = now_channel["name"]+'.sqlite' if now_channel["archive"]["file_name"] == "" else now_channel["archive"]["file_name"]
    full_path = os.path.join(archive_path, archive_name) if '.txt' in archive_name or '.sqlite' in archive_name else os.path.join(archive_path, archive_name+'.sqlite')
    db = lite.database(full_path, now_channel["author_name"])
    undownload_posts = db.get_undownload_links()
    for undownload_post in undownload_posts:
        all_links = 0
        success = 0
        error = 0
        times = 1
        for link in undownload_post[1]:
            result_type = None
            link = unquote(unquote(link))
            if r'mediafire.com' in link:
                if '/file' == link[-5::]:
                    link = link[0:-5]
                if 'view' in link:
                    link = link.replace('/view/','/file_premium/')
                if '.' in link[-4::] and '/folder/' not in link:
                    print_log('Download', component, f'{undownload_post[0]} 使用Wget開始下載：\"{link}\"')
                    all_links += 1
                    download_path_tmp = os.path.join(download_path, unquote(link).split('/')[-1])
                    result_type = wget(link+'/file', download_path_tmp)
                    if result_type == 'Error':
                        error += 1
                    else: 
                        success += 1
                else:
                    print_log('Download', component, f'{undownload_post[0]} 使用mediafire.py開始下載：\"{link}\"')
                    all_links += 1
                    command = f'python "{mediafire}" -o "{download_path}" "{link}"'
                    print(command)
                    result = subprocess.run(command, capture_output=True, shell=True)
                    if result.returncode:
                        if "KeyError: 'folder_info'" in result.stderr.decode('utf-8') or "KeyError: 'folder_content'" in result.stderr.decode('utf-8'):
                            result_type = 'File has been remove'
                            print_log('Skip', component, f'檔案已被移除，跳過此下載：\"{link}\"')
                            success += 1
                        elif r"file\x1b[0m" in result.stderr.decode('utf-8') and 'HTTPError' in result.stderr.decode('utf-8'):
                            result_type = 'Link Not Newest'
                            print_log('Skip', component, f'連結並非最新，跳過此下載：\"{link}\"')
                            success += 1
                        else:
                            print(result.stdout.decode('utf-8'))
                            print_log('Error', component, f'{undownload_post[0]} 貼文連結：\"https://www.youtube.com/post/{undownload_post[0]}\"')
                            print_log('Error', component, f'{undownload_post[0]} 下載失敗：\"{link}\"')
                            error += 1
                    else:
                        success += 1
                        if 'www' in link:
                            download_path_tmp = os.path.join(download_path, link.split('/')[-1])
                            if os.path.exists(download_path_tmp):
                                print_log('Info', component, f'{undownload_post[0]} 開始壓縮檔案："{download_path_tmp}.zip"')
                                with zipfile.ZipFile(download_path_tmp+'.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
                                    for root, dirs, files in os.walk(download_path_tmp):
                                        for file in files:
                                            file_path = os.path.join(root, file)
                                            relative_path = os.path.relpath(file_path, download_path_tmp)
                                            zipf.write(file_path, relative_path)
                                print_log('Info', component, f'{undownload_post[0]} 壓縮完成')
                                upload_to_discord_with_file(download_path_tmp+'.zip')
                                os.remove(download_path_tmp+'.zip')
                                print_log('Successful', component, f'{undownload_post[0]} 移除暫存壓縮檔')
            elif r'https://www.dropbox.com/' in link:
                print_log('Download', component, f'{undownload_post[0]} 使用Wget開始下載：\"{link}\"')
                link_tmp = link 
                if r'&dl=0' in link_tmp:
                    link_tmp = link_tmp.split(r'&dl=0')[0]
                if r'?rlkey' in link_tmp:
                    link_tmp = link_tmp.split(r'?rlkey')[0]
                if '.' not in link_tmp[-4::]:
                    download_path_tmp = os.path.join(download_path, f'{link_tmp.split("/")[-1]}.zip')
                else:
                    download_path_tmp = os.path.join(download_path, unquote(link_tmp).split('/')[-1])
                all_links += 1
                result_type = wget(link, download_path_tmp)
                if result_type == 'Error':
                    error += 1
                else: 
                    success += 1
            elif r'https://yt3.ggpht.com/' in link:
                print_log('Download', component, f'{undownload_post[0]} 使用Wget開始下載：\"{link}\"')
                all_links += 1
                today = datetime.datetime.now()
                name = f'{str((today.year%100)*100+today.month)}_壁紙 {undownload_post[0]} {times}.png'
                times += 1
                download_path_tmp = os.path.join(download_path, name)
                result_type = wget(link, download_path_tmp)
                if result_type == 'Error':
                    error += 1
                else: 
                    success += 1
            else:
                print_log('Skip', component, f'{undownload_post[0]} 跳過\"{link}\"非下載連結')
            if result_type:
                if now_channel["notify"]["discord"]["enable"]:
                    text_default = f'貼文：\"https://www.youtube.com/post/{undownload_post[0]}\"\n網址：\"{link}\"'
                    if result_type == 'Error':
                        notify_type = ['all','error', 'importent', 'download']
                        text = f'{undownload_post[0]} 下載此網址失敗\n{text_default}'
                    elif result_type == 'Successful':
                        notify_type = ['all','download']
                        text = f'{undownload_post[0]} 下載成功\n{text_default}'
                    elif result_type == 'Extract Zip File Failed':
                        notify_type = ['all','error', 'importent', 'download']
                        text = f'{undownload_post[0]} 下載成功，但自動解壓縮失敗\n{text_default}'
                    elif result_type == 'File has been remove':
                        notify_type = ['all','importent', 'download']
                        text = f'{undownload_post[0]} 檔案已被移除\n{text_default}'
                    elif result_type == 'File Exist':
                        notify_type = ['all','download']
                        text = f'{undownload_post[0]} 檔案已存在，自動跳過\n{text_default}'
                    elif result_type == 'Link Not Newest':
                        notify_type = ['all','error', 'importent', 'download']
                        text = f'{undownload_post[0]} 檔案已存在，自動跳過\n{text_default}'
                    if now_channel["notify"]["discord"]["type"] in notify_type:
                        notify_json = {
                            "content": text
                        }
                        webhook_url = now_channel["upload"]["discord"]["webhook_url"] if now_channel["notify"]["discord"]["webhook_url"] == "" else now_channel["notify"]["discord"]["webhook_url"]
                        discord_webhook(webhook_url, notify_json)
        
        if all_links:
            print_log('Finish', component, f'下載結束，總數：\"{all_links}\" | 成功數：\"{success}\" | 失敗數：\"{error}\"')
        if all_links == success:
            db.insert_post_data(db.get_id(undownload_post[0]), 'post_links_download', 1)
            
def main():
    channels = load_channels()
    print('\n')
    
    for channel in channels:
        #下載會限貼文
        global now_channel
        now_channel = channel
        call_ytct()
        #上傳會限貼文
        if now_channel["upload"]["discord"]["enable"] :
            upload_discord()
        if now_channel["upload"]["misskey"]["enable"] :
            upload_misskey()
        #下載會限檔案連結
        if now_channel["download_content_link"]["enable"]:
            download_post_link()
        print('\n')

if __name__ == '__main__':
    main()
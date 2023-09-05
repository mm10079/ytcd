import json, os, time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def default_setting():
    global data
    global filename
    filename = "default.json"
    data = {
        "author_name": "",
        "main_channel": "",
        "channelid": "",
        "post_save_path": "",
        "date_folder": 0,
        "download_content_link": {
            "enable": 0,
            "folder_path": ""
        },
        "cookies": {
            "enable": 0,
            "file_path": "cookies/cookie.txt",
            "check_cookies": 1
        },
        "archive": {
            "enable": 0,
            "folder_path": "",
            "file_name": ""
        },
        "upload": {
            "misskey": {
                "enable": 0,
                "token": "",
                "url": ""
            },
            "discord": {
                "enable": 0,
                "webhook_url": ""
            }
        },
        "notify": {
            "discord": {
                "enable": 0,
                "type": "importent",
                "webhook_url": ""
            }
        }
    }

def edit_channel():
    global data
    global filename
    clear_screen()

    if filename == 'default.json':
        while True:
            #訂閱檔名稱
            filename = input("請輸入檔案名稱(僅辨識用)：")
            if '.json' != filename[-5::]:
                filename += '.json'
            clear_screen()
            print(f'輸入的是：{filename}')
            doit = input("確認？Y/N：")
            if doit =='y' or doit == "Y":
                break


    while True:
        #資料庫與Discord標題名稱
        clear_screen()
        text = '更改資料庫表單名稱與Discord訊息框名稱\n使用同個表單名稱與同個資料庫位置會導致讀取到相同的資料表，請注意！\n可以直接用頻道名稱，範例：存流 -ASU-\n\n'
        text += f'目前名稱：{data["author_name"]}' if data["author_name"] != "" else f'目前名稱：{filename[0:-5]}'
        print(text)
        input_tmp = input('請輸入名稱(不輸入將保持原先內容)：')
        if input_tmp != '':
            data["author_name"] = input_tmp
            clear_screen()
            print(f'輸入的是：{data["author_name"]}')
            doit = input("確認？Y/N：")
            if doit =='y' or doit == "Y":
                break
        elif input_tmp == '' and data["author_name"] != '':
            break
        else:
            data["author_name"] = filename[0:-5]
            break

    while True:
        #頻道ID
        clear_screen()
        text = '更改頻道ID\nID為24碼頻道ID，例如："https://www.youtube.com/channel/UC3VN9h8fokwB2XURWHNcdWw/"中的"UC3VN9h8fokwB2XURWHNcdWw"\n取得方式請詳見channels中stop內的"設定檔介紹.txt"'
        if data["channelid"]:
            text += f'\n\n目前頻道ID：{data["channelid"]}'
        print(text)
        if data["channelid"]:
            input_tmp = input("請輸入頻道ID(不輸入將保持原先內容)：")
        else:
            input_tmp = input("請輸入頻道ID：")
        if len(input_tmp) == 24:
            data["channelid"] = input_tmp
            print(f'輸入的是：{data["channelid"]}')
            doit = input("確認？Y/N：")
            if doit =='y' or doit == "Y":
                break
        elif data["channelid"]:
            break
        else:
            print('應為24字，請確認是否正確！')
            time.sleep(2)

    while True:
        #main_channel
        clear_screen()
        text = '設定第二頻道連結(如果設定用於副頻道，可以填寫主頻道連結)，此為Discord相關功能\n\n'
        text += f'目前連結為："{data["main_channel"]}"' if data["main_channel"] != "" else f'目前連結為："https://www.youtube.com/channel/{data["channelid"]}"'
        print(text)
        input_tmp = input('請輸入連結(不輸入將保持原先內容)：')
        if input_tmp:
            data["main_channel"] = input_tmp
        if data["main_channel"]:
            print(f'輸入的是：{data["main_channel"]}')
        else:
            print(f'輸入的是：https://www.youtube.com/channel/{data["channelid"]}')
        doit = input("確認？Y/N：")
        if doit =='y' or doit == "Y":
            break

    while True:
        #貼文存檔位置
        clear_screen()
        text = '請輸入貼文儲存的位置(將自動轉換斜線方向)\n\n'
        text += f'目前儲存位址為："{data["post_save_path"]}"' if data["post_save_path"] else f'目前儲存位址為："downloads"'
        print(text)
        input_tmp = input("請輸入位置(不輸入將保持原先內容)：").replace('\\\\','/').replace('\\','/')
        if input_tmp != "" :
            data["post_save_path"] = input_tmp
        print(f'輸入的是：{data["post_save_path"]}')
        doit = input("確認？Y/N：")
        if doit =='y' or doit == "Y":
            break

    while True:
        #資料夾年月分類
        clear_screen()
        text = f'是否要啟用年月分類\n例如：儲存路徑/年月/年月日/貼文\n不啟用則全部存在同一個資料夾\n\n目前為：{data["date_folder"]}'
        print(text)
        data["date_folder"] = int(input("是否啟動：1.啟動 0.關閉："))
        break

    while True:
        #下載貼文中的檔案
        clear_screen()
        text = '啟用自動下載貼文中的檔案\n支援：Dropbox、Mediafire與含"壁紙"內容的貼文圖片\n'
        text += '1.是否啟用下載(目前"啟用")\n' if data["download_content_link"]["enable"] else '1.是否啟用下載(目前"關閉")\n'
        text += '2.目前儲存位置：downloads\n' if data["download_content_link"]["folder_path"] == "" else f'2.目前儲存位置：{data["download_content_link"]["folder_path"]}\n'
        text += '3.重置回預設值\n'
        text += '0.完成編輯'
        print(text)
        choice = input("請輸入選項：")
        if choice == '0':
            break
        elif choice == '1':
            doit = input('是否啟動？Y/N：')
            data["download_content_link"]["enable"] = 1 if doit == 'Y' or doit == 'y' or doit == 1 else 0
        elif choice == '2':
            input_tmp = input("請輸入位置(不輸入將保持原先內容)：").replace('\\\\','/').replace('\\','/')
            if input_tmp != "" :
                data["download_content_link"]["folder_path"] = input_tmp
        elif choice == '3':
            data["download_content_link"]["enable"] = 0
            data["download_content_link"]["folder_path"] = ''

    while True:
        #cookies設定
        clear_screen()
        text = '啟用Cookies功能\n若要下載會限資料必須設定Cookies功能\n可以用Chrome的插件"EditThisCookies"取得Cookies\n'
        text += '1.是否啟用Cookies(目前"啟用")\n' if data["cookies"]["enable"] else '1.是否啟用Cookies(目前"關閉")\n'
        text += f'2.目前儲存位置：{data["cookies"]["file_path"]}\n'
        text += '3.是否啟用Cookies檢查(目前"啟用")\n' if data["cookies"]["check_cookies"] else '1.是否啟用Cookies檢查(目前"關閉")\n'
        text += '4.重置回預設值\n'
        text += '0.完成編輯'
        print(text)
        choice = input("請輸入選項：")
        if choice == '0':
            break
        elif choice == '1':
            doit = input('是否啟動？Y/N：')
            data["cookies"]["enable"] = 1 if doit == 'Y' or doit == 'y' or doit == 1 else 0
        elif choice == '2':
            input_tmp = input('請輸入位置(不輸入將保持原先內容)：').replace('\\\\','/').replace('\\','/')
            if input_tmp != '' :
                data["cookies"]["file_path"] = input_tmp
        elif choice == '3':
            print('Cookies檢查會自動比對是否有會限貼文，若檢驗失敗將會寄送Notify的Discord訊息通知。')
            doit = input('是否啟動？Y/N：')
            data["cookies"]["check_cookies"] = 1 if doit == 'Y' or doit == 'y' or doit == 1 else 0
        elif choice == '4':
            data["cookies"]["enable"] = 0
            data["cookies"]["file_path"] = 'cookies/cookie.txt'
            data["cookies"]["check_cookies"] = 1

    while True:
        #archive設定
        clear_screen()
        text = '啟用資料庫登記功能，將會記錄已下載過的貼文並自動跳過\n可以與其他設定檔使用同個sqlite資料庫\nsqlite如何察看與更改可以使用工具中的sqlite檢視\n'
        text += '1.是否啟用資料庫(目前"啟用")\n' if data["archive"]["enable"] else '1.是否啟用資料庫(目前"關閉")\n'
        text += f'2.資料庫儲存位置：{data["archive"]["folder_path"]}\n' if data["archive"]["folder_path"] else '2.資料庫儲存位置："archive"\n'
        text += f'3.資料庫檔案名稱：{data["archive"]["file_name"]}\n' if data["archive"]["file_name"] else f'3.資料庫檔案名稱：{filename[0:-5]}.sqlite\n'
        text += '4.重置回預設值\n'
        text += '0.完成編輯'
        print(text)
        choice = input("請輸入選項：")
        if choice == '0':
            break
        elif choice == '1':
            doit = input('是否啟動？Y/N：')
            data["archive"]["enable"] = 1 if doit == 'Y' or doit == 'y' or doit == 1 else 0
        elif choice == '2':
            input_tmp = input('請輸入位置(不輸入將保持原先內容)：').replace('\\\\','/').replace('\\','/')
            if input_tmp != '' :
                data["archive"]["folder_path"] = input_tmp
        elif choice == '3':
            input_tmp = input('請輸入資料庫檔案名稱(不輸入將保持原先內容)：')
            data["archive"]["file_name"] = input_tmp if '.sqlite' == input_tmp[-7::] else input_tmp + '.sqlite'
        elif choice == '4':
            data["archive"]["enable"] = 0
            data["archive"]["folder_path"] = ''
            data["archive"]["file_name"] = ''

    while True:
        #upload設定
        clear_screen()
        text = '上傳相關選項，啟用Discord或Misskey功能自動發送貼文\n'
        text += '1.是否啟用Misskey(目前"啟用")\n' if data["upload"]["misskey"]["enable"] else '1.是否啟用Misskey(目前"關閉")\n'
        text += f'2.Misskey Token：{data["upload"]["misskey"]["token"]}\n'
        text += f'3.Misskey Url：{data["upload"]["misskey"]["url"]}\n'
        text += '4.是否啟用Discord(目前"啟用")\n' if data["upload"]["discord"]["enable"] else '4.是否啟用Discord(目前"關閉")\n'
        text += f'5.Discord Url：{data["upload"]["discord"]["webhook_url"]}\n'
        text += '6.重置回預設值\n'
        text += '0.完成編輯'
        print(text)
        choice = input("請輸入選項：")
        if choice == '0':
            break
        elif choice == '1':
            doit = input('是否啟動？Y/N：')
            data["upload"]["misskey"]["enable"] = 1 if doit == 'Y' or doit == 'y' or doit == 1 else 0
        elif choice == '2':
            input_tmp = input('請輸入金鑰(不輸入將保持原先內容)：')
            if input_tmp != '' :
                data["upload"]["misskey"]["token"] = input_tmp
        elif choice == '3':
            input_tmp = input('請輸入連結(不輸入將保持原先內容)：')
            if input_tmp != '' :
                data["upload"]["misskey"]["url"] = input_tmp
        elif choice == '4':
            doit = input('是否啟動？Y/N：')
            data["upload"]["discord"]["enable"] = 1 if doit == 'Y' or doit == 'y' or doit == 1 else 0
        elif choice == '5':
            input_tmp = input('請輸入連結(不輸入將保持原先內容)：')
            if 'https://discord.com/api/webhooks/' not in input_tmp:
                print(f'請輸入正確的Webhook網址，你輸入的是："{input_tmp}"')
                time.sleep(1)
            else:
                data["upload"]["discord"]["webhook_url"] = input_tmp
        elif choice == '6':
            data["upload"]["misskey"]["enable"] = 0
            data["upload"]["misskey"]["token"] = ''
            data["upload"]["misskey"]["url"] = ''
            data["upload"]["discord"]["enable"] = 0
            data["upload"]["discord"]["webhook_url"] = ''

    while True:
        #notify設定
        clear_screen()
        text = '訊息通知系統，Discord將發送系統訊息\n'
        text += '1.是否啟用Discord(目前"啟用")\n' if data["notify"]["discord"]["enable"] else '1.是否啟用Discord(目前"關閉")\n'
        text += f'2.通知種類：{data["notify"]["discord"]["type"]}\n'
        text += f'3.Discord Url：{data["notify"]["discord"]["webhook_url"]}\n'
        text += '4.重置回預設值\n'
        text += '0.完成編輯'
        print(text)
        choice = input("請輸入選項：")
        if choice == '0':
            if data["notify"]["discord"]["enable"] and data["notify"]["discord"]["type"] and data["notify"]["discord"]["webhook_url"]:
                break
            elif not data["notify"]["discord"]["enable"]:
                break
            else:
                print('已啟用Discord通知，請完成其餘設定。')
                time.sleep(1)
        elif choice == '1':
            doit = input('是否啟動？Y/N：')
            data["notify"]["discord"]["enable"] = 1 if doit == 'Y' or doit == 'y' or doit == 1 else 0
        elif choice == '2':
            clear_screen()
            print(f'請選擇通知種類：\n1.all 所有訊息通知\n2.importent 通知下載異常、cookies預期與錯誤(推薦)\n3.download 通知所有下載訊息\n4.post 通知貼文儲存\n5.error 通知所有錯誤訊息\n0.取消')
            choice = input("請輸入選項：")
            if choice == '0' :
                continue
            if choice == '1' :
                data["notify"]["discord"]["type"] = 'all'
            if choice == '2' :
                data["notify"]["discord"]["type"] = 'importent'
            if choice == '3' :
                data["notify"]["discord"]["type"] = 'download'
            if choice == '4' :
                data["notify"]["discord"]["type"] = 'post'
            if choice == '5' :
                data["notify"]["discord"]["type"] = 'error'
        elif choice == '3':
            input_tmp = input('請輸入連結(不輸入將保持原先內容)：')
            if 'https://discord.com/api/webhooks/' not in input_tmp:
                print(f'請輸入正確的Webhook網址，你輸入的是："{input_tmp}"')
                time.sleep(1)
            else:
                data["notify"]["discord"]["url"] = input_tmp
        elif choice == '4':
            data["notify"]["discord"]["enable"] = 0
            data["notify"]["discord"]["type"] = ''
            data["notify"]["discord"]["webhook_url"] = ''


def load_file():
    global data
    global filename
    while True:
        clear_screen()
        print(f'目前已使用的檔案：{filename}')
        filelist = {}
        num = 0
        print("已啟用的訂閱：")
        for active_channel in os.listdir(os.path.join(os.getcwd(), "channels")):
            if active_channel == 'default.json':
                continue
            if '.json' in active_channel:
                num += 1
                print(f'{num}. {active_channel}')
                filelist[str(num)] = [active_channel,os.path.join(os.path.join(os.getcwd(), "channels"), active_channel)]
        print("\n停用的訂閱：")
        for active_channel in os.listdir(os.path.join(os.getcwd(), os.path.join("channels", "stop"))):
            if active_channel == 'default.json':
                continue
            if '.json' in active_channel:
                num += 1
                print(f'{num}. {active_channel}')
                filelist[str(num)] = [active_channel,os.path.join(os.path.join(os.getcwd(), os.path.join("channels", "stop")), active_channel)]
        print('\n0.離開')
        choice = input("\n請輸入編號：")
        if choice == '0':
            return
        try:
            doit = input(f'選擇 "{filelist[choice][0]}"，Y:使用設定檔 N:取消：')
            if doit == "Y" or doit == "y":
                filename = filelist[choice][0]
                with open(filelist[choice][1], encoding='utf-8') as file_data:
                    data = json.load(file_data)
                break
        except:
            print('無法讀取檔案！請選擇可使用的檔案')
            time.sleep(2)


def menu():
    while True:
        clear_screen()
        channel_path = os.path.join(os.getcwd(), 'channels')
        print('設定檔操作系統')
        print('設定檔儲存位置：channels')
        print(f'目前設定檔：{filename}')
        print('1.新建訂閱')
        print('2.讀取訂閱')
        print('3.編輯目前訂閱')
        print('4.儲存目前訂閱')
        print('5.顯示目前訂閱檔訊息')
        if os.path.exists(os.path.join(channel_path, filename)):
            print('6.停用訂閱')
        else:
            print('6.啟用訂閱')
        print('7.刪除訂閱')
        print('0.離開')
        choice = input("\n請輸入編號：")
        if choice == '0':
            exit()
        elif choice == '1':
            default_setting()
            edit_channel()
            clear_screen()
            print(json.dumps(data, indent=4, ensure_ascii=False))
            doit = input('顯示完成，Y:儲存設定檔 N:回到菜單：')
            if doit == 'y' or doit == 'Y' or doit == 1:
                save()
        elif choice == '2':
            load_file()
        elif choice == '3':
            edit_channel()
        elif choice == '4':
            save()
        elif choice == '5':
            print(json.dumps(data, indent=4, ensure_ascii=False))
            input('顯示完成，輸入任意訊息繼續：')
        elif choice == '6':
            if os.path.exists(os.path.join(channel_path, filename)):
                if filename != 'default.json':
                    os.rename(os.path.join(channel_path, filename), os.path.join(channel_path, os.path.join('stop', filename)))
            else:
                if filename != 'default.json':
                    os.rename(os.path.join(channel_path, os.path.join('stop', filename)), os.path.join(channel_path, filename))
        elif choice == '7':
            if os.path.exists(os.path.join(channel_path, filename)):
                if filename != 'default.json':
                    os.remove(os.path.join(channel_path, filename))
            else:
                if filename != 'default.json':
                    os.remove(os.path.join(channel_path, os.path.join('stop', filename)))
        else:
            print("請輸入正確的值！")
            time.sleep(2)
            
def save():
    if filename == 'default.json':
        print('無法儲存預設貼文，請新建貼文或讀取貼文')
        return
    with open(os.path.join(os.path.join(os.getcwd(), "channels"), filename), "w") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

def main():
    default_setting()
    menu()

if __name__ == '__main__':
    main()

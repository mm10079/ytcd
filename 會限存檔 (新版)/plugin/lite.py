import sqlite3
import datetime
import json

def print_log(type, component, message, end='\n'):
    print(f'{component} |【{type}】 {message}',end=end)

def replace_illegal_characters(word):
    # 将表名中的非法字符替换为空格
    word = word.replace('-', '').replace(',', '').replace('.', '').replace('"', '').replace('=', '').replace(' ', '')
    word = word.replace('()', '<>')
    return word

class database:
    def __init__(self, path, table_name):
        self.path = path
        self.table_name = replace_illegal_characters(table_name)
        self.component = 'Database'

    def create_new_table(self):
        print_log('Info', self.component, f'創建新的儲存表："{self.table_name}"')
        with sqlite3.connect(self.path) as conn:
            conn.cursor().execute(f'''CREATE TABLE IF NOT EXISTS {self.table_name}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_download_time       TEXT       ,
                post_id       TEXT      ,
                post_json       TEXT       ,
                post_links       TEXT       ,
                post_path       TEXT       ,
                upload_discord     INTEGER  DEFAULT 0,
                upload_misskey     INTEGER  DEFAULT 0,
                post_links_download     INTEGER  DEFAULT 0,
                membership     INTEGER  DEFAULT 0
            )''')

    def save_new_post(self, post_id):
        now = datetime.datetime.now()
        post_download_time = str(now.year*10000+now.month*100+now.day)
        print_log('Info', self.component, f'新增貼文紀錄："{post_id}"')
        with sqlite3.connect(self.path) as conn:
            conn.cursor().executemany(f'''
                            INSERT INTO {self.table_name}
                            (post_download_time,post_id,post_json,post_links,post_path,upload_discord,upload_misskey,post_links_download,membership) 
                            VALUES (?,?,?,?,?,?,?,?,?)''',
                        [(post_download_time,post_id,"","","",0,0,0,0)])

    def load_all_value(self):
        skip_ids = []
        with sqlite3.connect(self.path) as conn:
            for data in conn.cursor().execute(f"SELECT post_id FROM {self.table_name}"):
                skip_ids.append(data[0])
        print_log('Info', self.component, f'檢索以儲存貼文數：{len(skip_ids)}筆')
        return skip_ids

    def get_id(self, post_id):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(f'SELECT id FROM {self.table_name} WHERE post_id = ?', (post_id,))
            data = cursor.fetchone()
        return data[0]

    def get_specific_list(self, keyword, data_vaule):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.execute(f'SELECT * FROM {self.table_name} WHERE {keyword} = ?', (data_vaule,))
            data = cursor.fetchall()
        return data
    
    def insert_post_data(self, post_key, keyword, data):
        #post_key = id
        #keyword = 要更改的項目
        #data = 值
        print_log('Info', self.component, f'id:"{post_key}" "{keyword}"資料更改為:"{data}"')
        with sqlite3.connect(self.path) as conn:
            conn.cursor().execute(f'UPDATE {self.table_name} SET {keyword} = ? WHERE id = ?',(data,post_key,))

    def get_unupload_posts(self, keyword):
        print_log('Info', self.component, f'讀取所有{keyword}未上傳的貼文項目')
        posts = []
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute(f"PRAGMA table_info({self.table_name})")
            table_info = c.fetchall()
            times = 0
            for col_info in table_info:
                if 'post_id' == col_info[1]:
                    post_id_num = times
                elif 'post_json' == col_info[1]:
                    post_json = times
                elif keyword == col_info[1]:
                    keyword_num = times
                times += 1
            c.execute(f"PRAGMA table_info({self.table_name})")
            for data in c.execute(f"SELECT * FROM {self.table_name}"):
                if data[keyword_num] == 0:
                    posts.append([data[post_id_num],data[post_json]])
            print_log('Info', self.component, f'搜索到 {len(posts)}筆未上傳資料')
        return posts
    
    def get_undownload_links(self):
        print_log('Info', self.component, f'讀取所有未下載的貼文檔案鏈結')
        posts = []
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            c.execute(f"PRAGMA table_info({self.table_name})")
            table_info = c.fetchall()
            times = 0
            for col_info in table_info:
                if 'post_id' == col_info[1]:
                    post_id_num = times
                elif 'post_links' == col_info[1]:
                    post_link_num = times
                elif 'post_links_download' == col_info[1]:
                    keyword_num = times
                times += 1
            c.execute(f"PRAGMA table_info({self.table_name})")
            for data in c.execute(f"SELECT * FROM {self.table_name}"):
                if data[keyword_num] == 0:
                    posts.append([data[post_id_num],json.loads(data[post_link_num])])
            print_log('Info', self.component, f'搜索到 {len(posts)}筆未下載資料')
        return posts
                
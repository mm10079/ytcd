from urllib import parse

def print_log(type, component, message, end='\n'):
    print(f'{component} |【{type}】 {message}',end=end)

def translate_url(url):
    return parse.quote(url, safe=':/')

def format_image_url_to_full(text,type_text):
    text_find = text.find("=")
    format_text = "".join(map(str,list(text)[0:text_find]))
    text = format_text + "=s0" + type_text
    return text


class json_post_translation:

    def __init__(self,post_json):
        self.post_json=post_json
        self.post_id = post_json['post_id']
        self.component = 'Dataformat'

    #轉換json文字檔
    def channel_name(self):
        return self.post_json["author"]["authorText"]["accessibility"]["accessibilityData"]["label"]
    
    def channel_link(self):
        return f'https://www.youtube.com/channel/{self.post_json["channel_id"]}'

    def content_text_include_url_text(self):
        if self.post_json is not None:
            post_content_text_finish = ''
            for data in self.post_json["content_text"]["runs"]:
                if "urlEndpoint" in data :
                    post_content_text_finish += translate_url(data["urlEndpoint"]["url"])
                else :
                    post_content_text_finish += data["text"]
            if "videoRenderer" in self.post_json:
                print_log('Info', self.component, f'貼文存在影片 Post id: {self.post_id}')
                post_content_text_finish += f'\nhttps://www.youtube.com/watch?v={self.post_json["backstage_attachment"]["videoRenderer"]["videoId"]}'
            return f'''{post_content_text_finish}'''

    def image(self):
        img_list = []
        if "backstageImageRenderer" in self.post_json["backstage_attachment"] or "postMultiImageRenderer" in self.post_json["backstage_attachment"] :
            if "backstageImageRenderer" in self.post_json["backstage_attachment"]:
                images_target = self.post_json["backstage_attachment"]["backstageImageRenderer"]
            elif "postMultiImageRenderer" in self.post_json["backstage_attachment"]:
                images_target = self.post_json["backstage_attachment"]["postMultiImageRenderer"]

            if "image" in images_target:
                img_list.append(format_image_url_to_full(images_target["image"]["thumbnails"][-1]["url"],"-nd-v1"))
                print_log('Info', self.component, f'{self.post_id} 貼文存在圖片 尺寸：{str(images_target["image"]["thumbnails"][-1]["width"])}x{str(images_target["image"]["thumbnails"][-1]["height"])}')
            else:
                for img in images_target["images"]:
                    img_list.append(format_image_url_to_full(img["backstageImageRenderer"]["image"]["thumbnails"][-1]["url"],"-nd-v1"))
                print_log('Info', self.component, f'{self.post_id} 貼文存在圖片 尺寸：{str(img["backstageImageRenderer"]["image"]["thumbnails"][-1]["width"])}x{str(img["backstageImageRenderer"]["image"]["thumbnails"][-1]["height"])}')
        elif "videoRenderer" in self.post_json["backstage_attachment"]:
            img_list.append(self.post_json["backstage_attachment"]["videoRenderer"]["thumbnail"]["thumbnails"][-1]["url"])
        return img_list
    
    def post_link(self):
        post_post_link=f'https://www.youtube.com/channel/{self.post_json["channel_id"]}/community?lb={self.post_id}'
        return post_post_link
    
    def post_type(self):
        if self.post_json["sponsor_only_badge"] != None:
            return "**頻道會員專屬**"
        else:
            return "**公開推文**"

    def get_video_data(self):
        videoRenderer_tag = self.post_json['backstage_attachment']["videoRenderer"]
        video_link = f'https://www.youtube.com/watch?v={videoRenderer_tag["videoId"]}'
        video_title = videoRenderer_tag["title"]["runs"][0]["text"]
        try:
            video_description = videoRenderer_tag["descriptionSnippet"]["runs"][0]["text"]
        except:
            video_description = ''
        post_video = {"video_title":video_title,"video_link":video_link,"video_description":video_description}
        return post_video
    
    def author_icon(self):
        icon = "https:" + self.post_json["author"]["authorThumbnail"]["thumbnails"][-1]["url"]
        return icon

class format_to_json:
    def __init__(self, post_json):
        self.post_json=post_json
        self.post_content=json_post_translation(self.post_json)

    def format_to_discord_webhook(self,author_name, main_channel_link):
        data = {
            "content" : f'[{self.post_content.post_type()}]({self.post_content.post_link()})',
        }
        data["embeds"] = [{}]
        data["embeds"][0]["author"] = {}
        data["embeds"][0]["author"]["name"] = author_name#本帳名稱
        data["embeds"][0]["author"]["url"] = main_channel_link#本帳連結
        data["embeds"][0]["author"]["icon_url"] = self.post_content.author_icon()#小帳號縮圖
        data["embeds"][0]["title"] = self.post_content.channel_name() #小標題 頻道標籤
        data["embeds"][0]["description"] = self.post_content.content_text_include_url_text().replace('~~','～') #小介紹 貼文主體
        data["embeds"][0]["url"] = self.post_content.channel_link() #小標題連結 副頻道連結
        data["embeds"][0]["thumbnail"] = {}
        data["embeds"][0]["thumbnail"]["url"] = format_image_url_to_full(self.post_content.author_icon(),"-no-rj-mo")#右側方形縮圖
        if self.post_json['backstage_attachment'] != None:
            if "videoRenderer" in self.post_json['backstage_attachment']:
                if self.post_json['backstage_attachment']["videoRenderer"]["watchEndpoint"]["url"]  != None:
                    video_data = self.post_content.get_video_data()
                    data["embeds"] +=  [{
                        "title":video_data["video_title"],
                        "url":video_data["video_link"],
                        "description":video_data["video_description"]
                        }]
                else:
                    print_log('Info', 'Discord',f"{self.post_json['post_id']} 此貼文影片已遭移除或是隱藏，跳過添加影片網址步驟")
            for add_image in self.post_content.image():
                data["embeds"] += [{"image":{"url":""}}]
                data["embeds"][-1]["image"]["url"] = add_image#下方大圖
        data["embeds"] +=  [{
            "title":"** **",
            "description":""
            }]
        return data
    
    def format_to_misskey(self):
        post_content_text = self.post_content.post_type() + "\n" + self.post_content.content_text_include_url_text()
        post_content_text += f'\n[原文鏈結]({self.post_content.post_link()})'
        if self.post_json['backstage_attachment'] != None:
            if "videoRenderer" in self.post_json['backstage_attachment']:
                if self.post_json['backstage_attachment']["videoRenderer"]["watchEndpoint"]["url"]  != None:
                    video_data = self.post_content.get_video_data()
                    post_content_text += '\n---------------------------------\n'
                    post_content_text += video_data["video_title"] + '\n'
                    post_content_text += video_data["video_description"] + '\n'
                    post_content_text += translate_url(video_data["video_link"]) + '\n'
                    post_content_text += '\n---------------------------------\n'
                else:
                    print_log('Info', 'Misskey',f'{self.post_json["post_id"]} 此貼文影片已遭移除或是隱藏，跳過添加影片網址步驟')


            img_num = 1
            for add_image in self.post_content.image():
                post_content_text += f'[觀看貼文圖片{str(img_num)}]({add_image})'
                img_num += 1
        data = {
            "content" : post_content_text
            }
        return post_content_text
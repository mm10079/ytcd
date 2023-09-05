# ytcd
下載Youtube社群貼文、會限貼文，自動下載貼文中的mediafire、dropbox、壁紙圖片，並且發送貼文至Discord

安裝依賴項：
```
pip install gazpacho sqlite3 misskey zipfile
```
youtube_community_tab為fork [bot-jonas/youtube-community-tab](https://github.com/bot-jonas/youtube-community-tab)
```
pip install git+https://github.com/mm10079/youtube-community-tab.git
```

使用方法：
Windows用戶直接手動開啟**啟動.bat**

1.創建訂閱頻道內容，Linux用戶需手動建立、Windows用戶在**啟動.bat**中選 2.編輯訂閱頻道 操作即可
檔案路徑：\~/channels
範本與手動建檔的說明在：\~/channels/stop

2.執行main.py即可開始下載，windows用戶選1.即可

資料由嘉藥學生資訊網擷取https://stweb1.cnu.edu.tw/sc2008/Main4ST.asp?ScrX=2048&ScrY=1152&RUN=

資料擷取分兩個部分先用scraper.py把資料轉成courses.json
但轉換過程不知道為什麼我的"department"全部會變成"食品科技系食品餐飲僑生專班"，而且會有很多空的課
於是我用clean_data.py把資料courses.json轉成courses_fixed.json
後利用網頁讀取courses_fixed.json

網頁連結https://amdbs-0928.github.io/CNU_Course_Scraper/Webpage/index.html

2026.3.4版本更新增加了文字搜索功能跟大綱進度舊版檔案已標上版本日期
2026.3.8版本更新調整了二次資料處理的程式碼改善同課多教室卻分成兩個課的問題
2026.3.9版本更新修改了手機載網頁上的顯示方式使其更符合手機操作方式
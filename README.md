資料由嘉藥(學生資訊網全校開課課表查詢)擷取https://stweb1.cnu.edu.tw/sc2008/Main4ST.asp?ScrX=1536&ScrY=864&RUN=

資料擷取分兩個部分先用scraper.py把資料轉成courses.json
但轉換過程不知道為什麼我的"department"全部會變成"食品科技系食品餐飲僑生專班"，而且會有很多空的課
於是我用clean_data.py把資料courses.json轉成courses_fixed.json
後利用網頁讀取courses_fixed.json

網頁連結https://amdbs-0928.github.io/CNU_Course_Scraper/Webpage/index.html

2026.3.4版本更新增加了文字搜索功能跟大綱進度舊版檔案已標上版本日期

2026.3.8版本更新調整了二次資料處理的程式碼改善同課多教室卻分成兩個課的問題

2026.3.9版本更新修改了手機載網頁上的顯示方式使其更符合手機操作方式

2026.3.25版本整理了1~3步驟的資料夾。修改沒有戊班的問題。通識中心網頁中發展通識pdf轉換成json格式資料加到Data。目前還找不到發展通識公開資料的課程大綱，同學們我盡力了!
資料來源 https://edu.cnu.edu.tw/?.p=HEHE&.__id=P20260120113223079  
哭阿 發展通識資料幹嘛不放(學生資訊網全校開課課表查詢)，GPS登入帳號才能查發展通識課程大綱，是要增加讓我被告或被查的風險嗎?

2026.3.26版本更新修改了部分選項導致班級查不到問題。優化了2_Data_Correction步驟中部份多班開課顯示雜亂的問題，同時將相同的資料格式套用到3_Data_Supplement(pdf to json)步驟進行修改。

2026.4.14版本更新採用https://github.com/Unclecheng-li/AI_Animation 所學到的資源優化網頁視覺介面。採用項目檔案BG6.html、3D - demonstrate.html搭配Vibe Coding 
請支持原作YouTube頻道：https://youtube.com/@mumu-159.5?si=ektcMl0Fq1TUZMPy 网络小白_Uncle城 
學習影片:https://youtu.be/iiXm0Ko8yXk?si=QbY4OW6KFsXxsE3W
根據社群媒體投票將2026.4.14版本作為獨立網頁版本原網址改為2026.3.26版本

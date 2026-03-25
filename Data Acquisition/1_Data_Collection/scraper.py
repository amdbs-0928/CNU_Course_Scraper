from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json
import re

def run(playwright):
    # slow_mo 設為 300 讓動作有間隔，防止太快被判定為機器人
    browser = playwright.chromium.launch(headless=False, slow_mo=300)
    context = browser.new_context()
    page = context.new_page()

    print("🌐 正在前往嘉藥系統首頁...")
    page.goto("https://stweb1.cnu.edu.tw/sc2008/Main4ST.asp?ScrX=1536&ScrY=864&RUN=")
    page.wait_for_load_state("networkidle")

    time.sleep(3)
    
    clicked = False
    for f in page.frames:
        target_link = f.locator("a:has-text('全校開課課表查詢')")
        if target_link.count() > 0:
            target_link.first.evaluate("node => node.click()")
            clicked = True
            break

    if clicked:
        print("⏳ 等待系統載入...")
        time.sleep(5) 
        
        menu_frame = None
        for f in page.frames:
            if "TOPNEW" in f.name.upper() or "NEWS" in f.url.upper():
                continue 
            if f.locator("text=日間部").count() > 0:
                menu_frame = f
                break

        if menu_frame:
            print("\n--- 🚀 開始鑽探樹狀目錄 ---")
            try:
                # 確保只進入 日間部 -> 大學部．四年制
                menu_frame.locator("a:has-text('日間部')").first.evaluate("node => node.click()")
                time.sleep(1.5)
                menu_frame.locator("a:has-text('大學部．四年制')").first.evaluate("node => node.click()")
                time.sleep(2)

                # 抓出「大學部．四年制」下的所有科系 (利用包含 "系" 或 "學程" 字眼判斷)
                all_links_text = menu_frame.locator("a").all_inner_texts()
                departments = [text.strip() for text in all_links_text if "系" in text or "學程" in text]
                departments = [d for d in departments if len(d) >= 3] # 過濾不小心抓到的雜訊
                
                print(f"🎯 在「大學部．四年制」共找到 {len(departments)} 個科系")
                
                all_courses_data = []
                visited_classes = set() 
                
                for dept in departments:
                    print(f"\n📁 準備展開科系：{dept}")
                    dept_link = menu_frame.locator(f"a:text-is('{dept}')")
                    if dept_link.count() > 0:
                        dept_link.first.evaluate("node => node.click()")
                        time.sleep(2.5) 
                    else:
                        continue

                    # 抓出該科系下所有的班級
                    current_links = menu_frame.locator("a").all_inner_texts()
                    class_pattern = re.compile(r".*[一二三四五][甲乙丙丁A-Z].*") # 班級命名特徵 (一甲, 二乙等)
                    
                    target_classes = [text.strip() for text in current_links if class_pattern.match(text.strip())]
                    target_classes = list(dict.fromkeys(target_classes))
                    target_classes = [c for c in target_classes if c not in visited_classes]
                    
                    print(f"  => 找到班級：{target_classes}")
                    
                    for class_name in target_classes:
                        print(f"\n     📥 正在擷取班級資料：{class_name}")
                        class_link = menu_frame.locator(f"a:text-is('{class_name}')")
                        
                        if class_link.count() > 0:
                            class_link.first.evaluate("node => node.click()")
                            visited_classes.add(class_name)
                            time.sleep(3.5) # 給予表格載入時間
                            
                            data_frame = None
                            for f in page.frames:
                                if f.get_by_text("科目名稱").count() > 0:
                                    data_frame = f
                                    break
                                    
                            if data_frame:
                                html_content = data_frame.content()
                                soup = BeautifulSoup(html_content, "html.parser")
                                rows = soup.find_all("tr")
                                
                                # 解析該班級課表
                                for row in rows:
                                    cols = row.find_all("td")
                                    if len(cols) >= 15:
                                        texts = [col.get_text(strip=True, separator="|") for col in cols]
                                        if "科目名稱" in texts[1]: continue
                                        
                                        grade = class_name[2] if len(class_name) >= 3 else ""
                                        class_section = class_name[3] if len(class_name) >= 4 else ""
                                        raw_subject_parts = texts[1].split("|")
                                        subject_name = " ".join(raw_subject_parts[2:]) if len(raw_subject_parts) > 2 else texts[1].replace("|", " ")
                                        raw_type_parts = texts[2].split("|")
                                        selection_type = raw_type_parts[0] if len(raw_type_parts) > 0 else ""
                                        course_category = raw_type_parts[1] if len(raw_type_parts) > 1 else ""
                                        credits = texts[3].replace("|", "").strip()
                                        hours = texts[4].replace("|", "").strip()
                                        
                                        raw_teacher_parts = texts[5].split("|")
                                        if len(raw_teacher_parts) > 1:
                                            teacher = raw_teacher_parts[-1]
                                            target_classes_str = "".join(raw_teacher_parts[:-1])
                                        else:
                                            teacher = texts[5].replace("|", "")
                                            target_classes_str = ""
                                            
                                        classroom = texts[6].replace("|", "").strip()
                                        
                                        schedule_list = []
                                        days = [1, 2, 3, 4, 5, 6, 7]
                                        for i in range(7):
                                            time_slot = texts[8 + i].replace("|", "").strip()
                                            if time_slot:
                                                schedule_list.append({"day": days[i], "period": time_slot})
                                                
                                        # 🟢 強效版：破解隱藏在圖片按鈕裡的 OpenKey
                                        syllabus_url = ""
                                        row_html = str(row)
                                        
                                        # 策略 1：直接找整列 HTML 有沒有明寫 OpenKey=數字 (忽略大小寫)
                                        match1 = re.search(r'(?i)OpenKey=(\d+)', row_html)
                                        
                                        if match1:
                                            open_key = match1.group(1)
                                            syllabus_url = f"https://stweb4.cnu.edu.tw/SC2008/STPJ/STPJ_A_PGDATA.ASP?OpenKey={open_key}"
                                        else:
                                            # 策略 2：如果學校把它藏在 onClick 事件裡 (例如 onclick="javascript:pop('203625')")
                                            # 掃描該列所有的 <a> 或 <img> 標籤
                                            for tag in row.find_all(['a', 'img', 'input']):
                                                tag_str = str(tag)
                                                # 尋找 onclick 裡面帶有 5~7 位數字的參數 (通常這就是 OpenKey)
                                                match2 = re.search(r'(?i)(?:onclick|href)=.*?[\'"](\d{5,7})[\'"]', tag_str)
                                                if match2:
                                                    open_key = match2.group(1)
                                                    syllabus_url = f"https://stweb4.cnu.edu.tw/SC2008/STPJ/STPJ_A_PGDATA.ASP?OpenKey={open_key}"
                                                    break # 找到就立刻跳出迴圈

                                        # --- 組裝成完美的 JSON 字典 ---
                                        course_dict = {
                                            "department": dept, # (或原本的 department)
                                            "grade": grade,
                                            "class": class_section,
                                            "subject_name": subject_name,
                                            "required_or_elective": selection_type,
                                            "course_category": course_category,
                                            "credits": credits,
                                            "hours": hours,
                                            "target_classes": target_classes_str,
                                            "classroom": classroom,
                                            "teacher": teacher,
                                            "schedule": schedule_list,
                                            "syllabus_url": syllabus_url  # 🟢 成功抓到的網址會寫入這裡
                                        }
                                        all_courses_data.append(course_dict)
                                
                                # 🟢 關鍵變更：每讀完並解析完一個班，就寫入一次檔案
                                print(f"     💾 正在存檔中... (目前累計 {len(all_courses_data)} 筆資料)")
                                with open("courses.json", "w", encoding="utf-8") as f:
                                    json.dump(all_courses_data, f, ensure_ascii=False, indent=4)

                            else:
                                print(f"     ❌ 找不到包含 {class_name} 課表資料的 Frame。")
                        else:
                            print(f"     ❌ 找不到班級：{class_name} 的超連結")
                        
                        time.sleep(2) # 班級與班級之間留緩衝

            except Exception as e:
                print("❌ 目錄操作失敗：", e)
        else:
            print("❌ 找不到左側選單 Frame。")
    else:
        print("❌ 找不到首頁連結。")

    time.sleep(3) 
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
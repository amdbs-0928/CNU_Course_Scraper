from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json

def run(playwright):
    browser = playwright.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()
    page = context.new_page()

    print("正在前往嘉藥系統首頁...")
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
            print("\n--- 開始鑽探樹狀目錄 ---")
            try:
                menu_frame.locator("a:has-text('日間部')").first.evaluate("node => node.click()")
                time.sleep(1.5)
                menu_frame.locator("a:has-text('大學部．四年制')").first.evaluate("node => node.click()")
                time.sleep(1.5)
                menu_frame.locator("a:has-text('資訊管理系')").first.evaluate("node => node.click()")
                time.sleep(1.5)

                target_classes = ["資管一甲", "資管二甲"]
                print(f"4. 準備依序查詢班級：{target_classes}")
                
                all_courses_data = []
                
                for class_name in target_classes:
                    print(f"\n=> 正在尋找並點擊班級：{class_name}")
                    target_class_link = menu_frame.locator(f"a:has-text('{class_name}')")
                    
                    if target_class_link.count() > 0:
                        target_class_link.last.evaluate("node => node.click()")
                        time.sleep(4) 
                        
                        data_frame = None
                        for f in page.frames:
                            if f.get_by_text("科目名稱").count() > 0:
                                data_frame = f
                                break
                                
                        if data_frame:
                            print(f"✅ 成功獲取 {class_name} 資料，開始精細拆解欄位...")
                            html_content = data_frame.content()
                            soup = BeautifulSoup(html_content, "html.parser")
                            rows = soup.find_all("tr")
                            
                            for row in rows:
                                cols = row.find_all("td")
                                if len(cols) >= 15:
                                    # 關鍵技巧：用 "|" 把 HTML 裡的換行 <br> 隔開，方便後續 split 切割
                                    texts = [col.get_text(strip=True, separator="|") for col in cols]
                                    
                                    if "科目名稱" in texts[1]:
                                        continue
                                    
                                    # --- 1. 科系、年級、班級 (從 "資管一甲" 拆解) ---
                                    department = "資訊管理系"
                                    grade = class_name[2] if len(class_name) >= 3 else "" # 取出 "一"
                                    class_section = class_name[3] if len(class_name) >= 4 else "" # 取出 "甲"

                                    # --- 2. 科目名稱 ---
                                    # texts[1] 格式: "日間部|4021104|大學英文(二)|College English(Ⅱ)"
                                    raw_subject_parts = texts[1].split("|")
                                    subject_name = " ".join(raw_subject_parts[2:]) if len(raw_subject_parts) > 2 else texts[1].replace("|", " ")

                                    # --- 3. 選課別、課程種類 ---
                                    # texts[2] 格式: "必修|通識課程"
                                    raw_type_parts = texts[2].split("|")
                                    selection_type = raw_type_parts[0] if len(raw_type_parts) > 0 else ""
                                    course_category = raw_type_parts[1] if len(raw_type_parts) > 1 else ""

                                    # --- 4. 學分數、時數 ---
                                    credits = texts[3].replace("|", "").strip()
                                    hours = texts[4].replace("|", "").strip() # 新增時數欄位

                                    # --- 5. 開課班級、授課老師 ---
                                    # texts[5] 格式: "食藥檢測一甲.粧品一甲.|邱顯懿"
                                    raw_teacher_parts = texts[5].split("|")
                                    if len(raw_teacher_parts) > 1:
                                        teacher = raw_teacher_parts[-1] # 最後一個通常是老師
                                        target_classes_str = "".join(raw_teacher_parts[:-1]) # 前面全是班級
                                    else:
                                        teacher = texts[5].replace("|", "")
                                        target_classes_str = ""

                                    # --- 6. 授課教室 ---
                                    classroom = texts[6].replace("|", "").strip()

                                    # --- 7. 星期幾 + 第幾節課 ---
                                    schedule_list = []
                                    days = [1, 2, 3, 4, 5, 6, 7]
                                    for i in range(7):
                                        time_slot = texts[8 + i].replace("|", "").strip()
                                        if time_slot:
                                            schedule_list.append({
                                                "day": days[i],
                                                "period": time_slot
                                            })
                                            
                                    # --- 組裝成完美的 JSON 字典 ---
                                    course_dict = {
                                        "department": department,
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
                                        "schedule": schedule_list
                                    }
                                    
                                    all_courses_data.append(course_dict)

                        else:
                            print(f"❌ 找不到包含課表資料的 Frame。")
                    else:
                        print(f"❌ 找不到班級：{class_name} 的超連結")
                    
                    time.sleep(2) 

                # 輸出 JSON 檔案
                print("\n💾 正在將精細拆解的資料寫入 courses.json...")
                with open("courses.json", "w", encoding="utf-8") as f:
                    json.dump(all_courses_data, f, ensure_ascii=False, indent=4)
                
                print("🎉 完美！資料已成功導出。")

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
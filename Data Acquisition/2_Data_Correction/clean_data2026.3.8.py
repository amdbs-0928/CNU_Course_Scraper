import json
import re

def clean_and_expand_courses():
    # 1. 讀取爬蟲抓下來的原始檔案
    try:
        with open('courses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ 找不到 courses.json 檔案！請確認爬蟲是否執行成功。")
        return

    cleaned_courses = []
    
    # 輔助：將中文年級轉為數字
    grade_map = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5"}
    
    # 正規表達式：精準匹配「科系(非一~五) + 年級(一~五) + 班級(甲乙丙...)」
    class_pattern = re.compile(r"^([^一二三四五]+)([一二三四五])(.*)$")

    for course in data:
        # 🎯 任務一：刪除沒有授課教師的無效空資料
        if not course.get("teacher") or str(course["teacher"]).strip() == "":
            continue
            
        target_classes_str = course.get("target_classes", "")
        
        # 如果沒有 target_classes (可能是全校共同選修)，直接保留原資料
        if not target_classes_str:
            cleaned_courses.append(course)
            continue

        # 🎯 任務二：處理 target_classes 複數班級的情況
        class_list = [c.strip() for c in target_classes_str.split(".") if c.strip()]
        
        for cls in class_list:
            new_course = course.copy() 
            
            match = class_pattern.match(cls)
            if match:
                new_course["department"] = match.group(1).strip()
                new_course["grade"] = grade_map.get(match.group(2), match.group(2))
                new_course["class"] = match.group(3).strip()
            else:
                new_course["class"] = cls 
            
            cleaned_courses.append(new_course)

    # 🎯 任務三：智慧合併重複課程與多間教室
    unique_courses_map = {}

    for c in cleaned_courses:
        # 將 schedule 轉成 tuple 形式，這樣才能作為字典的 Key 進行比較
        schedule_tuple = tuple((s.get('day'), s.get('period')) for s in c.get('schedule', []))
        
        # 建立「課程專屬身分證」，注意：這裡「不包含」classroom 欄位！
        course_identity_key = (
            c.get('department', ''),
            c.get('grade', ''),
            c.get('class', ''),
            c.get('subject_name', ''),
            c.get('teacher', ''),
            schedule_tuple,
            c.get('syllabus_url', '')
        )
        
        if course_identity_key in unique_courses_map:
            # 💡 發現是同一堂課！檢查教室是不是不一樣
            existing_classrooms = unique_courses_map[course_identity_key]['classroom'].split(',')
            existing_classrooms = [cr.strip() for cr in existing_classrooms if cr.strip()]
            
            new_classroom = c.get('classroom', '').strip()
            
            # 如果這間教室還沒被記錄過，就把它加進去
            if new_classroom and new_classroom not in existing_classrooms:
                existing_classrooms.append(new_classroom)
                # 重新組合教室字串，例如將 "C320" 變成 "C320, U103"
                unique_courses_map[course_identity_key]['classroom'] = ", ".join(existing_classrooms)
        else:
            # 第一次遇到這堂課，把整筆資料存入字典
            unique_courses_map[course_identity_key] = c.copy()

    # 將字典的值轉換回我們需要的陣列格式
    final_courses = list(unique_courses_map.values())

    # 4. 寫入全新的乾淨檔案
    with open("courses_fixed.json", "w", encoding="utf-8") as f:
        json.dump(final_courses, f, ensure_ascii=False, indent=4)

    print(f"✅ 資料清理與優化完成！")
    print(f"   📉 原始資料總筆數: {len(data)}")
    print(f"   📈 清理、展開並【合併多教室】後，有效資料共: {len(final_courses)} 筆")
    print(f"   💾 檔案已儲存為：courses_fixed.json")

if __name__ == "__main__":
    clean_and_expand_courses()
    
#2026/03/08 編寫

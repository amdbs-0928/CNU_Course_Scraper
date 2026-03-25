import json
import re

def clean_and_expand_courses():
    # 1. 讀取有問題的原始檔案 (請確認檔名是否為 courses.json)
    try:
        with open('courses.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ 找不到 courses.json 檔案！")
        return

    cleaned_courses = []
    
    # 輔助：將中文年級轉為數字，方便前端篩選 (例如 "一" 轉為 "1")
    grade_map = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5"}
    
    # 正規表達式：從「藥學一甲」中精準拆出「科系(藥學)」、「年級(一)」、「班級(甲)」
    class_pattern = re.compile(r"^([^一二三四五]+)([一二三四五])(.*)$")

    for course in data:
        # 🎯 任務三：把沒有教師名稱的部分空資料刪掉
        # 如果 teacher 是空的，或者只包含空白，直接跳過不處理
        if not course.get("teacher") or course["teacher"].strip() == "":
            continue
            
        target_classes_str = course.get("target_classes", "")
        if not target_classes_str:
            continue

        # 🎯 任務二：處理 target_classes 複數班級的情況
        # 將 "藥學一甲.藥學一乙." 用 "." 拆解成陣列 ["藥學一甲", "藥學一乙"]
        class_list = [c.strip() for c in target_classes_str.split(".") if c.strip()]
        
        # 將這堂課依據班級展開！
        for cls in class_list:
            match = class_pattern.match(cls)
            if match:
                dept_short = match.group(1)    # 抓出 "藥學"
                grade_zh = match.group(2)      # 抓出 "一"
                class_section = match.group(3) # 抓出 "甲"
                
                # 建立一筆全新的獨立課程資料，避免參考到同一個物件
                new_course = course.copy()
                
                # 🎯 任務一：將 department 替換為我們從 target_classes 拆出來的正確科系
                new_course["department"] = dept_short
                new_course["grade"] = grade_map.get(grade_zh, grade_zh)
                new_course["class"] = class_section
                
                cleaned_courses.append(new_course)

    # 去除重複：為了避免學校系統裡原本就有重複的資料，使用 set 幫我們去除完全一模一樣的課程物件
    unique_courses = []
    seen = set()
    for c in cleaned_courses:
        # 將字典轉成字串當作判斷是否重複的 key
        c_str = json.dumps(c, sort_keys=True)
        if c_str not in seen:
            seen.add(c_str)
            unique_courses.append(c)

    # 4. 寫入全新的乾淨檔案
    with open("courses_fixed.json", "w", encoding="utf-8") as f:
        json.dump(unique_courses, f, ensure_ascii=False, indent=4)

    print(f"✅ 清理完成！")
    print(f"   📉 包含空值的原始總筆數: {len(data)}")
    print(f"   📈 清理空資料並展開複數班級後，完美的有效資料共: {len(unique_courses)} 筆")
    print(f"   💾 檔案已儲存為：courses_fixed.json")

if __name__ == "__main__":
    clean_and_expand_courses()
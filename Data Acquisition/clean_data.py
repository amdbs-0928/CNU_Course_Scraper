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
        
        # 🎯 優化點：如果沒有 target_classes (可能是全校共同選修)，直接保留原資料
        if not target_classes_str:
            cleaned_courses.append(course)
            continue

        # 🎯 任務二：處理 target_classes 複數班級的情況
        class_list = [c.strip() for c in target_classes_str.split(".") if c.strip()]
        
        for cls in class_list:
            # 💡 這裡的 copy() 非常關鍵！它會把你的 syllabus_url 原封不動地複製過來
            new_course = course.copy() 
            
            match = class_pattern.match(cls)
            if match:
                # 成功拆解出 科系、年級、班級
                new_course["department"] = match.group(1).strip()
                new_course["grade"] = grade_map.get(match.group(2), match.group(2))
                new_course["class"] = match.group(3).strip()
            else:
                # 🎯 優化點：如果格式太怪異導致拆解失敗，我們依然保留它，不讓資料遺失
                new_course["class"] = cls 
            
            cleaned_courses.append(new_course)

    # 🎯 任務三：去除完全重複的課程資料
    unique_courses = []
    seen = set()
    for c in cleaned_courses:
        c_str = json.dumps(c, sort_keys=True)
        if c_str not in seen:
            seen.add(c_str)
            unique_courses.append(c)

    # 4. 寫入全新的乾淨檔案
    with open("courses_fixed.json", "w", encoding="utf-8") as f:
        json.dump(unique_courses, f, ensure_ascii=False, indent=4)

    print(f"✅ 資料清理與優化完成！")
    print(f"   📉 原始資料總筆數: {len(data)}")
    print(f"   📈 清理空資料並展開複數班級後，有效資料共: {len(unique_courses)} 筆")
    print(f"   💡 (課程大綱網址 syllabus_url 已自動繼承保留)")
    print(f"   💾 檔案已儲存為：courses_fixed.json")

if __name__ == "__main__":
    clean_and_expand_courses()
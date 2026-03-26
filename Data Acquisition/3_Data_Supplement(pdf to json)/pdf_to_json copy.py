import json
import re
import pdfplumber
import glob
import os

# 設定檔案路徑
json_file_path = 'courses_fixed.json'
output_json_path = 'courses_updated.json'

def build_class_map(courses_data):
    """
    從現有的 JSON 資料中，建立「系所」與「年級」對應的「班級」清單。
    回傳格式範例: {'藥學': {'1': {'甲', '乙', '丙', ...}}, '多媒體': {'3': {'甲'}}}
    """
    dept_class_map = {}
    for course in courses_data:
        dept = course.get('department', '').strip()
        grade = course.get('grade', '').strip()
        cls = course.get('class', '').strip()
        
        if dept and grade:
            if dept not in dept_class_map:
                dept_class_map[dept] = {}
            if grade not in dept_class_map[dept]:
                dept_class_map[dept][grade] = set()
            # 🟢 修正：忽略空值與我們標記的 "不分班"，只收集真正的甲乙丙丁
            if cls and cls != "不分班":
                dept_class_map[dept][grade].add(cls)
                
    return dept_class_map

def parse_header_departments(pdf_path):
    """
    讀取 PDF 第一頁的表頭，解析出適用的「系所」與「年級」。
    """
    target_depts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return target_depts
            text = pdf.pages[0].extract_text()
            if not text:
                return target_depts
                
            for line in text.split('\n'):
                # 尋找 "一年級:高福"、"二年級:藥學、社工..." 這種格式
                match = re.search(r'(一|二|三|四|五)年級[:：]\s*(.*)', line)
                if match:
                    g_char = match.group(1)
                    g_num = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5"}.get(g_char, "1")
                    depts_str = match.group(2)
                    
                    # 依據 "、" 分割系所名稱
                    depts = [d.strip() for d in depts_str.split('、') if d.strip()]
                    for d in depts:
                        # 移除括號內的文字，例如將 "粧品(二技一)" 轉為 "粧品"
                        actual_dept = re.sub(r'\(.*?\)', '', d).strip()
                        if actual_dept:
                            target_depts.append({"dept": actual_dept, "grade": g_num})
    except Exception as e:
        print(f"解析 {pdf_path} 表頭時發生錯誤: {e}")
        
    return target_depts

def parse_schedule_text(text):
    """解析星期與節次"""
    day_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}
    num_map = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10", "十一": "11", "十二": "12"}
    
    day_match = re.search(r'星期([一二三四五六日])', text)
    day = day_map.get(day_match.group(1)) if day_match else None
    
    period_match = re.search(r'第(.+)節', text)
    period = ""
    if period_match:
        raw_periods = period_match.group(1).split('、')
        periods = [num_map.get(p, p) for p in raw_periods]
        if len(periods) > 1:
            period = f"{periods[0]}-{periods[-1]}"
        elif len(periods) == 1:
            period = periods[0]

    if day and period:
        return {"day": day, "period": period}
    return None

def main():
    # 1. 讀取現有的 JSON 檔案 (從清理過的 courses_fixed.json 讀取)
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            courses_data = json.load(f)
    except FileNotFoundError:
        print(f"找不到 {json_file_path}，將建立空陣列。")
        courses_data = []

    # 2. 建立系所班級對應表
    dept_class_map = build_class_map(courses_data)
    new_courses = []

    # 3. 自動尋找目錄下所有的 PDF 開課表
    pdf_files = glob.glob("課程開課表*.pdf")
    if not pdf_files:
        print("當前目錄下找不到任何 '課程開課表*.pdf' 檔案。")
        return

    grade_zh_map = {"1": "一", "2": "二", "3": "三", "4": "四", "5": "五"}

    for pdf_path in pdf_files:
        print(f"\n開始處理檔案: {pdf_path}")
        
        target_depts = parse_header_departments(pdf_path)
        if not target_depts:
            print(f"無法從 {pdf_path} 抓取到適用的系所表頭，跳過此檔。")
            continue
            
        current_schedule = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text: continue
                
                lines = text.split('\n')
                for line in lines:
                    if "星期" in line and "節" in line:
                        parsed_time = parse_schedule_text(line)
                        if parsed_time:
                            current_schedule = [parsed_time]
                        continue
                    
                    match = re.match(r'^(X\d{6})\s+(\S+)\s+(\S+)\s+(\S+)', line.replace('"', '').replace(',', ' '))
                    if match:
                        domain = match.group(2)       
                        subject_name = match.group(3) 
                        teacher = match.group(4)      
                        
                        # 4. 針對表頭抓取到的每一個系所，展開獨立的課程資料
                        for target in target_depts:
                            dept_name = target['dept']
                            grade_num = target['grade']
                            grade_zh = grade_zh_map.get(grade_num, grade_num)
                            
                            classes = dept_class_map.get(dept_name, {}).get(grade_num, set())
                            
                            # 🟢 核心修改：如果有分班，就為每一個班級建立一筆獨立資料
                            if classes:
                                for c in sorted(list(classes)):
                                    target_class_str = f"{dept_name}{grade_zh}{c}."
                                    new_course = {
                                        "department": dept_name,
                                        "grade": grade_num,
                                        "class": c,  # 填入具體班級 (甲、乙...)
                                        "subject_name": subject_name,
                                        "required_or_elective": "發展通識", 
                                        "course_category": domain,
                                        "credits": "2",
                                        "hours": "2",
                                        "target_classes": target_class_str,
                                        "classroom": "",
                                        "teacher": teacher,
                                        "schedule": current_schedule.copy() if current_schedule else [],
                                        "syllabus_url": ""
                                    }
                                    new_courses.append(new_course)
                            
                            # 🟢 核心修改：如果該年級沒有分班，就標記為 "不分班"
                            else:
                                target_class_str = f"{dept_name}{grade_zh}."
                                new_course = {
                                        "department": dept_name,
                                        "grade": grade_num,
                                        "class": "不分班", # 填入不分班
                                        "subject_name": subject_name,
                                        "required_or_elective": "發展通識", 
                                        "course_category": domain,
                                        "credits": "2",
                                        "hours": "2",
                                        "target_classes": target_class_str,
                                        "classroom": "",
                                        "teacher": teacher,
                                        "schedule": current_schedule.copy() if current_schedule else [],
                                        "syllabus_url": ""
                                }
                                new_courses.append(new_course)

    # 5. 合併與寫入 JSON 檔案
    courses_data.extend(new_courses)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(courses_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n執行完成！共擴展新增了 {len(new_courses)} 筆課程記錄，已儲存至 {output_json_path}")

if __name__ == "__main__":
    main()

#2026/03/26 編寫
# 读取岗位JD
with open("jobs/sample_jd.txt", "r", encoding="utf-8") as f:
    jd = f.read()

# 读取主简历
with open("resumes/master_resume.txt", "r", encoding="utf-8") as f:
    resume = f.read()

print("===== Resume Matcher 启动 =====")
print(f"JD读取成功，共 {len(jd)} 个字符")
print(f"主简历读取成功，共 {len(resume)} 个字符")

# CareerOS当前支持识别的关键词
keyword_library = [
    "Python",
    "SQL",
    "Power BI",
    "Excel",
    "数据分析",
    "商业分析",
    "经营分析",
    "金融",
    "财务分析",
    "财务建模",
    "年度预算",
    "滚动预测",
    "成本分析",
    "行业研究",
    "DCF",
    "战略分析",
    "战略咨询",
    "机器学习",
    "Tableau",
    "英语"
]

# 同义词与相关表达
synonym_library = {
    "数据分析": [
        "数据分析",
        "数据清洗",
        "数据处理",
        "数据可视化",
        "经营分析",
        "商业分析"
    ],
    "成本分析": [
        "成本分析",
        "成本差异分析",
        "BOM成本分析",
        "成本控制"
    ],
    "财务建模": [
        "财务建模",
        "DCF",
        "估值模型",
        "盈利预测",
        "现金流折现"
    ],
    "战略分析": [
        "战略分析",
        "战略咨询",
        "情景分析",
        "决策分析",
        "敏感性分析"
    ],
    "英语": [
        "英语",
        "CET-6",
        "英文",
        "中英文"
    ]
}
# 第一步：找出JD中真正要求的关键词
required_keywords = []

for keyword in keyword_library:
    if keyword.lower() in jd.lower():
        required_keywords.append(keyword)

print("\n===== JD要求的关键词 =====")

for keyword in required_keywords:
    print("📌", keyword)

# 第二步：检查简历是否具备这些关键词
matched_keywords = []
missing_keywords = []

for keyword in required_keywords:
    resume_lower = resume.lower()

    # 默认先检查关键词本身
    is_matched = keyword.lower() in resume_lower

    # 如果关键词本身没有匹配，再检查同义词
    if not is_matched and keyword in synonym_library:
        for synonym in synonym_library[keyword]:
            if synonym.lower() in resume_lower:
                is_matched = True
                break

    # 根据检查结果进行分类
    if is_matched:
        matched_keywords.append(keyword)
    else:
        missing_keywords.append(keyword)

print("\n===== 简历已匹配 =====")

for keyword in matched_keywords:
    print("✅", keyword)

print("\n===== 简历暂未匹配 =====")

if len(missing_keywords) == 0:
    print("无")
else:
    for keyword in missing_keywords:
        print("❌", keyword)

# 第三步：计算匹配率
if len(required_keywords) > 0:
    score = len(matched_keywords) / len(required_keywords) * 100
else:
    score = 0

print("\n===== Resume Matcher 报告 =====")
print(f"JD要求关键词：{len(required_keywords)} 个")
print(f"简历匹配关键词：{len(matched_keywords)} 个")
print(f"简历缺失关键词：{len(missing_keywords)} 个")
print(f"关键词匹配率：{score:.1f}%")

if score >= 80:
    print("投递建议：推荐投递 ✅")
elif score >= 60:
    print("投递建议：修改简历后投递 ⚠️")
else:
    print("投递建议：匹配度较低，谨慎投递 ❌")
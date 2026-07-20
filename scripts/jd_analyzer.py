with open("jobs/sample_jd.txt", "r", encoding="utf-8") as f:
    jd = f.read()

with open("resumes/master_resume.txt", "r", encoding="utf-8") as f:
    resume = f.read()
print("===== 简历内容 =====")
print(resume)
print("===== JD内容 =====")
print(jd)

keywords = [
    "Python",
    "SQL",
    "Power BI",
    "Excel",
    "数据分析",
    "金融"
]

print("\n===== 识别关键词 =====")

matched = 0

for keyword in keywords:
    if keyword in resume:
        print("✅", keyword)
        matched += 1
    else:
        print("❌", keyword)

print("\n===== 关键词识别完成 =====")
print(f"匹配到 {matched} 个关键词")

score = matched / len(keywords) * 100
print(f"匹配率：{score:.1f}%")
if score >= 80:
    print("建议：推荐投递 ✅")
else:
    print("建议：暂缓投递 ⚠️")

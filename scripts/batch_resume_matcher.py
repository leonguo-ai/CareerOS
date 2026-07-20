import csv
from pathlib import Path

JOB_POOL_PATH = "data/job_pool.csv"
MASTER_RESUME_PATH = "resumes/master_resume.txt"
JOBS_DIRECTORY = Path("jobs")

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

jd_alias_library = {
    "英语": ["英语", "英文", "English"],
    "数据分析": ["数据分析", "数据处理", "数据清洗"],
    "财务分析": ["财务分析", "财务测算"],
    "成本分析": ["成本分析", "成本控制", "成本差异"],
    "战略分析": ["战略分析", "战略研究", "战略规划"]
}

resume_alias_library = {
    "英语": ["英语", "英文", "CET-6", "中英文"],
    "数据分析": [
        "数据分析",
        "数据处理",
        "数据清洗",
        "数据可视化",
        "商业分析",
        "经营分析"
    ],
    "财务分析": [
        "财务分析",
        "财务测算",
        "DCF",
        "盈利预测"
    ],
    "成本分析": [
        "成本分析",
        "成本控制",
        "成本差异分析",
        "BOM成本分析"
    ],
    "战略分析": [
        "战略分析",
        "战略咨询",
        "情景分析",
        "决策分析",
        "敏感性分析"
    ]
}

# 读取完整主简历
with open(MASTER_RESUME_PATH, "r", encoding="utf-8") as f:
    resume = f.read()

resume_lower = resume.lower()

# 读取岗位池
jobs = []

with open(JOB_POOL_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        jobs.append(row)

print("===== CareerOS Batch Resume Matcher V1 =====")

results = []

for job in jobs:
    if job["status"].strip().lower() != "open":
        continue

    jd_path = JOBS_DIRECTORY / f'{job["job_id"]}.txt'

    if not jd_path.exists():
        print(f'跳过：{job["job_id"]} 没有对应JD文件')
        continue

    jd = jd_path.read_text(encoding="utf-8")
    jd_lower = jd.lower()

    required_keywords = []

    for keyword in keyword_library:
        aliases = jd_alias_library.get(keyword, [keyword])

        if any(alias.lower() in jd_lower for alias in aliases):
            required_keywords.append(keyword)

    matched_keywords = []
    missing_keywords = []

    for keyword in required_keywords:
        aliases = resume_alias_library.get(keyword, [keyword])

        if any(alias.lower() in resume_lower for alias in aliases):
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    if required_keywords:
        match_score = (
            len(matched_keywords) / len(required_keywords) * 100
        )
    else:
        match_score = 0

    results.append(
        {
            "job_id": job["job_id"],
            "company": job["company"],
            "job_title": job["job_title"],
            "location": job["location"],
            "match_score": match_score,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords
        }
    )

# 按简历匹配率从高到低排序
results.sort(
    key=lambda item: item["match_score"],
    reverse=True
)

print(f"成功分析岗位：{len(results)}")
print("\n===== 批量简历匹配结果 =====")

for rank, result in enumerate(results, start=1):
    print(
        f'{rank}. {result["company"]} | '
        f'{result["job_title"]} | '
        f'{result["location"]} | '
        f'简历匹配率：{result["match_score"]:.1f}%'
    )

    print(
        "   已匹配："
        + (
            "、".join(result["matched_keywords"])
            if result["matched_keywords"]
            else "无"
        )
    )

    print(
        "   暂缺："
        + (
            "、".join(result["missing_keywords"])
            if result["missing_keywords"]
            else "无"
        )
    )
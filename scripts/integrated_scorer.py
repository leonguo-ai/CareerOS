import csv
import json
from datetime import date
from pathlib import Path

JOB_POOL_PATH = "data/job_pool.csv"
PREFERENCES_PATH = "data/candidate_preferences.json"
MASTER_RESUME_PATH = "resumes/master_resume.txt"
JOBS_DIRECTORY = Path("jobs")
OUTPUT_PATH = "data/integrated_shortlist.csv"

# 评分权重
PREFERENCE_WEIGHT = 0.40
RESUME_MATCH_WEIGHT = 0.60


# CareerOS支持识别的岗位关键词
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


# JD中可能出现的相关表达
jd_alias_library = {
    "英语": ["英语", "英文", "English"],
    "数据分析": ["数据分析", "数据处理", "数据清洗"],
    "财务分析": ["财务分析", "财务测算"],
    "成本分析": ["成本分析", "成本控制", "成本差异"],
    "战略分析": ["战略分析", "战略研究", "战略规划"]
}


# 主简历中可以作为能力证据的相关表达
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


# 读取求职偏好
with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
    preferences = json.load(f)


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


# 岗位去重
unique_jobs = []
seen_urls = set()
seen_job_keys = set()

for job in jobs:
    source_url = job["source_url"].strip().lower()

    job_key = (
        job["company"].strip().lower(),
        job["job_title"].strip().lower(),
        job["location"].strip().lower()
    )

    if source_url in seen_urls or job_key in seen_job_keys:
        continue

    seen_urls.add(source_url)
    seen_job_keys.add(job_key)
    unique_jobs.append(job)


# 分析开放岗位
scored_jobs = []

for job in unique_jobs:
    if job["status"].strip().lower() != "open":
        continue

    preference_score = 0
    preference_reasons = []

    job_title = job["job_title"]
    location = job["location"]
    job_type = job["job_type"]

    # 计算岗位方向偏好分
    for keyword, points in preferences["target_job_keywords"].items():
        if keyword.lower() in job_title.lower():
            preference_score += points
            preference_reasons.append(
                f"目标岗位：{keyword} +{points}"
            )

    # 计算城市偏好分
    if location in preferences["preferred_locations"]:
        points = preferences["preferred_locations"][location]
        preference_score += points
        preference_reasons.append(
            f"目标城市：{location} +{points}"
        )

    # 计算招聘类型偏好分
    if job_type in preferences["preferred_job_types"]:
        points = preferences["preferred_job_types"][job_type]
        preference_score += points
        preference_reasons.append(
            f"招聘类型：{job_type} +{points}"
        )

    # 寻找该岗位对应的完整JD
    jd_path = JOBS_DIRECTORY / f'{job["job_id"]}.txt'

    if not jd_path.exists():
        print(f'跳过：{job["job_id"]} 没有对应JD文件')
        continue

    jd = jd_path.read_text(encoding="utf-8")
    jd_lower = jd.lower()

    # 提取岗位要求的关键词
    required_keywords = []

    for keyword in keyword_library:
        aliases = jd_alias_library.get(keyword, [keyword])

        if any(alias.lower() in jd_lower for alias in aliases):
            required_keywords.append(keyword)

    # 检查简历匹配和缺失的关键词
    matched_keywords = []
    missing_keywords = []

    for keyword in required_keywords:
        aliases = resume_alias_library.get(keyword, [keyword])

        if any(alias.lower() in resume_lower for alias in aliases):
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    # 计算简历匹配率
    if required_keywords:
        resume_match_score = (
            len(matched_keywords)
            / len(required_keywords)
            * 100
        )
    else:
        resume_match_score = 0

    # 将岗位偏好分限制在100以内
    normalized_preference_score = min(preference_score, 100)

    # 计算综合评分
    final_score = (
        normalized_preference_score * PREFERENCE_WEIGHT
        + resume_match_score * RESUME_MATCH_WEIGHT
    )

    scored_jobs.append(
        {
            "job": job,
            "preference_score": normalized_preference_score,
            "resume_match_score": resume_match_score,
            "final_score": final_score,
            "required_keywords": required_keywords,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "preference_reasons": preference_reasons
        }
    )


# 按综合评分排序
scored_jobs.sort(
    key=lambda item: item["final_score"],
    reverse=True
)


# 每日最多选择20个岗位
daily_limit = preferences["daily_application_limit"]
top_jobs = scored_jobs[:daily_limit]


print("===== CareerOS Integrated Scorer V1 =====")
print(f"岗位池原始记录：{len(jobs)}")
print(f"去重后岗位：{len(unique_jobs)}")
print(f"成功综合评分岗位：{len(scored_jobs)}")
print(f"今日候选岗位：{len(top_jobs)}")

print("\n===== 综合岗位排名 =====")

for rank, item in enumerate(top_jobs, start=1):
    job = item["job"]

    print(
        f'{rank}. {job["company"]} | '
        f'{job["job_title"]} | '
        f'{job["location"]}'
    )

    print(
        f'   岗位偏好分：'
        f'{item["preference_score"]:.1f}'
    )

    print(
        f'   简历匹配率：'
        f'{item["resume_match_score"]:.1f}%'
    )

    print(
        f'   综合评分：'
        f'{item["final_score"]:.1f}'
    )

    print(
        "   已匹配："
        + (
            "、".join(item["matched_keywords"])
            if item["matched_keywords"]
            else "无"
        )
    )

    print(
        "   暂缺："
        + (
            "、".join(item["missing_keywords"])
            if item["missing_keywords"]
            else "无"
        )
    )

    print(f'   链接：{job["source_url"]}')
    print()


# 导出综合评分后的每日清单
today = date.today().isoformat()

fieldnames = [
    "rank",
    "job_id",
    "company",
    "job_title",
    "location",
    "job_type",
    "preference_score",
    "resume_match_score",
    "final_score",
    "matched_keywords",
    "missing_keywords",
    "source_url",
    "shortlist_date",
    "review_status",
    "application_status"
]

with open(
    OUTPUT_PATH,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for rank, item in enumerate(top_jobs, start=1):
        job = item["job"]

        writer.writerow(
            {
                "rank": rank,
                "job_id": job["job_id"],
                "company": job["company"],
                "job_title": job["job_title"],
                "location": job["location"],
                "job_type": job["job_type"],
                "preference_score": (
                    f'{item["preference_score"]:.1f}'
                ),
                "resume_match_score": (
                    f'{item["resume_match_score"]:.1f}'
                ),
                "final_score": f'{item["final_score"]:.1f}',
                "matched_keywords": "、".join(
                    item["matched_keywords"]
                ),
                "missing_keywords": "、".join(
                    item["missing_keywords"]
                ),
                "source_url": job["source_url"],
                "shortlist_date": today,
                "review_status": "pending",
                "application_status": "not_applied"
            }
        )

print(f"综合岗位清单已生成：{OUTPUT_PATH}")
print(f"清单岗位数量：{len(top_jobs)}")
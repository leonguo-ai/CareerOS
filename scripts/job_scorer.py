import csv
import json

from datetime import date
JOB_POOL_PATH = "data/job_pool.csv"
PREFERENCES_PATH = "data/candidate_preferences.json"

# 读取求职偏好
with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
    preferences = json.load(f)

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

# 只保留开放岗位
open_jobs = []

for job in unique_jobs:
    if job["status"].strip().lower() == "open":
        open_jobs.append(job)

# 为每个岗位打分
scored_jobs = []

for job in open_jobs:
    score = 0
    reasons = []

    job_title = job["job_title"]
    location = job["location"]
    job_type = job["job_type"]

    # 岗位方向得分
    for keyword, points in preferences["target_job_keywords"].items():
        if keyword.lower() in job_title.lower():
            score += points
            reasons.append(f"目标岗位：{keyword} +{points}")

    # 城市偏好得分
    if location in preferences["preferred_locations"]:
        points = preferences["preferred_locations"][location]
        score += points
        reasons.append(f"目标城市：{location} +{points}")

    # 招聘类型得分
    if job_type in preferences["preferred_job_types"]:
        points = preferences["preferred_job_types"][job_type]
        score += points
        reasons.append(f"招聘类型：{job_type} +{points}")

    scored_jobs.append(
        {
            "job": job,
            "score": score,
            "reasons": reasons
        }
    )

# 按得分从高到低排序
scored_jobs.sort(key=lambda item: item["score"], reverse=True)

daily_limit = preferences["daily_application_limit"]
top_jobs = scored_jobs[:daily_limit]

print("===== CareerOS Job Scorer V1 =====")
print(f"岗位池原始记录：{len(jobs)}")
print(f"去重后岗位：{len(unique_jobs)}")
print(f"当前开放岗位：{len(open_jobs)}")
print(f"今日候选岗位：{len(top_jobs)}")

print("\n===== 今日岗位排名 =====")

for rank, item in enumerate(top_jobs, start=1):
    job = item["job"]
    score = item["score"]

    print(
        f'{rank}. {job["company"]} | '
        f'{job["job_title"]} | '
        f'{job["location"]} | '
        f'评分：{score}'
    )

    if item["reasons"]:
        for reason in item["reasons"]:
            print(f"   - {reason}")
    else:
        print("   - 暂未命中求职偏好")

    print(f'   - 链接：{job["source_url"]}')

    # 输出每日待审核岗位清单
shortlist_path = "data/daily_shortlist.csv"
today = date.today().isoformat()

fieldnames = [
    "rank",
    "job_id",
    "company",
    "job_title",
    "location",
    "job_type",
    "score",
    "source_url",
    "shortlist_date",
    "review_status",
    "application_status"
]

with open(shortlist_path, "w", newline="", encoding="utf-8-sig") as f:
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
                "score": item["score"],
                "source_url": job["source_url"],
                "shortlist_date": today,
                "review_status": "pending",
                "application_status": "not_applied"
            }
        )

print(f"\n每日岗位清单已生成：{shortlist_path}")
print(f"清单岗位数量：{len(top_jobs)}")
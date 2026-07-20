import csv

job_pool_path = "data/job_pool.csv"

jobs = []

with open(job_pool_path, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        jobs.append(row)

print("===== CareerOS Job Pool V1 =====")
print(f"岗位总数：{len(jobs)}")

open_jobs = []

for job in jobs:
    if job["status"] == "open":
        open_jobs.append(job)

print(f"当前开放岗位：{len(open_jobs)}")
print(f"已经关闭岗位：{len(jobs) - len(open_jobs)}")

print("\n===== 当前开放岗位 =====")

for job in open_jobs:
    print(
        f'{job["job_id"]} | '
        f'{job["company"]} | '
        f'{job["job_title"]} | '
        f'{job["location"]}'
    )
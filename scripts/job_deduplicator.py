import csv

job_pool_path = "data/job_pool.csv"

all_jobs = []
unique_jobs = []
duplicate_jobs = []

seen_urls = set()
seen_job_keys = set()

with open(job_pool_path, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        all_jobs.append(row)

        source_url = row["source_url"].strip().lower()

        job_key = (
            row["company"].strip().lower(),
            row["job_title"].strip().lower(),
            row["location"].strip().lower()
        )

        is_duplicate_url = source_url in seen_urls
        is_duplicate_job = job_key in seen_job_keys

        if is_duplicate_url or is_duplicate_job:
            duplicate_jobs.append(row)
        else:
            unique_jobs.append(row)
            seen_urls.add(source_url)
            seen_job_keys.add(job_key)

print("===== CareerOS Job Deduplicator V1 =====")
print(f"原始岗位数量：{len(all_jobs)}")
print(f"去重后岗位数量：{len(unique_jobs)}")
print(f"发现重复岗位：{len(duplicate_jobs)}")

print("\n===== 重复岗位 =====")

if len(duplicate_jobs) == 0:
    print("无")
else:
    for job in duplicate_jobs:
        print(
            f'{job["job_id"]} | '
            f'{job["company"]} | '
            f'{job["job_title"]} | '
            f'{job["source_url"]}'
        )

print("\n===== 去重后的开放岗位 =====")

for job in unique_jobs:
    if job["status"].strip().lower() == "open":
        print(
            f'{job["job_id"]} | '
            f'{job["company"]} | '
            f'{job["job_title"]} | '
            f'{job["location"]}'
        )
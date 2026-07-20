import csv
import re
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright


INPUT_PATH = "data/bytedance_filtered_jobs.csv"
OUTPUT_PATH = "data/bytedance_verified_jobs.csv"
DETAIL_DIRECTORY = Path("data/bytedance_job_details")

DETAIL_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)

# V1最多验证5个岗位，避免请求过快
MAX_JOBS = 5

candidate_jobs = []

with open(INPUT_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["recommendation"] in [
            "priority_review",
            "manual_review"
        ]:
            candidate_jobs.append(row)

candidate_jobs.sort(
    key=lambda row: int(row["relevance_score"]),
    reverse=True
)

candidate_jobs = candidate_jobs[:MAX_JOBS]

print("===== ByteDance Job Detail Verifier V1 =====")
print(f"待验证岗位：{len(candidate_jobs)}")
print()

verified_jobs = []

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True
    )

    context = browser.new_context(
        viewport={
            "width": 1440,
            "height": 1000
        },
        locale="zh-CN"
    )

    for index, job in enumerate(candidate_jobs, start=1):
        page = context.new_page()

        source_url = job["source_url"]
        raw_title = job["raw_job_title"]

        print(f"正在验证第 {index} 个岗位")
        print(f"网址：{source_url}")

        page_status = "unverified"
        final_url = ""
        page_title = ""
        clean_job_title = ""
        detail_text = ""
        error_message = ""

        try:
            response = page.goto(
                source_url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(5000)

            final_url = page.url
            page_title = page.title().strip()

            status_code = (
                response.status
                if response is not None
                else None
            )

            if status_code is not None and status_code >= 400:
                page_status = "http_error"
                error_message = f"HTTP状态码：{status_code}"

            else:
                body = page.locator("body")

                detail_text = body.inner_text(
                    timeout=10000
                ).strip()

                page_status = "reachable" if detail_text else "empty_page"
# 从岗位列表中的原始文字提取真实岗位名称
# 从岗位列表中的原始文字提取真实岗位名称
            title_stop_patterns = [
                r"\s+(北京|上海|深圳|广州|杭州|成都|武汉|西安|南京)\s*",
                r"\s+职位\s+ID",
                r"\s+ByteIntern",
                r"\s+日常实习",
                r"\s+校招",
                r"\s+正式研发",
                r"\s+实习研发"
            ]

            clean_job_title = raw_title.strip()

            for pattern in title_stop_patterns:
                clean_job_title = re.split(
                    pattern,
                    clean_job_title,
                    maxsplit=1
                )[0].strip()

            # 防止网页导航标题被误识别为岗位名称
            invalid_titles = [
                "",
                "校招",
                "校园招聘",
                "职位",
                "字节跳动校园招聘"
            ]

            if clean_job_title in invalid_titles:
                clean_job_title = raw_title[:80].strip()

                if detail_text:
                    page_status = "reachable"
                else:
                    page_status = "empty_page"

            safe_name = re.sub(
                r'[\\/:*?"<>|]+',
                "_",
                clean_job_title or f"job_{index}"
            )

            safe_name = safe_name[:60]

            detail_path = (
                DETAIL_DIRECTORY
                / f"{index:02d}_{safe_name}.txt"
            )

            detail_path.write_text(
                detail_text,
                encoding="utf-8"
            )

            print(f"岗位名称：{clean_job_title}")
            print(f"页面状态：{page_status}")
            print(f"正文字符数：{len(detail_text)}")
            print(f"详情保存：{detail_path}")

        except Exception as error:
            page_status = "error"
            error_message = str(error)

            print("页面状态：error")
            print(f"错误：{error_message}")

        finally:
            page.close()

        verified_jobs.append(
            {
                "company": "字节跳动",
                "job_title": clean_job_title,
                "raw_job_title": raw_title,
                "source_url": source_url,
                "final_url": final_url,
                "page_title": page_title,
                "page_status": page_status,
                "detail_length": len(detail_text),
                "is_2027": job["is_2027"],
                "relevance_score": job["relevance_score"],
                "recommendation": job["recommendation"],
                "error_message": error_message,
                "verified_at": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "review_status": "pending"
            }
        )

        print()

    context.close()
    browser.close()


fieldnames = [
    "company",
    "job_title",
    "raw_job_title",
    "source_url",
    "final_url",
    "page_title",
    "page_status",
    "detail_length",
    "is_2027",
    "relevance_score",
    "recommendation",
    "error_message",
    "verified_at",
    "review_status"
]


with open(
    OUTPUT_PATH,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(verified_jobs)


reachable_count = sum(
    job["page_status"] == "reachable"
    for job in verified_jobs
)

error_count = sum(
    job["page_status"] in [
        "error",
        "http_error"
    ]
    for job in verified_jobs
)


print("===== 详情验证报告 =====")
print(f"已处理岗位：{len(verified_jobs)}")
print(f"详情页正常：{reachable_count}")
print(f"详情页错误：{error_count}")
print(f"验证结果已保存：{OUTPUT_PATH}")
print(f"详情文本目录：{DETAIL_DIRECTORY}")
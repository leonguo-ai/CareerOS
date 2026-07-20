import csv
from datetime import date
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

LIST_URL = "https://jobs.bytedance.com/campus/position"
OUTPUT_PATH = "data/bytedance_discovered_jobs.csv"

discovered_jobs = []
seen_urls = set()

print("===== CareerOS ByteDance Adapter V1 =====")
print(f"职位列表网址：{LIST_URL}")

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

    page = context.new_page()

    try:
        page.goto(
            LIST_URL,
            wait_until="domcontentloaded",
            timeout=30000
        )

        page.wait_for_timeout(8000)

        print(f"网页标题：{page.title()}")
        print(f"最终网址：{page.url}")

        anchors = page.locator("a")
        anchor_count = anchors.count()

        print(f"页面链接数量：{anchor_count}")

        for index in range(anchor_count):
            anchor = anchors.nth(index)

            try:
                text = anchor.inner_text(
                    timeout=1500
                ).strip()

                href = anchor.get_attribute("href")

            except Exception:
                continue

            if not href:
                continue

            absolute_url = urljoin(page.url, href)
            normalized_text = " ".join(text.split())

            url_lower = absolute_url.lower()

            # 只保留可能的职位详情链接
            is_position_link = (
                "/position/" in url_lower
                or "position/detail" in url_lower
            )

            if not is_position_link:
                continue

            # 排除职位列表页本身
            if absolute_url.rstrip("/") == LIST_URL.rstrip("/"):
                continue

            if absolute_url in seen_urls:
                continue

            if not normalized_text:
                normalized_text = "职位名称待提取"

            seen_urls.add(absolute_url)

            discovered_jobs.append(
                {
                    "company": "字节跳动",
                    "job_title": normalized_text,
                    "source_url": absolute_url,
                    "source_type": "official_campus",
                    "discovered_date": date.today().isoformat(),
                    "status": "open_unverified",
                    "review_status": "pending"
                }
            )

        print(f"发现候选职位：{len(discovered_jobs)}")

    except Exception as error:
        print("字节职位列表读取失败")
        print(f"错误：{error}")

    finally:
        page.screenshot(
            path="data/bytedance_position_page.png",
            full_page=False
        )

        context.close()
        browser.close()

fieldnames = [
    "company",
    "job_title",
    "source_url",
    "source_type",
    "discovered_date",
    "status",
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
    writer.writerows(discovered_jobs)

print("===== 字节岗位发现报告 =====")
print(f"候选职位数量：{len(discovered_jobs)}")
print(f"结果已保存：{OUTPUT_PATH}")
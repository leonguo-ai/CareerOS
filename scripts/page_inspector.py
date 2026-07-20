import csv
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

SOURCE_PATH = "data/job_sources.csv"
OUTPUT_PATH = "data/discovered_entry_links.csv"

TARGET_KEYWORDS = [
    "岗位",
    "职位",
    "校招",
    "校园招聘",
    "岗位投递",
    "职位搜索",
    "立即投递",
    "去投递",
    "一键投递",
    "查看职位",
    "应届生",
    "实习生",
    "提前批",
    "管培生",
    "招聘项目"
]

sources = []

with open(SOURCE_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["enabled"].strip().lower() == "true":
            sources.append(row)

discovered_links = []

print("===== CareerOS Page Inspector V1 =====")
print(f"待检查来源：{len(sources)}")
print()

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        headless=True
    )

    context = browser.new_context(
        viewport={
            "width": 1440,
            "height": 900
        },
        locale="zh-CN"
    )

    for source in sources:
        page = context.new_page()

        print(f'正在检查：{source["company"]}')
        print(f'网址：{source["source_url"]}')

        try:
            page.goto(
                source["source_url"],
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(5000)

            anchors = page.locator("a")
            anchor_count = anchors.count()

            source_link_count = 0
            seen_links = set()

            for index in range(anchor_count):
                anchor = anchors.nth(index)

                try:
                    text = anchor.inner_text(
                        timeout=2000
                    ).strip()

                    href = anchor.get_attribute("href")

                except Exception:
                    continue

                if not href:
                    continue

                normalized_text = " ".join(text.split())

                matched_keyword = ""

                for keyword in TARGET_KEYWORDS:
                    if keyword.lower() in normalized_text.lower():
                        matched_keyword = keyword
                        break

                if not matched_keyword:
                    continue

                absolute_url = urljoin(
                    page.url,
                    href
                )

                link_key = (
                    source["source_id"],
                    normalized_text,
                    absolute_url
                )

                if link_key in seen_links:
                    continue

                seen_links.add(link_key)

                discovered_links.append(
                    {
                        "source_id": source["source_id"],
                        "company": source["company"],
                        "link_text": normalized_text,
                        "matched_keyword": matched_keyword,
                        "entry_url": absolute_url,
                        "source_url": source["source_url"],
                        "review_status": "pending"
                    }
                )

                source_link_count += 1

            print(f"页面链接总数：{anchor_count}")
            print(f"发现候选招聘入口：{source_link_count}")
            print("结果：成功")

        except Exception as error:
            print("结果：失败")
            print(f"错误：{error}")

        finally:
            page.close()

        print()

    context.close()
    browser.close()

fieldnames = [
    "source_id",
    "company",
    "link_text",
    "matched_keyword",
    "entry_url",
    "source_url",
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
    writer.writerows(discovered_links)

print("===== 页面检查报告 =====")
print(f"候选入口总数：{len(discovered_links)}")
print(f"报告已生成：{OUTPUT_PATH}")

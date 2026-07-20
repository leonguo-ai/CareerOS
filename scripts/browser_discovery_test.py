import csv
from pathlib import Path

from playwright.sync_api import sync_playwright

SOURCE_PATH = "data/job_sources.csv"
SCREENSHOT_DIRECTORY = Path("data/source_screenshots")

SCREENSHOT_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True
)

sources = []

with open(SOURCE_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["enabled"].strip().lower() == "true":
            sources.append(row)

print("===== CareerOS Browser Discovery Test V1 =====")
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

        print(f'正在打开：{source["company"]}')
        print(f'原始网址：{source["source_url"]}')

        try:
            page.goto(
                source["source_url"],
                wait_until="domcontentloaded",
                timeout=30000
            )

            page.wait_for_timeout(5000)

            title = page.title()
            final_url = page.url

            screenshot_path = (
                SCREENSHOT_DIRECTORY
                / f'{source["source_id"]}.png'
            )

            page.screenshot(
                path=str(screenshot_path),
                full_page=False
            )

            print(f"网页标题：{title}")
            print(f"最终网址：{final_url}")
            print(f"截图保存：{screenshot_path}")
            print("结果：成功")

        except Exception as error:
            print("结果：失败")
            print(f"错误：{error}")

        finally:
            page.close()

        print()

    context.close()
    browser.close()

print("===== 浏览器测试完成 =====")
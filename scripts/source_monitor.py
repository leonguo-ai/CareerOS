import csv
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCE_PATH = "data/job_sources.csv"
OUTPUT_PATH = "data/source_status.csv"

sources = []

with open(SOURCE_PATH, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["enabled"].strip().lower() == "true":
            sources.append(row)

results = []

print("===== CareerOS Source Monitor V1 =====")
print(f"启用的招聘来源：{len(sources)}")
print()

for source in sources:
    url = source["source_url"]

    print(f'正在检查：{source["company"]}')
    print(f"网址：{url}")

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/126.0 Safari/537.36"
            )
        }
    )

    http_status = ""
    status = ""
    note = ""

    try:
        with urlopen(request, timeout=15) as response:
            http_status = response.getcode()

            if 200 <= http_status < 400:
                status = "reachable"
                note = "网站可以访问"
            else:
                status = "unexpected_status"
                note = f"收到HTTP状态码 {http_status}"

    except HTTPError as error:
        http_status = error.code

        if error.code in [401, 403, 429]:
            status = "protected"
            note = "网站可以连接，但存在访问保护或频率限制"
        else:
            status = "http_error"
            note = f"HTTP错误 {error.code}"

    except URLError as error:
        status = "connection_error"
        note = str(error.reason)

    except TimeoutError:
        status = "timeout"
        note = "访问超时"

    except Exception as error:
        status = "unknown_error"
        note = str(error)

    checked_at = datetime.now().isoformat(timespec="seconds")

    results.append(
        {
            "source_id": source["source_id"],
            "company": source["company"],
            "source_name": source["source_name"],
            "source_url": url,
            "http_status": http_status,
            "status": status,
            "note": note,
            "checked_at": checked_at
        }
    )

    print(f"结果：{status}")
    print(f"说明：{note}")
    print()

    # 礼貌限速，避免连续快速请求
    time.sleep(2)

fieldnames = [
    "source_id",
    "company",
    "source_name",
    "source_url",
    "http_status",
    "status",
    "note",
    "checked_at"
]

with open(
    OUTPUT_PATH,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

reachable_count = sum(
    result["status"] == "reachable"
    for result in results
)

protected_count = sum(
    result["status"] == "protected"
    for result in results
)

print("===== 来源监控报告 =====")
print(f"检查来源数量：{len(results)}")
print(f"可以直接访问：{reachable_count}")
print(f"存在访问保护：{protected_count}")
print(f"状态报告已生成：{OUTPUT_PATH}")

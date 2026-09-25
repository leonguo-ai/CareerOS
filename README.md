# CareerOS：字节跳动岗位核验闭环

当前阶段是一条单站点原型：发现链接 → 按岗位 ID 筛选和采集详情 → 记录原文证据 → 人工核实开放状态与 2027 届资格 → 匹配简历证据 → 人工审核并保存投递进度。**不会自动提交申请。**通用岗位池仍是另一条示例流程。

`data/bytedance_*` 中原有记录采于 **2026-07-20**，仅作为历史示例。`reachable` 只表示页面当时可访问，不能证明现在开放；旧 CSV 的 `is_2027`、高分和 `priority_review` 不作为申请资格凭据。ZIP 不含私人简历和历史详情文本，无法从旧 CSV 复算旧分数。运行新版筛选、详情采集后才会生成按 `BD-<职位数字ID>.txt` 保存的详情。旧的 `01_标题.txt` 文件不自动关联，以免行顺序变化造成错配。

## 离线演示

以下命令均在 **WSL** 中从仓库根目录执行，标准库即可运行。PowerShell 中可将 `python3` 改为 `python`，路径分隔符用 `\`。

```bash
python3 scripts/bytedance_workflow.py build \
  --filtered examples/bytedance/filtered.csv \
  --verified examples/bytedance/verified.csv \
  --details examples/bytedance/details \
  --resume examples/bytedance/sample_resume.txt \
  --reviews examples/bytedance/empty_reviews.json \
  --output /tmp/careeros_demo.csv
```

第一轮结果为 `verify_first`，即使示例 JD 提到 2027 届并且简历有关键词证据也是如此。核实实际岗位时，先检查官网、再引用对应原文并分别记录两项状态（命令不会访问或提交招聘网站）：

```bash
python3 scripts/bytedance_workflow.py review BD-7660366669840566533 \
  --opening open --opening-evidence '从官网职位页复制可证明仍在招聘的原文'
python3 scripts/bytedance_workflow.py review BD-7660366669840566533 \
  --eligibility yes --eligibility-evidence '从官网职位页复制明确的2027届毕业时间范围'
python3 scripts/bytedance_workflow.py build --resume resumes/master_resume.txt
```

只有在 **详情可用、近期（7 天内）网页可达、开放状态由人工确认且未超过 7 天、2027 届资格由人工确认** 时，结果才可进入 `manual_review`。通过 `review ID --review approved` 保存人工审核，结果显示 `manually_approved`，仍需本人决定是否投递。投递后可用 `review ID --application applied` 保存进度。审核和投递状态单独存于忽略的 `data/bytedance_reviews.json`，再次采集或生成清单不会重置。

## 真实采集（需 Playwright 和 Chromium）

在 **WSL** 中：

```bash
python3 scripts/bytedance_adapter.py
python3 scripts/bytedance_candidate_filter.py
python3 scripts/bytedance_detail_verifier.py
python3 scripts/bytedance_workflow.py build --resume resumes/master_resume.txt
```

Playwright 需要本机已有安装和 Chromium 浏览器；离线演示与测试无此依赖。原始 CSV 及私有详情不代表实时招聘状态。每次采集都应检查页面来源、时间和引用文字。`requirements_evidence` 保存 JD 原句；`resume_evidence` 给出 `evidence_found`、`not_found`、`human_review` 或未提供简历时的 `not_checked`，其中命中只表示文本证据，不能自动断言实际符合技能或经验要求。无详情时留空，禁止生成貌似可信的匹配率。`data/bytedance_actionable.csv` 和审核 JSON 含私有信息，已从 Git 排除。

测试（**WSL**）：

```bash
python3 -m unittest discover -s tests -v
```

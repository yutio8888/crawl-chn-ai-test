# quotes 引文全量校对计划（Issue #72）

## 冻结边界

- 基线提交：`23956ebfbdc5316cfad5e93a9b0183ad76b3727f`。
- 英文生产源：`crawl-ref/source/dat/descript/quotes.txt`。
- 中文生产源：`crawl-ref/source/dat/descript/zh/quotes.txt`。
- 术语权威：`docs/glossary.md`，SHA-256
  `366e807eaae5403b6c3925df5970cd237b447ead76fdb717b71273473b5db67e`。
- 冻结全集：465 个 canonical key，其中 386 条直接引文、79 条 `<target>`
  别名；EN/ZH 键集、物理顺序、章节归属和解析后的别名图均相等。
- 清单 SHA-256：
  `c2018b6538cceb11b82f82240b5fa83af7bbc578315d75fc317991f10782a216`。

Issue 中“约 233 block”是初步估计，不是生产解析结果。本轮以
DescriptionDB 的 `%%%%` 分隔、canonical lowercase key、后定义覆盖和
`<target>` 别名语义为准，因此完整审阅边界是 465 个身份。

## 验收标准

1. `.claude/scripts/quotes_inventory.py` 从 exact Git blob 重建清单，绑定
   baseline、glossary、输入摘要、加载/查询/显示消费者和别名解析证据。
2. 465 个身份各有且仅有一张严格证据卡，卡片完整保存当前 EN/ZH 正文、
   章节、别名目标、解析目标、事实摘要和终态结论。
3. 终态只能为 `keep`、`adjust`、`retranslate`、`defer terminology` 或
   `defer implementation`；本轮没有无法裁决的延期项。
4. 按章节及别名依赖组核对语义、专名、术语、自然度、署名与换行；Issue #3
   的 `QUOTE_NAME_EXCEPTIONS` 和 `docs/decisions.md` 裁定只复用，不重审。
5. 文学出处、译本和标点风格等偏好只记为 suggestion，不凭偏好阻断；只有
   可由英文正文、当前术语或生产语义直接证明的问题才进入修改。
6. 候选审计要求 EN 不变、身份和结构不变，并要求每条 ZH 逐字等于证据卡
   批准的 proposal；inventory/reviewed 双向差集必须为空。
7. 中文资产由单一 `zh-translator` 顺序落地；开发验证使用 translation
   profile，之后按机械路由完成 readiness 和唯一一次 schema-v4 final gate。

## 非目标

- 不修改 quotes 消费者、游戏机制、数值、身份键或别名拓扑。
- 不重审 Issue #3 已裁定的怪物名与文学专名例外。
- 不把译本选择、书名号/引号统一或文学润色偏好升级为阻断项。
- 不新增通用 ledger/schema；严格账本仍是可由本任务清单校验的 Markdown
  JSONL 块。

## 依赖顺序

按文件中八个生产章节依次审阅：Dungeon features → Dungeon branches →
Spells and abilities → Items → Unique monsters → Vault monsters → Monster glyphs
→ Non-unique monsters。别名卡与其 resolved target 在同一依赖组复核，避免把
别名占位当成可独立润色的正文。

## 可复现命令

基线审计：

```bash
DCSS_INVENTORY_TEMP_ROOT=/tmp python3 .claude/scripts/quotes_inventory.py \
  --baseline-ref 23956ebfbdc5316cfad5e93a9b0183ad76b3727f \
  --review-results docs/quotes-review-results.md \
  --inventory-output /tmp/quotes-inventory-issue72.json
```

候选阶段追加 `--candidate-ref <exact-commit>`。输出必须是安全临时目录下的
全新文件；工具会失败关闭清单漂移、账本缺项、非 canonical JSON、未批准翻译
变化、英文漂移或结构漂移。

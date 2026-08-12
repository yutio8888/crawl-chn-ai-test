# Graffiti 全量审核计划（Issue #66）

## 冻结边界

- 基线：`888354b254f86a6b2de13e7ec6b1b73992a629f7`
- 英文生产源：`crawl-ref/source/dat/database/graffiti.txt`
- 中文生产源：`crawl-ref/source/dat/database/zh/graffiti.txt`
- 唯一生产根：`any_graffiti`
- 身份全集：两侧各 58 个唯一 canonical key；英文 404 个加权变体，中文 403 个加权变体。
- 术语权威：`docs/glossary.md`，SHA-256 `95eeacf9704e046c2010ef34859b750d2f8a1937ad87c4a86e8a404c98689407`。

`graffiti.txt` 同时装入 SpeakDB 与 MiscDB。喷泉/装饰地形通过
`decorlines.txt -> any_graffiti` 递归取值，Xom 地形消息通过 Godspeak
递归取值；两条路径最终都执行怪物名/神祇/技能等显示替换。因此本批把
58 个键、递归 token、外部姓名/颜色依赖和后处理 token 视为一个不可拆分
的闭包。

## 基线缺陷与验收标准

基线允许且只允许以下已冻结缺陷：

- `_graffiti_hailed_god_`：EN 5 / ZH 4；
- `_graffiti_happened_reason_`：EN 26 / ZH 25；
- `any_graffiti`：EN 15 / ZH 16；
- 英文 `_graffiti_vengeance_` 第 2 个变体含悬空
  `@graffiti_author_any@`；
- 中文递归图从 `any_graffiti` 无法到达 `_graffiti_unreadable_`。

候选必须满足：

1. 58 个身份各有且仅有一张严格审核卡；每张卡完整绑定当前 EN/ZH
   变体和拟议 EN/ZH 变体、权重、证据与结论。
2. 双语各 404 个变体；每个键的变体数及权重序列逐项一致。
3. 双语从 `any_graffiti` 可达全部 58 个键；无悬空 token、解析错误、
   空 body 或覆盖定义。
4. 仅允许严格账本明确批准的文本、权重、顺序与 token 变化；英文与
   中文候选必须逐字等于账本 proposal。
5. 不修改消费者逻辑、随机选择算法或 RNG 调用拓扑；本批的结构变动
   只恢复已审阅的 canonical EN/ZH 数据等价。

唯一有序 token 语法例外是 `_graffiti_short_saying_` 第 3 个变体：英文
“A loves B's relative/quality”的递归顺序为 A、关系/品质、B，而自然中文
所有格必须为 A、B、关系/品质。审计器仍要求 token 多重集、权重和随机站
完全一致；真实 MiscDB 消费路径用 4096 个固定 seed 证明 EN/ZH 最终 RNG
state/count 一致，并覆盖 15/15 个根分支。

## 批次与依赖顺序

1. 署名、姓名、书写材质、样式、教授/课程和图像碎片；
2. 广告、争斗、人生、传闻、短句、复仇和货物等叙事碎片；
3. 宗教/神祇碎片、不可读/粗俗文本和 `any_graffiti` 根；
4. 顺序落地资产修改，重新生成双语 phase-0 dump，执行候选审计；
5. code profile（含生产路径 Catch2）、机械 review readiness、唯一 Final Gate。

## 可复现命令

基线 inventory：

```bash
python3 .claude/scripts/graffiti_inventory.py \
  --baseline-ref 888354b254f86a6b2de13e7ec6b1b73992a629f7 \
  --english-dump /tmp/issue40-graffiti-phase0-en.json \
  --localized-dump /tmp/issue40-graffiti-phase0-zh.json \
  --review-results docs/graffiti-review-results.md \
  --inventory-output /tmp/issue66-graffiti-inventory.json
```

候选阶段在同一命令追加精确 candidate ref 与两份 candidate phase-0 dump。
输出只能直接写入 `/tmp`；脚本校验 exact-Git 来源、干净候选边界、账本与
glossary blob，并失败关闭任何未审阅漂移。

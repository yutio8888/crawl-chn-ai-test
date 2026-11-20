# DCSS 中文版 0.35-trunk-014 更新公告

各位地牢探险者好：

Dungeon Crawl Stone Soup 中文版现已发布开发分支预发布版 **0.35-trunk-014**。

> **特别提醒**：这是 trunk 预发布（开发线），**不是正式版**。稳定正式版（当前 Latest 为 **0.34.1-zh5-1-018**，后续以稳定线最新正式版为准）仍是推荐版本。trunk 存档不能回到稳定版，两条线可并存安装，建议使用稳定版存档副本进行体验。

---

## 玩家可见亮点

### 1. C++ 国际化与界面显示修复
- **怪物对白与窄屏快捷动作菜单**：修正中文怪物对白中 `@foe,@` 称谓的多余逗号、面向怪物时 `@foe_possessive@` 所有格与盟友名撇号保留；窄终端下 Q 快捷动作菜单会单独测量快捷键行，并按 CJK 宽度折行底栏提示，确保 `[!] 聚焦模式` 等开关状态清晰显示（[#448](https://github.com/yutio8888/crawl-chn-ai-test/pull/448)）。
- **状态、提示与交互细节**：修复 `Cleave+` 状态帮助拼接异常（消除 `None铭印效果`）（[#454](https://github.com/yutio8888/crawl-chn-ai-test/pull/454)）、Xom 祝福查询不再产生副作用并本地化动作页脚标点（[#453](https://github.com/yutio8888/crawl-chn-ai-test/pull/453)）、果冻怪称谓统一与 Xom 称号润色（[#447](https://github.com/yutio8888/crawl-chn-ai-test/pull/447)）。
- **奇械（gizmo）拼接与寻路热键**：`get_gizmo_name` 样式 2–4 的中文词组件之间不再插入多余空格（缺失中文库回退英文词时仍保留词间空格），`gizmo.txt` 补齐 17 项前缀词缀形容词与 `bogo` → `波戈` 等译名；修正祭坛跨层寻路首字母热键查找与提示文案（[#465](https://github.com/yutio8888/crawl-chn-ai-test/pull/465)）。

### 2. D-1..D-7 术语统一与三轮全库翻译质量润色
- **术语与随机书名去重**：统一 `flail` 为“链枷”、七项变异裸键、`quiver` 动作为“快捷动作”（D-C-127）、`cleave` 为“顺劈”、`rFire∞`/`rCold∞`/`rElec∞` 等抗性免疫限定写法（D-C-123）、`Fire+`/`Fire++` 为“着火+`/`着火++”及 Vehumet 射程描述；精简 `randbook.txt` 学派形容词词干与等级书名模板以消除重复的“的”（[#456](https://github.com/yutio8888/crawl-chn-ai-test/pull/456)）。
- **全库润色与运行时一致性（Wave 1–3）**：完成高/中低频条目及可裁决暂缓条目（含引文、武器歌、神祇人称，移除英文原文未陈述的额外机制）的全面润色（[#458](https://github.com/yutio8888/crawl-chn-ai-test/pull/458)、[#462](https://github.com/yutio8888/crawl-chn-ai-test/pull/462)、[#464](https://github.com/yutio8888/crawl-chn-ai-test/pull/464)）；同步 3 条 `CANDIDATE` 怪物施法运行时覆盖与 `zh/monspell.txt`（蛛网、召唤凡间勇士、Boris 悲伤行军），并将 `options_guide.txt` 的“发射栏”全部对齐为“快捷动作”（[#468](https://github.com/yutio8888/crawl-chn-ai-test/pull/468)）。

### 3. 上游游戏内容同步（至 `9cbd9afba78`）
- **技能点与经验药水重做**：同步上游技能点模型重构与经验药水改动（含修复豺狼人全技能满 27 级后分布训练死循环的本地有界回归修复）（[#460](https://github.com/yutio8888/crawl-chn-ai-test/pull/460)）。
- **物品与说明调整**：`bone scales` 更名为 `bone dragon armour`（中文「骨龙甲」），更新气龙脉“3 个最远目标且伤害不随距离衰减”、位面撕裂“深渊”分支及 Xom 混沌解经祈祷机制；同步 Recall 对异层伙伴与永久盟友击杀统计、Gulch 地图平衡及新训练金库（[#443](https://github.com/yutio8888/crawl-chn-ai-test/pull/443)、[#460](https://github.com/yutio8888/crawl-chn-ai-test/pull/460)）。

---

## 升级与存档说明

- **旧存档机制**：旧存档中已生成的随机书名、神器名和已记录的消息历史保留生成时的文字；新的命名与翻译只作用于之后生成或显示的内容。
- **独立配置与存档隔离**：trunk 使用独立存档目录，不与稳定版混用；仍建议用稳定版存档副本测试，**trunk 存档不能回到稳定版**。

---

## 测试反馈

本版本**没有经过真机或游玩验收**，欢迎玩家试用并协助验证。

如遇问题，请前往反馈：
- **Release Issue**：#469 https://github.com/yutio8888/crawl-chn-ai-test/issues/469
- **Issues 页**：https://github.com/yutio8888/crawl-chn-ai-test/issues

---

## 技术附录与发布核验

### 包含 PR（相对 `0.35-trunk-013`）
- 上游同步：[#443](https://github.com/yutio8888/crawl-chn-ai-test/pull/443)（`ecd2bd72d73`）、[#460](https://github.com/yutio8888/crawl-chn-ai-test/pull/460)（`9cbd9afba78`）
- 翻译、代码与归档：[#440](https://github.com/yutio8888/crawl-chn-ai-test/pull/440)、[#441](https://github.com/yutio8888/crawl-chn-ai-test/pull/441)、[#447](https://github.com/yutio8888/crawl-chn-ai-test/pull/447)、[#448](https://github.com/yutio8888/crawl-chn-ai-test/pull/448)、[#450](https://github.com/yutio8888/crawl-chn-ai-test/pull/450)、[#453](https://github.com/yutio8888/crawl-chn-ai-test/pull/453)、[#454](https://github.com/yutio8888/crawl-chn-ai-test/pull/454)、[#456](https://github.com/yutio8888/crawl-chn-ai-test/pull/456)、[#458](https://github.com/yutio8888/crawl-chn-ai-test/pull/458)、[#462](https://github.com/yutio8888/crawl-chn-ai-test/pull/462)、[#464](https://github.com/yutio8888/crawl-chn-ai-test/pull/464)、[#465](https://github.com/yutio8888/crawl-chn-ai-test/pull/465)、[#468](https://github.com/yutio8888/crawl-chn-ai-test/pull/468)

### 注意事项

- 本版不含 WebTiles 服务器端新改动；服务器部署仍须使用同一次构建的 `crawl` 与 `webserver/game_data/` 静态资源。

### 支持平台

- Windows Tiles：ZIP，解压后运行 `crawl.exe`；存档写入 `%APPDATA%\crawl-trunk`。请解压到独立目录，避免覆盖稳定版。
- macOS Tiles：ad-hoc 签名 DMG，打开后运行 `Dungeon Crawl Stone Soup Trunk - Tiles.app`。首次启动仍可能需按 Gatekeeper 提示选择“打开”，或在“系统设置 → 隐私与安全性”中选择“仍要打开”。若系统仍拦截，可在已将应用拖出 DMG 后执行 `xattr -dr com.apple.quarantine "Dungeon Crawl Stone Soup Trunk - Tiles.app"`；ad-hoc 签名只封存应用内容，不代表 Apple Developer 签名或公证。
- Android：签名的四 ABI APK（包名 `org.develz.crawl.trunk`，与稳定版 `org.develz.crawl` 并存）。

### 延期平台

- Linux：仅保留 CI 编译验证。

### 下载校验

请使用 `SHA256SUMS` 校验 Windows ZIP、macOS DMG 与 Android APK；`RELEASE-MANIFEST.txt` 记录标签、准确提交和资产摘要。

### 待测试玩家验证（发布后）

当前状态：全部**未验证**。
- Windows Tiles：解压启动，中文默认语言、字体、主菜单；记录 Windows 版本与 CPU 架构。
- macOS：DMG 校验、打开并启动 Tiles（含一次 Gatekeeper 确认）；记录 macOS 版本与架构。
- Android：安装或覆盖升级签名 APK，确认中文显示，稳定版应用与存档未受影响；记录 Android 版本、设备与 ABI。
- 各平台：新游戏、帮助、存档与读档；trunk 与稳定版并存安装。
- 本版重点：窄屏 Q 快捷动作菜单换行、奇械（gizmo）中文拼接、祭坛寻路热键、随机书名去重、`options_guide.txt` 快捷动作术语、以及上游技能点/经验药水/骨龙甲等新文本显示。

### 发布前技术核验（2026-11-20）

- 标签 `0.35-trunk-014`（annotated）→ `c662be078cb34f6b1519f0bba4f3eca0ff88b427`；标签 CI [run 44710669630](https://github.com/yutio8888/crawl-chn-ai-test/actions/runs/44710669630) 首次尝试 14/14 job 成功。
- `RELEASE-MANIFEST.txt` 绑定上述提交；`SHA256SUMS` 对三个安装包回下载校验全部 OK；资产为封闭的 5 项（Windows ZIP、macOS DMG、Android APK、`SHA256SUMS`、`RELEASE-MANIFEST.txt`）。
- Android：`org.develz.crawl.trunk`（Dungeon Crawl Stone Soup Trunk），versionCode 1036（013 为 991），versionName `0.35-trunk-014`，四 ABI（`arm64-v8a`、`armeabi-v7a`、`x86`、`x86_64`，均含 `libmain.so` 与 `libpcre.so`）；`apksigner` v1/v2/v3 验证通过，签名证书 SHA-256 `fb3ce3ed1cc644cf6640f3a0acdd71eaef534372d6caf36ec0708c6251971801` 与 `0.35-trunk-013` 一致。
- 以上为构建与包身份技术检查，**不代表**真机或实际游玩验收。

# 翻译工具链使用说明

项目 `.claude/scripts/` 下有 4 个脚本覆盖翻译质量保障的完整链路。所有脚本从仓库根目录运行。

## 快速参考

| 需求 | 命令 |
|------|------|
| 验证 T_() key 覆盖率 | `python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| 发现无 T_() 的英文消息 | `python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/` |
| 检查 mprf_p 兼容性 | `python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| 检查 %s 数量一致 | `python3 .claude/scripts/scan_i18n.py arg-mismatch --source-txt crawl-ref/source/dat/i18n/zh/source.txt` |
| 检测语言依赖参数 | `python3 .claude/scripts/scan_i18n.py lang-args crawl-ref/source/` |
| 数据库完整性 | `bash .claude/scripts/check_consistency.sh --all` |
| 运行测试 | `bash .claude/scripts/tests/test_scan_i18n.sh` |

## 脚本详解

### i18n_extract.py — T_() 键提取与验证

从 C++ 源码中提取所有 `T_("...")` 和 `C_("ctx", "...")` 调用，与 source.txt 对比。

```bash
# 提取所有 T_() 键
python3 .claude/scripts/i18n_extract.py extract crawl-ref/source/

# 验证覆盖率（CI 阻断级）
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# 生成缺失键的存根
python3 .claude/scripts/i18n_extract.py missing crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# 查找不再被引用的死条目
python3 .claude/scripts/i18n_extract.py stale crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
```

### scan_i18n.py — T_() 世界盲区扫描

替代旧的 `scan_untranslated.sh`（旧脚本基于 if/else 语言守卫检测，在 T_() 世界已失效）。

```bash
# missing-t: 找出所有 mprf/mpr 调用中缺少 T_() 包裹的英文消息
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/

# mprf-p: source.txt 用了 %n$s 位置参数的翻译，代码必须用 mprf_p 而非 mprf
# （MinGW vsnprintf 不支持 POSIX 位置参数，mprf_p 走手写实现）
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# arg-mismatch: 检查 EN key 和 CN 翻译的 %s 数量是否一致
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# lang-args: 检测 T_() 调用中语言依赖的参数（启发式，产生候选列表）
python3 .claude/scripts/scan_i18n.py lang-args crawl-ref/source/
```

### check_consistency.sh — 数据库完整性

```bash
bash .claude/scripts/check_consistency.sh --all     # 全部检查
bash .claude/scripts/check_consistency.sh --gods    # 神名翻译一致性
bash .claude/scripts/check_consistency.sh --skills  # 技能学派翻译
bash .claude/scripts/check_consistency.sh --spells  # 法术键完整性
bash .claude/scripts/check_consistency.sh --format  # %%%% 分隔符数量校验
bash .claude/scripts/check_consistency.sh --database # @keyword@ 引用完整性
```

## 典型工作流

### 新增翻译后

```bash
# 1. 验证所有 T_() 键都有 source.txt 条目
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# 2. 检查位置参数是否正确使用 mprf_p
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt

# 3. 编译
cd crawl-ref/source && make -j4
```

### 发现盲区

```bash
# 1. 扫描遗漏的英文消息
python3 .claude/scripts/scan_i18n.py missing-t crawl-ref/source/ > missing.txt

# 2. 扫描 %s 数量不一致
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt > mismatches.txt

# 3. 手动审查候选列表，将真正需要翻译的建立 Issue
```

### CI / 提交前检查

```bash
# 必须全部通过才能提交
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
make -j4
```

## 退出码约定

| 脚本 | 子命令 | 发现时退出码 |
|------|--------|-------------|
| `i18n_extract.py` | `validate` | 1（有缺失 key） |
| `i18n_extract.py` | `stale`, `missing` | 0（信息性） |
| `scan_i18n.py` | `missing-t`, `mprf-p`, `arg-mismatch` | 1（有违规） |
| `scan_i18n.py` | `lang-args` | 0（启发式，始终通过） |

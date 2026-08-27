# Titan 日志分析工具

本地网页工具：导入 Titan（TKA 手术机器人 Qt 应用）的 spdlog 日志，按 `docs/titan-log-spec.md` 里的表格做步骤映射、重点标注和异常标注，并画成时间轴。

分类规则只来自 spec 文件。改表保存后点界面「重新加载规则」，或刷新页面（服务会按文件 mtime 自动重载）。不必改代码。

## 运行

需要 Python 3.10+（只用标准库，无需 pip）。

```bash
python3 -m app.main
```

浏览器打开 http://127.0.0.1:8765 （默认绑定 0.0.0.0:8765）。

可选端口：`python3 -m app.main 8765` 或 `python3 -m app.main 0.0.0.0:8765`。

## 用法

1. 左侧「导入日志」可多选文件（批量导入）。一次只查看一个文件。
2. 点文件名打开时间轴。默认隐藏噪声（键盘、关节角转储等）和未映射行。
3. 「显示噪声」/「显示全部」切换过滤。
4. 金色条 = 重点（标注=key），红色条 = 异常（标注=anomaly 或级别 E/C）。
5. 点击事件展开原始日志行、级别、线程号。
6. 删除只影响 data/ 里的副本，不改原始文件。

## 日志格式

    [HH:MM:SS +08:00] [Daily_logger] [---L---] [thread N] message

L 为 T/D/I/W/E/C。文件名 log_file_YYYY-MM-DD.txt 会取出日期；医院改名文件没有日期时用文件 mtime，或显示为未知。崩溃堆栈（CRASH DETECTED、SIGSEGV 等非标准行）会收成一条异常事件。

## Spec 匹配顺序（硬编码，与 spec 文内约定一致）

1. 级别 E/C（含空的 ---E---，标签「空错误行」）
2. 异常表
3. 噪声表（默认隐藏）
4. 步骤映射表 + 关键信息表
5. 未匹配的已解析行：默认隐藏，可用「显示全部」打开

同一张表内从上到下，第一条命中即停。不解析「软件页面与步骤（业务顺序）」那张表（列是顺序/源码页面，不是日志匹配）。步骤映射/关键信息表可有可选列「阈值」（或 threshold），如 `>1` / `>1mm`：取出消息最后一个浮点数（mm），超过则标 anomaly，事件带 `value_mm`。

## API（本地）

- GET /api/logs 文件列表
- POST /api/logs multipart 上传，字段名 files
- POST /api/logs/import-path JSON {"path": "/abs/file.txt"} 或 {"paths": [...]}
- GET /api/logs/{id}/timeline?show_noise=0&show_all=0
- DELETE /api/logs/{id}
- GET /api/spec  /  POST /api/spec/reload

事件过多（>5 万）时时间轴返回默认过滤集并带 truncated 标记。

## 目录

- docs/titan-log-spec.md — 唯一分类配置
- app/ — 解析器与 HTTP 服务
- web/ — 静态页面（无构建步骤）
- data/ — 导入副本与索引（已 gitignore）
- samples/ — 本地试跑用，不要提交

不要把医院现场日志提交进 git。

# Titan 日志分析：关键定义与步骤说明

> 本文件是日志分析工具的**唯一配置依据**。改完保存后刷新网页即可生效（若未生效，重启服务）。
>
> 工具按表格**从上到下**匹配，第一条命中即停。
>
> 这是初稿。步骤中文名、还要不要显示、阈值等，请你直接改本文件；工具按表生效，不必先改代码。
>
> 标记约定：
> - 匹配方式：`contains`（默认，子串）| `prefix` | `regex`
> - 类别：`lifecycle` 生命周期 / `page` 大页面跳转 / `step` 页内步骤 / `key` 关键信息 / `robot` 机器人动作 / `noise` 噪声 / `other`
> - 时间轴：`show` 显示 | `hide` 默认隐藏
> - 标注：`none` 普通 | `key` 重点（蓝/金） | `anomaly` 异常（红）
> - 阈值：可选。如 `>1` 表示日志里最后一个数字（单位 mm）大于 1 则升为异常，否则仍按「标注」列。空着=不做数值判断

## 日志格式（不要改，除非 Titan 换了 logger）

日常文件：`tka_logs/log_file_YYYY-MM-DD.txt`（相对进程工作目录，不是 Documents）。

行格式：

```
[HH:MM:SS +08:00] [Daily_logger] [---L---] [thread N] message
```

`L`：T 跟踪 / D 调试 / I 信息 / W 警告 / E 错误 / C 严重。UTF-8。按天滚动，追加写入。

医院现场常把文件改名为 `医院-病例-姓名-侧-后缀.txt`，内容格式相同。工具同时接受这两种文件名。

`qDebug` 不进 tka_logs，只在 stdout，本工具不解析。

崩溃时会出现非标准行，例如 `===== CRASH DETECTED =====`、`Caught signal 11`、函数堆栈。按「异常规则」处理。

---

## 软件页面与步骤（业务顺序）

时间轴按**大页面跳转**分段（方案预览、配准、导航、术中测量评估等）。页内步骤是页面下面的细项。中文名请按你们实际 UI/培训改。

| 顺序 | 软件步骤（显示名） | 源码页面/模块 | 日志中的实际名称 | 说明 |
| --- | --- | --- | --- | --- |
| 0 | 启动 | TKAMainWindow | Titan Application Startup | |
| 1 | 登录 | TKAPageLogin | login page | 日志几乎没有登录成败，只有离开登录页 |
| 2 | 方案管理 | TKAPageManage | plan manage page | |
| 3 | 主页 | home page | home page | |
| 4 | 方案预览 | TKAPlanViewer | planviewer page | 大页面 |
| 5 | 配准 | TKAFemurReg | prepare page | 大页面。页内 check = 检查配准精度 |
| 5.1 | 股骨配准 | TKAFemurReg | femur register step | |
| 5.2 | 股骨配准精度检查 | TKAFemurReg | femur check step | 不是截骨页的 check |
| 5.3 | 胫骨配准 | TKAFemurReg | tibia register step | |
| 5.4 | 胫骨配准精度检查 | TKAFemurReg | tibia check step | 日志带 `to`：`switch to tibia check step` |
| 6 | 导航 | TKARobotMotion | robot motion | 大页面。页内 check = 工具测量实际截骨量 |
| 6.1 | 股骨远端截骨 | TKARobotMotion | femur distal step | |
| 6.2 | 胫骨截骨 | TKARobotMotion | tibia step | |
| 6.3 | 股骨后髁截骨 | TKARobotMotion | femur poster step | |
| 6.4 | 股骨远端截骨量测量 | TKARobotMotion | femur distal check step | |
| 6.5 | 胫骨截骨量测量 | TKARobotMotion | tibia check step | 日志不带 `to`：`switch tibia check step` |
| 6.6 | 股骨后髁截骨量测量 | TKARobotMotion | femur poster check step | |
| 7 | 术中测量评估 | TKAGapMeasure | gapmeasure page | 大页面 |
| 8 | 导航（摆锯） | TKACutterNavigation | cutter navigation page | 也是导航类大页面；显示名可改 |
| 9 | 退出 | TKAMainWindow | Titan Application Exit | |

台车放置：`switch cart placement left/right`，**不算关键步骤**，时间轴默认隐藏。

---

## 步骤映射（时间轴主事件）

改「软件步骤」列即改时间轴上的中文标签。

| 日志匹配 | 匹配方式 | 软件步骤 | 类别 | 时间轴 | 标注 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| Titan Application Startup | contains | 软件启动 | lifecycle | show | key | |
| Titan vesrion | contains | 软件版本 | lifecycle | show | key | 源码拼写就是 vesrion |
| Titan Application Exit | contains | 软件退出 | lifecycle | show | key | |
| from login page switch to plan manage page | contains | 登录 → 方案管理 | page | show | key | |
| from plan manage page switch to home page | contains | 方案管理 → 主页 | page | show | key | |
| from home page switch to plan manage page | contains | 主页 → 方案管理 | page | show | key | 返回方案列表 |
| take over planviewer page | contains | 方案预览 | page | show | key | 大页面 |
| take over prepare page | contains | 配准 | page | show | key | 日志带句号 |
| robot motion take over | contains | 导航 | page | show | key | 机器人截骨导航 |
| take over gapmeasure page | contains | 术中测量评估 | page | show | key | 大页面 |
| take over cutter navigation page | contains | 导航（摆锯） | page | show | key | 大页面；显示名可改 |
| click start operation | contains | 开始手术 | step | show | key | |
| start load plan uuid | contains | 开始加载方案 | step | show | key | 消息含 UUID |
| load plan sucess | contains | 加载方案成功 | step | show | key | 源码拼写 sucess |
| load ct plan sucess | contains | 加载 CT 方案成功 | step | show | key | |
| loaded plan | prefix | 方案植入物信息 | key | show | key | brand/series/type |
| operation side | prefix | 手术侧/性别/年龄 | key | show | key | TODO：是否脱敏显示 |
| start import plan path | contains | 开始导入方案 | step | show | key | |
| read plan path | contains | 读取外部方案 | step | show | none | 后续有 sucess/fail |
| import plan path | contains | 导入方案结果 | step | show | key | |
| create ctfree plan uuid | contains | 创建 CT-Free 方案 | step | show | key | |
| delete ctfree plan uuid | contains | 删除 CT-Free 方案 | step | show | none | |
| delete ctbase plan uuid | contains | 删除 CT 方案 | step | show | none | |
| switch to femur register step | contains | 股骨配准 | step | show | key | |
| switch to femur check step | contains | 股骨配准精度检查 | step | show | key | 配准页 check |
| switch to tibia register step | contains | 胫骨配准 | step | show | key | |
| switch to tibia check step | contains | 胫骨配准精度检查 | step | show | key | 配准页，日志含 to |
| switch femur distal check step | contains | 股骨远端截骨量测量 | step | show | key | 导航页 check=测截骨量 |
| switch femur poster check step | contains | 股骨后髁截骨量测量 | step | show | key | |
| switch femur distal step | contains | 股骨远端截骨 | step | show | key | |
| switch femur poster step | contains | 股骨后髁截骨 | step | show | key | |
| switch tibia check step | contains | 胫骨截骨量测量 | step | show | key | 导航页，日志不含 to |
| switch tibia step | contains | 胫骨截骨 | step | show | key | |
| switch cart placement left | contains | 台车放置-左 | step | hide | none | 不算关键步骤 |
| switch cart placement right | contains | 台车放置-右 | step | hide | none | 不算关键步骤 |
| start collect gap in gapmeasure page | contains | 开始采集间隙 | step | show | key | |
| finish collect gap in gapmeasure page | contains | 完成采集间隙 | step | show | key | |
| cutter before in gapmeasure page | contains | 间隙测量-截前 | step | show | key | |
| cutter after in gapmeasure page | contains | 间隙测量-截后 | step | show | key | |
| switch show gap curve in gapmeasure page | contains | 间隙曲线视图 | step | show | none | |
| switch show realtime model in gapmeasure page | contains | 间隙实时模型视图 | step | show | none | |
| enter tibia draw line mode | contains | 进入胫骨划线 | step | show | key | |
| exit tibia draw line mode | contains | 退出胫骨划线 | step | show | none | |
| enter saw mode | contains | 进入摆锯模式 | step | show | key | |
| exit saw mode | contains | 退出摆锯模式 | step | show | none | |
| kuka app is connected | contains | KUKA 已连接 | robot | show | key | |
| kuka app is disconnected | contains | KUKA 断开 | robot | show | anomaly | |
| connect ndi sucess | contains | NDI 连接成功 | key | show | key | |
| connect mxio sucess | contains | MXIO 连接成功 | key | show | none | |
| login encryption dog | contains | 加密狗登录 | key | show | none | |

---

## 关键信息（重点标注）

距离单位都是 **mm**。配准误差、点校验误差 **>1 mm 升为异常**（改「阈值」列即可）。

| 日志匹配 | 匹配方式 | 软件步骤 | 类别 | 时间轴 | 标注 | 阈值 | 说明 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| femur register error | contains | 股骨配准误差 | key | show | key | >1 | 取消息最后一个数字，单位 mm |
| tibia register error | contains | 胫骨配准误差 | key | show | key | >1 | |
| arm register finish error | contains | 手臂配准误差 | key | show | key | >1 | |
| probe verify femur point | contains | 股骨点校验误差 | key | show | key | >1 | `probe verify femur point N error: x`，x 为 mm |
| probe verify tibia point | contains | 胫骨点校验误差 | key | show | key | >1 | |
| TKANail nail verify error | contains | 骨钉校验误差 | key | show | key | >1 | |
| probe calibration error | contains | 探针标定误差 | key | show | key | >1 | |
| probe calibration result | contains | 探针标定结果 | key | show | none |  |  |
| plan femur distal medial depth | contains | 方案-股骨远端内侧深度 | key | show | none |  | 打开截骨导航时一批方案参数 |
| plan femur distal lateral depth | contains | 方案-股骨远端外侧深度 | key | show | none |  |  |
| plan femur poster medial depth | contains | 方案-股骨后髁内侧深度 | key | show | none |  |  |
| plan femur poster lateral depth | contains | 方案-股骨后髁外侧深度 | key | show | none |  |  |
| plan tibia proximal medial depth | contains | 方案-胫骨近端内侧深度 | key | show | none |  |  |
| plan tibia proximal lateral depth | contains | 方案-胫骨近端外侧深度 | key | show | none |  |  |
| plan femur varus | contains | 方案-股骨内翻 | key | show | none |  |  |
| plan femur flexion | contains | 方案-股骨屈曲 | key | show | none |  |  |
| plan femur rotation | contains | 方案-股骨旋转 | key | show | none |  |  |
| plan tibia varus | contains | 方案-胫骨内翻 | key | show | none |  |  |
| plan tibia flexion | contains | 方案-胫骨屈曲 | key | show | none |  |  |
| plan tibia rotation | contains | 方案-胫骨旋转 | key | show | none |  |  |
| cutted after stretch medial max gap | contains | 截后伸直内侧最大间隙 | key | show | key |  |  |
| cutted after stretch lateral max gap | contains | 截后伸直外侧最大间隙 | key | show | key |  |  |
| cutted after bend medial max gap | contains | 截后屈曲内侧最大间隙 | key | show | key |  |  |
| cutted after bend lateral max gap | contains | 截后屈曲外侧最大间隙 | key | show | key |  |  |
| cutted before stretch medial max gap | contains | 截前伸直内侧最大间隙 | key | show | key |  |  |
| cutted before stretch lateral max gap | contains | 截前伸直外侧最大间隙 | key | show | key |  |  |
| cutted before bend medial max gap | contains | 截前屈曲内侧最大间隙 | key | show | key |  |  |
| cutted before bend lateral max gap | contains | 截前屈曲外侧最大间隙 | key | show | key |  |  |
| cutted after knee varus | contains | 截后膝内翻 | key | show | key |  |  |
| cutted before knee varus | contains | 截前膝内翻 | key | show | key |  |  |
| after move guider | contains | 导板到位后参数 | key | show | none |  | TODO：是否全部上时间轴，量很大 |
| FmeurReg's marker nail wighet open | contains | 配准页骨钉权重打开 | key | show | none |  | 源码拼写 Fmeur/wighet |

---

## 异常操作（红色重点标注）

工具匹配顺序（改工具时遵守，本表本身也参与匹配）：异常规则与级别 E/C 优先于步骤映射。空消息的 `---E---` 标为「空错误行」。

| 日志匹配 | 匹配方式 | 软件步骤 | 类别 | 时间轴 | 标注 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| CRASH DETECTED | contains | 软件崩溃 | other | show | anomaly | 非标准行，堆栈会跟在后面 |
| Caught signal | contains | 捕获信号崩溃 | other | show | anomaly | 常见 SIGSEGV |
| Emergency stop button external is pressed | contains | 外部急停按下 | robot | show | anomaly | |
| connect ndi failed | contains | NDI 未连接（进模拟器） | other | show | anomaly | NDI 没连上算异常 |
| connect mxio failed | contains | MXIO 连接失败 | other | show | anomaly | |
| send teach cmd but robot app is disconnect | contains | 示教时机器人未连接 | robot | show | anomaly | |
| read plan path .+ from external fail | regex | 读取外部方案失败 | step | show | anomaly | |
| import plan path .+ fail | regex | 导入方案失败 | step | show | anomaly | 若源码没有 fail 句，可删 |
| import brand ini fail | contains | 导入品牌 ini 失败 | other | show | anomaly | |
| can not get | contains | 数据库缺少品牌缩写 | other | show | anomaly | |
| kuka app is disconnected | contains | KUKA 断开 | robot | show | anomaly | TODO：术中断开才算异常的话请加说明 |

工具实现约定（改工具时遵守）：

1. 先匹配「异常规则」和级别 `E`/`C`（空消息的 `---E---` 也算异常，标签：空错误行）。
2. 再匹配本文件的异常表。
3. 再匹配噪声表（命中则默认隐藏）。
4. 再匹配步骤映射 + 关键信息表。
5. 未匹配的普通日志：时间轴默认隐藏，可「显示全部」。

级别规则：

| 级别 | 默认标注 | 时间轴 | 说明 |
| --- | --- | --- | --- |
| E | anomaly | show | 含空消息 |
| C | anomaly | show | |
| W | none | show | TODO：警告是否全部显示 |
| I/D/T | none | 由映射表决定 | |

---

## 噪声（默认从时间轴隐藏）

现场日志里这类占大多数。需要看细节时打开「显示噪声」。

| 日志匹配 | 匹配方式 | 软件步骤 | 类别 | 时间轴 | 标注 | 说明 |
| --- | --- | --- | --- | --- | --- | --- |
| keyPressEvent | contains | 键盘按键 | noise | hide | none | |
| TKAKeyboard | contains | 脚踏/键盘有效性 | noise | hide | none | |
| press keyboard | contains | 按下键盘 | noise | hide | none | |
| release keyboard | contains | 松开键盘 | noise | hide | none | |
| set keyboard | contains | 设置键盘有效 | noise | hide | none | |
| Follow btn | contains | Follow 按钮 | noise | hide | none | |
| joint, a1: | contains | 关节角转储 | noise | hide | none | `before/end/after ... joint` |
| before tibia | contains | 胫骨运动前关节角 | noise | hide | none | |
| before femur | contains | 股骨运动前关节角 | noise | hide | none | |
| after robot move joint | contains | 运动后关节角 | noise | hide | none | |
| after move guider | contains | 导板运动后数值 | noise | hide | none | 与关键信息表冲突：若你希望显示导板到位参数，从本表删掉这行 |
| detect net ip | contains | 网卡 IP 探测 | noise | hide | none | |
| BrandKnee ini is already exist | contains | 品牌 ini 已存在 | noise | hide | none | 每次启动都有 |
| load all brand | contains | 加载全部品牌 | noise | hide | none | |
| temp pdf dir | contains | 临时 PDF 目录 | noise | hide | none | |
| pkill SiriusApp | contains | 结束 Sirius | noise | hide | none | TODO：是否其实是关键步骤 |
| probe2femurmarker point | contains | 股骨采点坐标 | noise | hide | none | 校验误差已在关键信息里 |
| probe2tibiamarker point | contains | 胫骨采点坐标 | noise | hide | none | |
| probe2ndi | contains | 探针相对 NDI | noise | hide | none | |
| femurmarker2ndi | contains | 股骨 marker NDI | noise | hide | none | |
| tibiamarker2ndi | contains | 胫骨 marker NDI | noise | hide | none | |
| femurmarker2ct | contains | 股骨 marker→CT | noise | hide | none | |
| tibiamarker2ct | contains | 胫骨 marker→CT | noise | hide | none | |
| cart teach button | contains | 台车示教按钮 | noise | hide | none | TODO：是否要显示 |
| TKARobotMotion recv | contains | 机器人收到指令 | noise | hide | none | |
| TKARobotMotion end | contains | 机器人指令结束 | noise | hide | none | |
| TKAKukaCmd send | contains | 发送 KUKA 指令 | noise | hide | none | 关键结果用步骤表，不看每条 cmd |
| before send | contains | 发送前关节角 | noise | hide | none | |
| before fix plane send joint | contains | 定平面前关节角 | noise | hide | none | |
| robot stop | contains | 机器人停止类 | noise | hide | none | TODO：急停不是这个 |
| send teach cmd and try to open hard switch | contains | 示教开硬开关 | noise | hide | none | |
| send open soft switch cmd | contains | 开软开关 | noise | hide | none | |
| reading handguding button | contains | 手导按钮 | noise | hide | none | |
| RobotTeachState | contains | 示教状态机 | noise | hide | none | |
| robot cmd tool guider send | contains | 发送导板工具 | noise | hide | none | |
| fix plane motion | contains | 定平面+键盘 | noise | hide | none | |
| fix line motion | contains | 定直线+键盘 | noise | hide | none | |

---

## 已定（写在上面的表里了）

- 距离单位 mm；配准和点校验 **>1 mm** 算异常
- 配准页 check = 检查配准精度；导航页 check = 工具测量实际截骨量
- 时间轴按大页面分段：方案预览、配准、术中测量评估、导航等
- 台车放置不算关键步骤
- NDI 没连上算异常

## 请你在本文件继续完善

步骤中文名、还要显示哪些、哪些改成噪声/异常，直接改表。保存后点网页「重新加载规则」。
新增一行映射就能多一种步骤，一般不必改代码。

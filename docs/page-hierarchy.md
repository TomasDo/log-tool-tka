# Titan 页面 / 步骤分级（时间轴轨道用）

> 和 `titan-log-spec.md` 一起驱动工具。显示名以 spec 为准；本文件只定 **一级 / 二级 / 三级** 和轨道该画什么。
>
> 源码依据：`TKAUIStruct.h` 的 `PageIndex`、`TopNavigation`、`PrepareSubStep`、`CutterStep`，以及 `TKAConsummation` 注释（一级进度栏 / 任务清单 / 页内切换）。
>
> **有疑问的行标了 `?`。请直接改本文件后 push。**

## 怎么用在时间轴上

横向时间轴（剪辑器风格）：

- 主轨道：日志全文（一行一个刻度，可缩放）
- 一级轨道：登录、方案管理、方案预览、准备、术中评估、导航
- 二级轨道：当前一级页面下的任务清单
- 三级轨道：页内模式（摆锯可视化、胫骨划线、附加采集等）
- 播放头拖动 ↔ 原始日志某一行（terminal 窗口跟着滚）

横轴按**日志行号**（不是墙钟），这样拖进度条能精确对到行。

---

## 壳页面（进 home 之前）

`PageIndex`：`login` / `manage` / `home`。`home` 是四个一级手术页的主窗口，本身不单独占一级轨道。

| 级别 | 显示名 | 源码 | 日志匹配 | 轨道 |
| --- | --- | --- | --- | --- |
| 1 | 登录 | PageIndex::login | from login page switch to plan manage page（离开登录） | L1，从启动到切走 |
| 1 | 方案管理 | PageIndex::manage | from login…plan manage；from home…plan manage | L1 |
| （容器） | 主窗口 | PageIndex::home | from plan manage page switch to home page | 不单独占轨道 |

---

## 一级：home 顶栏 `TopNavigation`

`slot_first_level_index`。其中 `cutter_navigation` 会同时 `take_over` 截骨器导航页 **和** `TKARobotMotion`（机械臂导航）。

| 级别 | 显示名 | 源码 | 日志匹配 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 方案预览 | TopNavigation::planviewer | take over planviewer page | |
| 1 | 准备 | TopNavigation::prepare | take over prepare page | 含工具标定、股骨/胫骨注册验证 |
| 1 | 术中评估 | TopNavigation::gap_measure | take over gapmeasure page | 用于截骨前间隙采集评估和截骨后间隙采集评估 |
| 1 | 导航 | TopNavigation::cutter_navigation | take over cutter navigation page **以及** robot motion take over | 顶栏同一级；机械臂截骨和摆锯都在这一页里 |
| — | 机械臂维护 / 相机 / 设置 / 退出 / EMC | robot_maintenance, camera, setting, exit, emc | 日志很少 | 这些是独立于业务的后台日志，记录设备的运行状态，设置独立的轨道 |

`click start operation`：方案预览点开始手术，进入准备。当作一级从「方案预览」切到「准备」。

---

## 二级：准备页任务清单 `PrepareSubStep`

`TKAConsummation`：二级 = 任务清单栏。

| 级别 | 显示名 | 源码 | 日志匹配 |
| --- | --- | --- | --- |
| 2 | 股骨注册 | femur_register | switch to femur register step |
| 2 | 股骨验证 | femur_verify | switch to femur check step |
| 2 | 胫骨注册 | tibia_register | switch to tibia register step |
| 2 | 胫骨验证 | tibia_verify | switch to tibia check step |

注册 / 配准同义，验证 / 配准精度检查同义。显示名跟 spec。

---

## 二级：导航页 `CutterStep` / `CutterNaviStep`

顶栏「导航」下的任务清单（股骨远端 / 胫骨近端 / 四合一 / 各自验证）。

| 级别 | 显示名 | 源码 | 日志匹配 |
| --- | --- | --- | --- |
| 2 | 股骨远端截骨 | femur_distal | switch femur distal step |
| 2 | 胫骨近端截骨 | tibia | switch tibia step |
| 2 | 股骨四合一 | femur_hole | switch femur poster step |
| 2 | 股骨远端验证 | femur_distal_check | switch femur distal check step |
| 2 | 胫骨近端验证 | tibia_check | switch tibia check step |
| 2 | 股骨后方验证 | femur_posterior_check | switch femur poster check step |

股骨远端验证 / 股骨后方验证 / 胫骨近端验证 悬停：验证工具 `collect check` 对比该会话最近一次 `plan`；|Δ| >1 mm 或 1° 标注，>2 mm 或 2° 重点。不改 L1/L2/L3 归属。

---

## 二级：术中评估 ?

日志有截前 / 截后、开始/结束采集、间隙曲线 / 实时模型。源码没有和 PrepareSubStep 同级的 enum。

| 级别 | 显示名 | 日志匹配 | ? |
| --- | --- | --- | --- |
| 2? | 截骨前 | cutter before in gapmeasure page | 算二级 |
| 2? | 截骨后 | cutter after in gapmeasure page | 算二级 |
| 2? | 采集间隙 | start/finish collect gap | 算三级，功能和控件被截骨前和截骨后共用 |

---

## 三级：页内切换

`TKAConsummation::update_third_level_step`：页面内切换（换图等）。准备页还有附加步骤 `PrepareAdditionStep`。

| 级别 | 显示名 | 源码 / 日志 | 说明 |
| --- | --- | --- | --- |
| 3 | 摆锯可视化 | enter/exit saw mode；take over cutter navigation 里的锯模式 | 二级步骤，和没使用摆锯可视化的导航同级 |
| 3 | 胫骨中线绘制 | enter/exit tibia draw line mode | 独立的二级步骤 |
| 3 | 标记钉采集 | PrepareAdditionStep::marker_nail；FmeurReg's marker nail… | 三级步骤 |
| 3 | 髋/踝中心 | hip_or_ankle | 三级步骤 |
| 3 | 示踪器 | tracker | 这些是独立于业务的后台日志，记录设备的运行状态，设置独立的轨道 |
| 3 | 间隙曲线 / 实时模型 | switch show gap curve / realtime model | 只当视图，被截骨前和截骨后共用 |

---

## 还不清楚、请改表

1. 顶栏 `cutter_navigation` 是否就叫「导航」，摆锯只放三级？（源码是这样，和上次备注一致）
2. 登录、方案管理是否和四个手术页画在同一条 L1 轨道？
3. 术中评估的截前/截后算二级吗？
4. 标记钉 / 髋踝 有没有更稳定的日志句，好画三级块？
5. 机械臂维护、设置要不要上轨道？

改本文件后 push，时间轴按表重画轨道。

---

## 手术 vs 软件会话（一天多台、同一台多次启动）

一个 `log_file_YYYY-MM-DD.txt` 是**当天全部记录**，里面经常有：

- 多台手术（不同 `plan uuid`）
- 同一台手术软件重启多次（多次 `Titan Application Startup`，uuid 相同）
- 启动了但没打开方案（只有 Startup/Exit）

样本：`2026-04-22` 同一 uuid 启了 3 次；`2026-07-16` 先同一台重启，再换另一台；`2026-07-29` 上午一台、下午另一台，中间夹了两次空启动。

### 切分

| 单位 | 切分点 | 合并规则 |
| --- | --- | --- |
| 会话 session | `Titan Application Startup` → 下一次 `Exit` 或下一次 `Startup` | 一次进程寿命 |
| 手术 case | 会话里 `start load plan uuid` / `load plan sucess {uuid}` | **相同 uuid 的多个会话合成一台手术** |
| 未打开方案 | 会话里没有 load plan | 单独一段，灰色，不并入任何手术 |

标签用 `loaded plan` 的 brand/series + `operation side`（如 `A / 左`），不把患者姓名写进轨道。

### 时间轴样式

最上方加一条 **手术** 轨道（在一级页面之上）：

- 不同手术：不同底色的长色块（色相轮转，同一 uuid 永远同色）
- 同一手术的多次启动：色块不断开，但内部用竖线切成「第 1 次 / 第 2 次…」，竖线对准 Startup；色块上写 `手术 1 · 3 次启动`
- 未打开方案的空会话：窄灰块，标 `未打开方案`
- 手术与手术之间若有空会话，中间留灰带，不要把两台手术连成一块

一级/二级/三级轨道仍按页走，只是背景跟着当前手术变淡色，换台时轨道背景换色。

Terminal 里会话边界加一行分隔：`── 手术 1 · 第 2 次启动 13:46:39 ──`

?
- 空启动要不要显示在手术轨道上（现在：显示为灰块）
- 同一 uuid 中间隔了另一台手术再回来，算同一台的续上，还是新开一台？（现在：同一 uuid 始终同一台、同一颜色）

---

## 启动 / 版本旗标

`Titan Application Startup`、`Titan vesrion …`（源码拼写）要**特殊标注**，比普通重点更显眼：

- 启动：标尺 + 手术轨道上的旗标，对准该行
- 版本：旗标旁徽章，显示版本字符串，归属该次 Startup
- Terminal 里这两行单独高亮

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
| 1 | 术中评估 | TopNavigation::gap_measure | take over gapmeasure page | |
| 1 | 导航 | TopNavigation::cutter_navigation | take over cutter navigation page **以及** robot motion take over | 顶栏同一级；机械臂截骨和摆锯都在这一页里 |
| — | 机械臂维护 / 相机 / 设置 / 退出 / EMC | robot_maintenance, camera, setting, exit, emc | 日志很少 | ? 要不要上 L1 |

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

---

## 二级：术中评估 ?

日志有截前 / 截后、开始/结束采集、间隙曲线 / 实时模型。源码没有和 PrepareSubStep 同级的 enum。

| 级别 | 显示名 | 日志匹配 | ? |
| --- | --- | --- | --- |
| 2? | 截骨前 | cutter before in gapmeasure page | 算二级还是三级 |
| 2? | 截骨后 | cutter after in gapmeasure page | |
| 2? | 采集间隙 | start/finish collect gap | |

---

## 三级：页内切换

`TKAConsummation::update_third_level_step`：页面内切换（换图等）。准备页还有附加步骤 `PrepareAdditionStep`。

| 级别 | 显示名 | 源码 / 日志 | 说明 |
| --- | --- | --- | --- |
| 3 | 摆锯可视化 | enter/exit saw mode；take over cutter navigation 里的锯模式 | 导航页内功能，不是顶栏一级 |
| 3 | 胫骨中线绘制 | enter/exit tibia draw line mode | |
| 3 | 标记钉采集 | PrepareAdditionStep::marker_nail；FmeurReg's marker nail… | 日志弱 |
| 3 | 髋/踝中心 | hip_or_ankle | 日志更弱 |
| 3 | 示踪器 | tracker | ? |
| 3 | 间隙曲线 / 实时模型 | switch show gap curve / realtime model | ? 三级还是只当视图 |

---

## 还不清楚、请改表

1. 顶栏 `cutter_navigation` 是否就叫「导航」，摆锯只放三级？（源码是这样，和上次备注一致）
2. 登录、方案管理是否和四个手术页画在同一条 L1 轨道？
3. 术中评估的截前/截后算二级吗？
4. 标记钉 / 髋踝 有没有更稳定的日志句，好画三级块？
5. 机械臂维护、设置要不要上轨道？

改本文件后 push，时间轴按表重画轨道。

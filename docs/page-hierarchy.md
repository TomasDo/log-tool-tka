# Titan 页面 / 步骤分级（时间轴轨道用）

> 和 `titan-log-spec.md` 一起驱动工具。显示名以 spec 为准；本文件只定 **一级 / 二级 / 三级** 和轨道该画什么。
>
> 源码依据：`TKAUIStruct.h` 的 `PageIndex`、`TopNavigation`、`PrepareSubStep`、`CutterStep`，以及 `TKAConsummation` 注释（一级进度栏 / 任务清单 / 页内切换）。

## 怎么用在时间轴上

横向时间轴（剪辑器风格）：

- 手术轨道：同一 `plan uuid` 一台手术（多次启动并在一块）
- 主轨道：日志全文（一行一个刻度）
- 一级轨道：登录、方案管理、方案预览、准备、术中评估、导航
- 二级轨道：当前一级页面下的任务清单
- 三级轨道：页内附加采集等
- 设备轨道：维护 / 相机 / 示踪器 / EMC 等后台状态
- 播放头对准原始日志某一行（terminal 跟着滚）

横轴按**日志行号**（不是墙钟）。缩放只用按钮；拖动和滚轮平移。

---

## 壳页面（进 home 之前）

`PageIndex`：`login` / `manage` / `home`。`home` 是四个一级手术页的主窗口，本身不单独占一级轨道。

| 级别 | 显示名 | 源码 | 日志匹配 | 轨道 |
| --- | --- | --- | --- | --- |
| 1 | 登录 | PageIndex::login | from login page switch to plan manage page（离开登录） | L1，从启动到切走 |
| 1 | 方案管理 | PageIndex::manage | from login…plan manage；from home…plan manage | L1 |
| （容器） | 主窗口 | PageIndex::home | from plan manage page switch to home page | 不单独占轨道 |

登录、方案管理和四个手术页画在同一条 L1 轨道上。

---

## 一级：home 顶栏 `TopNavigation`

`slot_first_level_index`。`cutter_navigation` 会同时 `take_over` 截骨器导航页 **和** `TKARobotMotion`（机械臂导航），L1 都叫「导航」。

| 级别 | 显示名 | 源码 | 日志匹配 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 方案预览 | TopNavigation::planviewer | take over planviewer page | |
| 1 | 准备 | TopNavigation::prepare | take over prepare page | 含工具标定、股骨/胫骨注册验证 |
| 1 | 术中评估 | TopNavigation::gap_measure | take over gapmeasure page | 截骨前/后间隙采集评估 |
| 1 | 导航 | TopNavigation::cutter_navigation | take over cutter navigation page **以及** robot motion take over | 机械臂截骨和摆锯都在这一页 |
| — | 机械臂维护 / 相机 / 设置 / EMC | robot_maintenance, camera, setting, emc | 少量后台日志 | 设备轨道，不是手术 L1 |

`click start operation`：方案预览点开始手术，进入准备。当作一级从「方案预览」切到「准备」。

---

## 二级：准备页任务清单 `PrepareSubStep`

| 级别 | 显示名 | 源码 | 日志匹配 |
| --- | --- | --- | --- |
| 2 | 股骨注册 | femur_register | switch to femur register step |
| 2 | 股骨验证 | femur_verify | switch to femur check step |
| 2 | 胫骨注册 | tibia_register | switch to tibia register step |
| 2 | 胫骨验证 | tibia_verify | switch to tibia check step |

注册 / 配准同义，验证 / 配准精度检查同义。显示名跟 spec。

---

## 二级：导航页 `CutterStep` / `CutterNaviStep`

| 级别 | 显示名 | 源码 | 日志匹配 |
| --- | --- | --- | --- |
| 2 | 股骨远端截骨 | femur_distal | switch femur distal step |
| 2 | 胫骨近端截骨 | tibia | switch tibia step |
| 2 | 股骨四合一 | femur_hole | switch femur poster step |
| 2 | 股骨远端验证 | femur_distal_check | switch femur distal check step |
| 2 | 胫骨近端验证 | tibia_check | switch tibia check step |
| 2 | 股骨后方验证 | femur_posterior_check | switch femur poster check step |
| 2 | 摆锯可视化 | saw mode | enter/exit saw mode；take over cutter navigation 里的锯模式 |
| 2 | 胫骨中线绘制 | tibia draw line | enter/exit tibia draw line mode |

验证块悬停：`collect check` 对比该会话最近一次 `plan`；|Δ| >1 mm 或 1° 标注，>2 mm 或 2° 重点。缺 collect 的参数标「未采集」；只做了对应截骨未进验证时，未采集挂在截骨块上。

---

## 二级 / 三级：术中评估

源码没有和 PrepareSubStep 同级的 enum，按日志切：

| 级别 | 显示名 | 日志匹配 |
| --- | --- | --- |
| 2 | 截骨前 | cutter before in gapmeasure page |
| 2 | 截骨后 | cutter after in gapmeasure page |
| 3 | 采集间隙 | start/finish collect gap（截骨前和截骨后共用） |

间隙曲线 / 实时模型只是视图，不画轨道。

---

## 三级：页内附加

| 级别 | 显示名 | 源码 / 日志 | 说明 |
| --- | --- | --- | --- |
| 3 | 标记钉采集 | PrepareAdditionStep::marker_nail；FmeurReg's marker nail… | |
| 3 | 髋/踝中心 | hip_or_ankle | |

示踪器、NDI 断连等到**设备**轨道，不画三级。

---

## 手术 vs 软件会话

一个 `log_file_YYYY-MM-DD.txt` 是当天全部记录：多台手术（不同 uuid）、同一台多次启动、空启动（没打开方案）。

| 单位 | 切分点 | 合并规则 |
| --- | --- | --- |
| 会话 session | `Titan Application Startup` → 下一次 `Exit` 或下一次 `Startup` | 一次进程寿命 |
| 手术 case | `start load plan uuid` / `load plan sucess {uuid}` | **相同 uuid 的多个会话合成一台手术**，即使中间隔了另一台 |
| 未打开方案 | 会话里没有 load plan | 灰色空块，显示在手术轨道上，不并入任何手术 |

标签用 `loaded plan` 的 brand/series + `operation side`（如 `A / 左`），不把患者姓名写进轨道。

### 时间轴样式

- 不同手术：不同底色（色相轮转，同一 uuid 永远同色）
- 同一手术多次启动：色块不断开，内部竖线切成「第 1 次 / 第 2 次…」，对准 Startup
- 手术之间的空会话：灰带，不要把两台手术连成一块

轨道窗口底部 **方案汇总**：每张卡片一台已打开方案的手术，列出必要步骤；点卡片跳到该手术。未打开方案不出卡。

Terminal 会话边界：`── 手术 1 · 第 2 次启动 13:46:39 ──`

---

## 启动 / 版本旗标

`Titan Application Startup`、`Titan vesrion …`（源码拼写）比普通重点更显眼：启动钉在标尺和手术轨道上；版本徽章归属该次 Startup；Terminal 里这两行单独高亮。

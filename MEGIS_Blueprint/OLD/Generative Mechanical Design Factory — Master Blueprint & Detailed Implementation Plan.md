# Generative Mechanical Design Factory
## Master Blueprint & Detailed Implementation Plan

**版本：v1.0 Master Blueprint**  
**定位：Guided Generative Engineering Platform**  
**最終目標：讓零 3D、零材料、零加工、零仿真背景的人，也能透過看圖、選擇、拖放與簡單回答，完成接近資深 ME 團隊水準的產品工程設計。**

---

# 0. 一句話定義

這不是：

- AI Creo
- Text-to-CAD
- Chatbot
- CAD Copilot
- COMSOL Copilot

而是：

> **把資深 Mechanical / Acoustic / Manufacturing Engineer 腦中的工程判斷，變成一套任何新人都能使用的 Guided Engineering System。**

使用者看到的是：

```text
看圖片
↓
選產品
↓
選用途
↓
選喜歡的形式
↓
加入零件
↓
回答幾個白話問題
↓
確認 AI 建議
↓
完成
```

系統底下真正執行：

```text
Product Architecture
↓
Mechanical Layout
↓
Material Selection
↓
Manufacturing Process
↓
Parametric CAD
↓
Tolerance
↓
DFM
↓
Physics / Acoustic Simulation
↓
Optimization
↓
Drawing
↓
BOM
↓
Release Package
```

使用者**不必知道上面任何一個專業名詞**。

---

# 1. 專案最高原則

## 原則 A：永遠假設使用者是完全新人

不設：

```text
Beginner
Engineer
Expert
```

三種模式。

整個產品只有：

> **一種使用者模式：人類模式。**

系統負責適應人，而不是要求人適應工程軟體。

如果工程師想知道更多，可以點：

```text
「為什麼？」
「查看工程依據」
「查看計算」
```

但不需要切模式。

---

# 2. UI 的核心哲學

傳統 CAD 的邏輯：

```text
使用者知道要畫什麼
↓
使用者知道怎麼畫
↓
使用者操作 Sketch
↓
Constraint
↓
Extrude
↓
Fillet
↓
Shell
↓
Pattern
↓
Assembly
```

Generative Mechanical Design Factory：

```text
使用者知道自己想要什麼
↓
系統理解用途
↓
系統決定架構
↓
系統決定零件
↓
系統決定材料
↓
系統決定製程
↓
系統建立 CAD
```

因此：

> **使用者描述「目的」，系統處理「工程手段」。**

---

# 3. 首頁不應該有 Prompt Box

首頁應該像產品型錄。

## 3.1 第一層：我要做什麼？

圖片卡：

```text
聲學產品
├─ Speaker
├─ Microphone
├─ TWS
├─ Headphone
├─ Hearing Device
├─ Bluetooth Speaker
├─ Soundbar
├─ Mic Array
└─ Artificial Head

3C
├─ Laptop
├─ Tablet
├─ Monitor
├─ Dock
└─ Electronic Device

Mechanical
├─ Housing
├─ Fixture
├─ Jig
├─ Bracket
├─ Base Plate
└─ Mechanism

Robot
├─ Robot
├─ Robot Car
├─ Track Robot
├─ Robot Boat
├─ Underwater Vehicle
└─ Sensor Platform

Test
├─ Test Station
├─ Acoustic Fixture
├─ Measurement Fixture
├─ DUT Holder
└─ Calibration Fixture
```

永遠保留：

```text
[ 我不知道是哪一類 ]
```

AI 自動判斷。

---

# 4. 不可以替每一個產品做 Wizard

如果：

```text
TWS = 一套 Wizard
Laptop = 一套 Wizard
Robot = 一套 Wizard
Soundbar = 一套 Wizard
```

產品會很快失控。

真正架構必須是：

# Product DNA Engine

任何產品都由相同的基本元素構成。

```text
Product
=
Envelope
+
Structure
+
Components
+
Interfaces
+
Relationships
+
Environment
+
Manufacturing
+
Physics
+
Constraints
+
Requirements
```

---

# 5. Product DNA

例如：

## ANC TWS

```text
TWS
├─ Housing
├─ Speaker
├─ Front Chamber
├─ Rear Chamber
├─ Vent
├─ Microphone
├─ PCB
├─ Battery
├─ Antenna
├─ Charging Contact
├─ Touch Sensor
├─ Acoustic Mesh
├─ Seal
└─ Ear Interface
```

## Laptop

```text
Laptop
├─ Display
├─ A Cover
├─ B Cover
├─ Hinge
├─ Keyboard
├─ Touchpad
├─ PCB
├─ Battery
├─ Fan
├─ Heat Pipe
├─ Speaker
├─ Microphone
├─ Connector
├─ C Cover
└─ D Cover
```

## Robot Car

```text
Robot Car
├─ Chassis
├─ Wheel
├─ Motor
├─ Motor Mount
├─ Battery
├─ Controller
├─ Sensor
├─ Camera
├─ LiDAR
├─ Microphone
├─ Speaker
├─ Cable
└─ Cover
```

## Robot Boat

```text
Robot Boat
├─ Hull
├─ Motor
├─ Propeller
├─ Rudder
├─ Battery
├─ Electronics
├─ Seal
├─ Sensor
├─ Antenna
└─ Buoyancy Volume
```

所以真正需要建立的不是數千種產品。

需要建立的是：

> **Universal Engineering Module Library。**

---

# 6. Universal Module Library

第一階段可建立約 50 個核心 Module。

例如：

```text
STRUCTURE
Housing
Cover
Plate
Bracket
Frame
Chassis
Shell
Tube
Beam

FASTENING
Screw
Nut
Insert
Boss
Snap
Clip
Adhesive
Latch

ELECTRONICS
PCB
Battery
Connector
USB
Button
LED
Display

ACOUSTIC
Speaker
Microphone
Front Chamber
Rear Chamber
Vent
Port
Mesh
Gasket

THERMAL
Fan
Heat Sink
Heat Pipe
Ventilation

MOTION
Motor
Wheel
Bearing
Shaft
Gear
Hinge

SENSOR
Camera
LiDAR
IMU
Mic Array

HUMAN
Ear
Head
Hand
Finger
Face
Body interface
```

每一個 Module 不是一個 STEP 檔。

它必須包含：

```text
Geometry
Dimensions
Interfaces
Material candidates
Manufacturing rules
Clearance rules
Assembly rules
Physics properties
Failure modes
Validation rules
Cost model
```

---

# 7. Component Library

例如 Speaker：

```text
Speaker Driver
│
├─ Size
├─ Height
├─ Diaphragm
├─ Magnet
├─ Terminal
├─ Mounting
├─ Gasket
├─ Excursion
├─ Frequency response
├─ Fs
├─ Vas
├─ Qts
├─ Sensitivity
└─ Power
```

PCB：

```text
PCB
├─ Outline
├─ Thickness
├─ Keep-out
├─ Mounting hole
├─ Connector
├─ Component height map
├─ Thermal zone
└─ Cable zone
```

使用者可以：

```text
上傳 STEP
上傳 DXF
輸入尺寸
選資料庫零件
```

系統自動建立 Component Metadata。

---

# 8. 新產品的擴充方式

新增產品不應該寫程式。

例如新增：

```text
Security Helmet
```

只新增：

```text
product_dna/security_helmet.yaml
```

內容描述：

```text
Required:
- shell
- liner
- head_interface
- retention

Optional:
- speaker
- microphone
- camera
- battery
- sensor

Constraints:
- human_head_clearance
- impact_zone
- ventilation
- weight_limit
```

UI 自動產生。

因此：

> **Product = Data。**

而不是：

> Product = 新程式。

這就是「無限擴充」成立的關鍵。

---

# 9. Universal Guided UI

整個系統採：

# Dynamic Question Engine

不是固定 Wizard。

系統會根據目前資訊，決定：

> 下一個最值得問的問題是什麼？

---

# 10. 每個問題必須遵守 5 條規則

### ① 優先圖片

不要問：

```text
Housing geometry?
```

而是：

```text
看起來比較像哪一種？

[方盒]
[圓柱]
[薄型]
[曲面]
[異形]
```

---

### ② 一定有 AI Recommendation

例如：

```text
哪種材料？

[AI 推薦]
[塑膠]
[金屬]
[其他]
```

---

### ③ 一定有「不知道」

```text
[不知道，幫我決定]
```

---

### ④ 不問可以推算的東西

不要問：

```text
Wall thickness = ?
```

如果系統知道：

```text
material
process
size
load
```

Wall thickness 應該自動推算。

---

### ⑤ 只有會改變結果的問題才問

這是最重要的 UX 原則。

---

# 11. Question Minimization Engine

每個未知參數有三種狀態：

```text
High confidence
→ AI 自動決定

Medium confidence
→ 顯示 AI 推薦，一鍵確認

Low confidence
→ 問使用者
```

建議：

```text
Confidence ≥ 85%
→ 自動選擇

60–85%
→ AI 推薦

< 60%
→ 詢問
```

這些門檻是產品初始設計值，可由實際資料調整。

---

# 12. 使用者真正看到的流程

## Step 1
你要做什麼？

選圖片。

## Step 2
主要用途？

選：

```text
室內
戶外
可攜
穿戴
水下
測試
工業
```

## Step 3
你比較喜歡哪種樣子？

圖片。

## Step 4
裡面需要什麼？

拖拉：

```text
Speaker
Mic
PCB
Battery
Motor
Sensor
```

## Step 5
你最在乎什麼？

```text
成本
體積
重量
強度
聲音
續航
外觀
防水
```

## Step 6
大約要做幾個？

```text
1
10
100
1,000
100,000
不知道
```

## Step 7
AI 顯示：

```text
我建議：

Material: PC+ABS
Process: Injection molding
Wall: 1.8 mm
Assembly: screws + snap
```

使用者只需要：

```text
接受
或
換一個
```

---

# 13. 材料系統

新人永遠不應該被要求懂：

```text
PC
ABS
PA66 GF30
AL6061-T6
ADC12
SUS304
```

使用者回答：

```text
會不會摔？
有沒有水？
溫度？
戶外嗎？
要不要透明？
重量重要嗎？
成本重要嗎？
```

Material Engine 自己轉成：

```text
Mechanical
Thermal
Environmental
Cost
Manufacturing
Acoustic
```

最後得出：

```text
Candidate 1
Candidate 2
Candidate 3
```

---

# 14. 製程系統

同樣不要問：

```text
CNC or injection molding?
```

而應該問：

```text
數量？
預算？
外觀重要嗎？
最快多久要？
尺寸？
材料？
```

系統自己判斷：

```text
3D printing
CNC
Sheet metal
Injection molding
Die casting
Extrusion
Casting
```

然後顯示：

> AI 推薦 Injection molding。

---

# 15. Geometry Engine

我建議核心採：

```text
Python
↓
CadQuery
↓
OpenCascade
```

CadQuery 原生就是 Python parametric CAD，支援 STEP、STL、DXF 等輸出；底層採 OpenCascade BREP kernel。

目前也值得保留：

```text
build123d
```

作為第二 Geometry Backend。

build123d 同樣基於 OpenCascade，而且 API 更偏現代、typed、composable CAD-as-code，但目前仍在往 1.0 API stability 演進，因此第一正式版我不建議完全押在它上面。

因此：

```text
Geometry Abstraction Layer
├─ CadQuery Adapter
├─ build123d Adapter
├─ OpenCascade Adapter
└─ Future Commercial CAD Adapter
```

---

# 16. 為什麼不能讓 LLM 直接自由畫？

LLM 只能提出：

```text
Design Intent
```

不能直接成為最終真相。

正確流程：

```text
AI proposes
↓
Schema validation
↓
Rule validation
↓
Geometry generation
↓
Geometry validation
↓
Manufacturing validation
↓
Physics validation
↓
Release
```

---

# 17. Design Intermediate Representation

AI 不應直接寫 CadQuery。

中間增加：

# Engineering IR

例如：

```yaml
product:
  type: fixture

envelope:
  x: 120
  y: 80
  z: 35

components:
  - type: pcb
    quantity: 2

interfaces:
  - usb_c

assembly:
  cover: removable

manufacturing:
  process: cnc
  material: aluminum_6061

constraints:
  minimum_wall: 2
```

然後：

```text
AI
↓
Engineering IR
↓
Rule Engine
↓
CAD Generator
```

這比：

```text
Prompt
↓
AI 自由寫 CAD code
```

可靠很多。

---

# 18. Product Constraint Graph

這會成為核心技術之一。

例如：

```text
Speaker
→ must connect → Front Chamber

Front Chamber
→ must connect → Acoustic Outlet

Battery
→ must not collide → PCB

USB-C
→ must intersect → Housing

Microphone
→ requires → Acoustic Path

Wheel
→ requires → Motor / Bearing

Boat electronics
→ requires → Waterproof enclosure
```

產品其實是一張：

> **Engineering Graph。**

---

# 19. Mechanical Rule Engine

每一條工程規則資料化。

例如：

```yaml
rule_id: CNC_MIN_WALL_001

scope:
  process: cnc
  material: aluminum

condition:
  wall_thickness < recommended

severity:
  warning

recommendation:
  increase_wall

source:
  internal_me_standard

version:
  1.2
```

必須保存：

```text
Rule ID
來源
版本
適用材料
適用製程
條件
風險
建議
Auto-fix
```

---

# 20. Know-how Database

至少包含：

```text
Plastic
CNC
Sheet Metal
Die Casting
3D Printing
Assembly
Fastener
Tolerance
Material
Acoustic
Thermal
Structural
Waterproof
EMI
Human Factors
Reliability
```

這才是長期護城河。

---

# 21. 2D Drawing

第一階段可利用：

```text
FreeCAD TechDraw
```

FreeCAD 已經具備專門產生技術圖面的 TechDraw Workbench。

Pipeline：

```text
STEP
↓
FreeCAD headless
↓
Views
↓
Dimensions
↓
Drawing
↓
PDF / DXF
```

之後再逐步增加：

```text
Tolerance
GD&T
Datum
Surface finish
Notes
```

---

# 22. BOM Engine

BOM 不應從 CAD filename 猜。

每個 Module 本身有：

```text
Part Number
Description
Material
Quantity
Supplier
Process
Cost
Weight
Revision
```

所以：

```text
Product Graph
↓
BOM
```

是天然結果。

---

# 23. Cost Engine

初期：

```text
Material Cost
+
Machining Time
+
Process Cost
+
Purchased Parts
+
Assembly Cost
```

後期加入：

```text
Vendor quotation
Historical quotation
Tooling
Yield
MOQ
Logistics
```

成本變成 Optimization objective。

---

# 24. DFM Engine

例如 CNC：

```text
Minimum wall
Tool access
Internal radius
Pocket depth
Thread depth
Hole aspect ratio
Setup direction
```

Plastic：

```text
Wall uniformity
Draft
Rib
Boss
Sink
Undercut
Parting
Gate feasibility
```

Sheet Metal：

```text
Bend radius
Hole-to-bend
K factor
Minimum flange
Flat pattern
```

系統回覆新人：

不要：

```text
Draft angle invalid
```

而是：

> 這個斜度可能造成脫模困難，我已經把側壁調整成較容易量產的形狀。

---

# 25. Physics Engine

AI 不自己算物理。

架構：

```text
AI
↓
Physics Setup Generator
↓
Trusted Solver
↓
Result
↓
AI Interpretation
```

COMSOL 已提供完整 API，官方文件明確指出 geometry、mesh、solver、result evaluation 都可以程式化控制，也可以 headless 執行，因此它很適合先當高可信 Physics Backend。

---

# 26. Acoustic Engine

這是本專案很重要的差異化。

例如 Speaker：

```text
Driver
↓
Front cavity
↓
Outlet
↓
Mesh
```

加：

```text
Rear chamber
Vent
Leak
Gasket
```

自動產生：

```text
Acoustic domain
Boundary
Material
Mesh
Frequency sweep
```

之後 COMSOL：

```text
Solve
↓
SPL
Frequency Response
Pressure field
Resonance
```

再讓 Design Engine 修改：

```text
Chamber volume
Vent diameter
Vent length
Outlet
Geometry
```

---

# 27. Mic Array

使用者不用輸入：

```text
array geometry
beamforming theory
spacing
aliasing
```

問：

```text
要聽哪裡？
距離？
環境多大？
裝置多大？
```

系統產生：

```text
2 Mic
4 Mic
6 Mic
Circular
Linear
Distributed
```

再評估候選。

---

# 28. Generative Design

不要只產生一個答案。

產生：

```text
Design A
Design B
Design C
...
Design N
```

每個 Design 都經過：

```text
DFM
Weight
Cost
Volume
Strength
Acoustic
Thermal
Manufacturability
```

形成：

```text
Score
```

---

# 29. Optimization Engine

第一階段先：

```text
Parameter sweep
DOE
Rule-based search
```

第二階段：

```text
Bayesian Optimization
```

後期：

```text
Evolutionary Optimization
Topology Optimization
Surrogate Model
```

nTop 現在已把「設計意圖 → reusable computational workflow → design space exploration」作為核心產品模式，證明 engineering logic 可以轉成可大量重複執行的運算流程。

---

# 30. 最重要：Validation Engine

AI 產生任何產品後，都必須走：

```text
GATE 1
Schema valid

GATE 2
Geometry valid

GATE 3
No self intersection

GATE 4
No collision

GATE 5
Clearance pass

GATE 6
Manufacturing pass

GATE 7
Assembly pass

GATE 8
Physics pass

GATE 9
Drawing pass

GATE 10
Release integrity
```

只有全部通過：

```text
RELEASED
```

---

# 31. Confidence System

任何 AI 建議都附：

```text
Confidence
```

例如：

```text
Material recommendation
92%

Manufacturing recommendation
89%

Acoustic model confidence
72%
```

如果低於安全門檻：

```text
Need verification
```

---

# 32. 安全關卡

以下產品不能自動宣稱 Production Ready：

```text
Helmet
Medical hearing device
Human safety device
Underwater vehicle
Robot safety structure
Pressure vessel
```

必須：

```text
Engineer Sign-off
或
Certification Required
```

AI 可以完成：

```text
Concept
CAD
Simulation
Prototype
```

但不能跳過法規與驗證。

---

# 33. Browser 3D UI

推薦：

```text
React / Next.js
+
Three.js / React Three Fiber
```

使用者看到：

```text
Rotate
Zoom
Select
Drag
Drop
Move
Resize
```

但所有 Drag 都受 Constraint Engine 控制。

例如使用者拖 Speaker：

```text
Collision
Clearance
Chamber volume
Wall
```

即時更新。

---

# 34. 推薦 Backend

```text
Frontend
Next.js
React
Three.js

API
FastAPI
Pydantic

AI Orchestrator
Python

Engineering IR
JSON / YAML

CAD
CadQuery
OpenCascade

Drawing
FreeCAD

Simulation
COMSOL Adapter

Optimization
SciPy
Optuna

Database
PostgreSQL

Artifacts
File Store / Object Store
```

---

# 35. AI 的定位

LLM 不是 CAD Kernel。

AI 是：

```text
Planner
Requirement Interpreter
Question Generator
Design Architect
Rule Selector
Error Fixer
Result Interpreter
```

確定性的工程工具則是：

```text
Geometry
Math
Physics
Validation
```

---

# 36. AI Agents

內部可拆：

```text
Front Desk Agent
Product Architect
Mechanical Designer
Material Engineer
Manufacturing Engineer
Acoustic Engineer
Simulation Engineer
DFM Engineer
Cost Engineer
Validation Engineer
Release Engineer
```

但是：

> 使用者永遠只看到「一個系統」。

---

# 37. Repository Architecture

```text
GMDF/
│
├─ apps/
│   ├─ web/
│   └─ api/
│
├─ core/
│   ├─ engineering_ir/
│   ├─ product_graph/
│   ├─ constraint_engine/
│   ├─ question_engine/
│   └─ orchestrator/
│
├─ cad/
│   ├─ cadquery/
│   ├─ build123d/
│   └─ occ/
│
├─ product_dna/
│   ├─ acoustic/
│   ├─ electronics/
│   ├─ robot/
│   ├─ fixture/
│   └─ general/
│
├─ modules/
│   ├─ mechanical/
│   ├─ acoustic/
│   ├─ electronics/
│   ├─ thermal/
│   └─ motion/
│
├─ rules/
│   ├─ cnc/
│   ├─ plastic/
│   ├─ sheetmetal/
│   ├─ assembly/
│   ├─ acoustic/
│   └─ material/
│
├─ simulation/
│   ├─ comsol/
│   ├─ acoustic/
│   ├─ structural/
│   └─ thermal/
│
├─ optimization/
│
├─ drawing/
│
├─ bom/
│
├─ costing/
│
├─ validation/
│
├─ release/
│
├─ tests/
│
└─ examples/
```

---

# 38. Release Package

最終每次設計輸出：

```text
PROJECT-0001/
│
├─ requirement.yaml
├─ product_graph.json
├─ engineering_ir.json
│
├─ CAD/
│   ├─ assembly.step
│   ├─ part_001.step
│   └─ model.stl
│
├─ Drawing/
│   ├─ assembly.pdf
│   └─ part_001.pdf
│
├─ BOM/
│   └─ bom.xlsx
│
├─ Simulation/
│   ├─ acoustic/
│   ├─ thermal/
│   └─ structural/
│
├─ Reports/
│   ├─ dfm_report.pdf
│   ├─ tolerance_report.pdf
│   ├─ material_report.pdf
│   └─ simulation_report.pdf
│
└─ release_manifest.json
```

---

# 39. 第一個 Reference Case

原始需求：

```text
120 × 80 × 35 mm
2 PCB
M3
USB-C
Removable cover
CNC aluminum
Minimum wall 2 mm
```

新人 UI：

```text
產品：
[測試治具]

裡面：
[PCB ×2]

需要外部連接？
[USB-C]

需要打開？
[是]

數量？
[1–10]

最在意？
[快速製作]
```

剩下：

```text
Aluminum
CNC
M3
Wall
Clearance
Fillet
Tool radius
```

全部 AI 決定。

---

# 40. 但第一版不要只證明 Box

90 天 MVP 必須證明三種完全不同的產品。

## Case A
CNC Fixture / Enclosure

驗證：

```text
Mechanical
DFM
Drawing
BOM
```

## Case B
Speaker / TWS Acoustic Module

驗證：

```text
Acoustic chamber
Speaker
Mic
Simulation
```

## Case C
Robot Car

驗證：

```text
Assembly
Motor
Wheel
Battery
Sensor
```

如果這三個都能使用同一套 Product DNA Engine：

> 架構才算成功。

---

# 41. P0 — Architecture
## Week 1–2

完成：

```text
Engineering IR
Product DNA Schema
Module Schema
Rule Schema
Constraint Graph
```

不要先做漂亮 UI。

Success：

```text
3 種產品都可以用 JSON 描述。
```

---

# 42. P1 — Guided UI
## Week 3–4

完成：

```text
Product cards
Image choices
Dynamic question
AI recommendation
I don't know button
```

成功標準：

新人不用輸入 CAD 專業詞。

---

# 43. P2 — CAD Engine
## Week 5–6

完成：

```text
Box
Plate
Shell
Hole
Boss
Pocket
Fillet
Chamfer
Cutout
Mount
```

輸出：

```text
STEP
STL
DXF
```

CadQuery 已支援這幾種主要交換輸出格式。

---

# 44. P3 — Module Engine
## Week 7–8

第一批建立：

```text
PCB
Battery
Speaker
Mic
USB-C
Motor
Wheel
Camera
LiDAR
Fastener
```

成功：

拖入 Module 可以自動建立：

```text
mount
clearance
opening
```

---

# 45. P4 — Rule Engine
## Week 9–10

至少：

```text
CNC 50 rules
Plastic 50 rules
Assembly 30 rules
Acoustic 20 rules
```

總計：

```text
150+ deterministic rules
```

---

# 46. P5 — Validation
## Week 11

完成：

```text
Collision
Wall
Clearance
Geometry validity
Basic DFM
```

目標：

> CAD generation success ≥ 90%  
> Known validation case detection ≥ 95%

作為 MVP 工程 KPI。

---

# 47. P6 — Release
## Week 12–13

完成：

```text
STEP
Drawing
BOM
DFM
Release folder
```

到這裡形成：

# 90-Day MVP

---

# 48. 90 天後應該展示的 Demo

使用者：

> 從沒用過 Creo。

5～10 分鐘內：

```text
選 Fixture
↓
選形狀
↓
加入 PCB
↓
加入 USB
↓
按 Generate
```

得到：

```text
STEP
Drawing
BOM
DFM
```

再：

```text
選 Speaker Module
```

得到：

```text
Speaker
Front Chamber
Rear Chamber
Acoustic Simulation
```

再：

```text
Robot Car
```

得到：

```text
Chassis
Wheel
Motor
Battery
Sensor
```

同一套 UI。

---

# 49. 6 個月目標

產品 DNA：

```text
20–30
```

Modules：

```text
100+
```

Rules：

```text
500+
```

支援：

```text
CNC
Plastic
Sheet Metal
3DP
```

Simulation：

```text
Acoustic
Structural basic
Thermal basic
```

---

# 50. 12 個月目標

產品：

```text
100+
```

但產品數量已經不再重要。

更重要：

```text
Product DNA composition
Module reuse
Rule coverage
```

功能：

```text
Automatic architecture
Multi-design
Cost optimization
DFM
Physics optimization
Drawing
BOM
Tolerance
```

---

# 51. 18～24 個月目標

進入真正：

# Generative Engineering

流程：

```text
Need
↓
Generate 100 candidates
↓
CAD
↓
DFM
↓
Physics
↓
Cost
↓
Optimization
↓
Best Pareto designs
```

最後：

```text
Design A
Cheapest

Design B
Lightest

Design C
Best Performance
```

---

# 52. UX KPI

系統不應以：

```text
Feature count
```

衡量 UX。

而應該量：

```text
第一次產生設計需要問幾題？

使用者需要輸入多少工程參數？

有多少問題可以 AI 自己回答？

第一次成功率？

需要人工修 CAD 幾次？
```

建議長期 KPI：

```text
Simple product
≤ 5 分鐘開始生成

Median manual questions
≤ 8

Engineering terminology shown
接近 0

Auto recommendation acceptance
> 70%

Valid first CAD
> 90%
```

---

# 53. AI Learning Loop

每次資深工程師修正：

```text
AI design
↓
Engineer correction
↓
Diff
↓
New Rule / Updated Rule
↓
Regression Test
```

久了以後：

> 系統累積的不是聊天紀錄。

累積的是：

```text
Engineering Knowledge
```

---

# 54. Golden Design Library

建立：

```text
Golden Fixture
Golden Housing
Golden TWS
Golden Speaker Module
Golden Robot
...
```

每次改系統：

```text
1000 個 Golden Case
重新生成
↓
比較
```

防止模型更新讓工程品質退化。

---

# 55. 真正護城河

不是：

```text
GPT
Claude
CadQuery
COMSOL
```

這些別人都能買。

真正 IP：

```text
Product Ontology

Product DNA

Engineering Rule Graph

Component Metadata

Failure Cases

Material Logic

Manufacturing Logic

Acoustic Know-how

Simulation Templates

Golden Designs

Engineer Corrections
```

---

# 56. 與 Creo 的根本差異

Creo 解決：

> 工程師怎麼建模？

你要解決：

> 人想做什麼產品？

完全不同層級。

---

# 57. 與 COMSOL 的根本差異

COMSOL 解決：

> 工程師怎麼建立物理模型？

你要解決：

> 我這個設計需要算什麼？怎麼算？結果代表什麼？

COMSOL 官方本身也透過 Application Builder 推廣把複雜 simulation 包裝成簡單 App，證明「把 solver 隱藏在簡單介面後」是合理方向。

---

# 58. 與 DriveWorks 的差異

DriveWorks 已能做到：

```text
Guided configuration
Rules
Conditional UI
3D visualization
```

而且官方明確支援依先前選項隱藏/顯示 UI，並用規則確保 configuration 滿足技術與製造要求。

你的下一步是：

```text
Configure existing design
```

升級成：

```text
Generate new engineering design
```

---

# 59. 與 nTop 的差異

nTop 的重要觀念是：

> Build processes, not just parts.

也就是把工程邏輯變成 reusable computational workflows。

你的方向再多一層：

```text
User intent
↓
AI constructs engineering workflow
↓
Workflow generates product
```

---

# 60. 最大技術風險

## Risk 1
產品範圍太廣。

解法：

```text
不是限制 Product。

限制最初 Module / Rule coverage。
```

未知產品仍可建立，只是標示：

```text
Coverage 65%
```

---

## Risk 2
AI 幻覺。

解法：

```text
AI ≠ Engineering Truth

Rule + Geometry + Solver
才是真相。
```

---

## Risk 3
CAD 失敗。

解法：

```text
CAD primitives
Design grammar
Parameter bounds
Regression tests
```

不要讓 AI 任意生成 feature tree。

---

## Risk 4
規則互相衝突。

解法：

Rule Priority：

```text
Safety
↓
Physics
↓
Manufacturing
↓
Assembly
↓
Performance
↓
Cost
↓
Appearance
```

---

# 61. 最重要的開發原則

## 不要先打造 AI。

先打造：

```text
Engineering Data Model
```

順序應該是：

```text
Product DNA
↓
Module
↓
Rule
↓
Constraint
↓
CAD
↓
Validation
↓
UI
↓
AI
```

AI 最後串進來，才能可靠。

---

# 62. 建議第一年不要做的東西

不要先做：

```text
Class-A surface
Automotive exterior
Full mechanism synthesis
Complete Mold design
Safety certification automation
Human medical approval
Full Creo compatibility
Full COMSOL replacement
```

不是永遠不做。

而是：

> 不要讓它們拖死核心 Engine。

---

# 63. 最終願景

新人想做：

> 一個戶外 AI Robot。

他只回答：

```text
在哪裡用？
→ 戶外

多大？
→ 桌上型

怎麼移動？
→ 輪子

需要什麼？
→ Camera / Mic / Speaker

續航？
→ 6 小時

防水？
→ 希望可以下雨使用
```

系統自己：

```text
Architecture
↓
Motor
↓
Wheel
↓
Battery
↓
PCB
↓
Sensor
↓
Speaker
↓
Mic
↓
Housing
↓
Seal
↓
Material
↓
Fastener
↓
CAD
↓
Thermal
↓
Acoustic
↓
Structural
↓
DFM
↓
Drawing
↓
BOM
```

---

# 64. 最後的產品本質

這個專案最終不是：

# Generative Mechanical Design Factory

單純「AI 幫人畫 CAD」。

真正應該成為：

# Guided Generative Engineering OS

底層：

```text
          Human Intent
               │
               ▼
        Guidance Engine
               │
               ▼
         Product DNA
               │
      ┌────────┼────────┐
      ▼        ▼        ▼
   Modules    Rules   Knowledge
      └────────┼────────┘
               ▼
       Engineering Graph
               │
               ▼
        AI Engineering
               │
     ┌─────────┼─────────┐
     ▼         ▼         ▼
    CAD     Physics     DFM
     │         │         │
     └─────────┼─────────┘
               ▼
          Optimization
               │
               ▼
           Validation
               │
               ▼
            Release
```

---

# 65. GO / NO-GO

## GO。

但前提是：

不要把專案定義成：

> 「讓 AI 畫 3D。」

而要堅持：

> **「把專業工程決策藏在系統後面，使零背景使用者也能完成高品質工程設計。」**

現有工具已經分別證明必要的底層能力存在：CadQuery / OpenCascade 可以提供 CAD-as-code 與 STEP/STL/DXF；FreeCAD 可以補 technical drawing；DriveWorks 已證明 guided configuration；nTop 已證明 reusable engineering workflow；COMSOL API 已證明 physics workflow 可以自動化。

真正尚未被完整整合起來、也最有產品價值的，就是：

> **Guided UI + Product DNA + Engineering Rules + Generative CAD + Physics + Validation + Optimization。**

這就是這個專案應該建立的核心。
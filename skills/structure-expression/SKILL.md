---
name: structure-expression
disable-model-invocation: false
user-invocable: true
description: >
  用于代码结构设计、实现与重构，让代码阅读结构尽可能对应业务执行结构。
  当设计业务流程、pipeline/workflow、函数组合、Graph、模块入口或控制流抽象，
  或代码出现深层嵌套、流程难以追踪、相关逻辑分散、
  Service/Manager/Handler 过多、修改需要跨多个目录时使用。
  通过执行顺序可读、局部语义内聚、复杂度渐进披露和抽象按需升级控制复杂度。
  本 Skill 提供结构设计原则，不强制采用特定框架、API 或 DSL。
---

# Structure Expression

## 1. Goal

让代码结构本身表达系统设计。

开发者打开一个模块时，应能够快速回答：

1. 这个模块做什么？
2. 主执行流程是什么？
3. 先做什么，后做什么？
4. 哪里存在并行、条件、循环或回退？
5. 某个阶段的实现在哪里？
6. 修改某个能力主要影响哪里？

期望阅读路径：

业务主流程
→ 业务阶段
→ 子流程
→ 领域行为
→ 实现细节
→ 基础设施

这是阅读方向，不是要求每个项目建立全部层级。

## 2. Core Principles

### 执行顺序可读

代码的空间阅读顺序应尽可能对应业务执行顺序。

不要要求读者通过多个文件、类、注册表或 edge 定义，
在脑中重新构造执行流程。

顺序流程重点表达先后关系。
并行流程重点表达并发与汇合关系。
Graph 重点表达节点及其转移、依赖关系。

不能仅靠排列顺序假装非线性执行是线性的。

### 局部语义内聚

相关语义尽可能放在一起。

优先围绕“这个业务能力是什么”组织代码，
而不是围绕“这个对象属于哪种技术角色”。

流程按执行关系表达；
模块按职责、知识归属和共同变化划分。

不要默认把每个步骤拆成独立模块，
也不要为了减少跳转合并无关职责。

### 复杂度渐进披露

顶层只表达主结构，复杂度逐层展开：

workflow
→ named flow / subgraph
→ domain function
→ implementation
→ infrastructure

同一层尽量保持相近的抽象层次。

每次深入都应获得有意义的信息，
而不是只经过一个参数转发层。

### 抽象按需升级

使用能够清晰表达当前问题的最简单抽象。

抽象应至少提供一项价值：

- 表达新的稳定语义；
- 隐藏调用方不需要理解的细节；
- 缩短阅读路径；
- 提高局部内聚；
- 降低修改影响范围。

不要因为未来可能复杂而提前升级。

## 3. Structure First

先识别业务结构，再选择表达方式。

不要先决定创建 Service、Manager、Class、
Fluent API、Graph 或 Workflow Engine。

先回答：

- 主流程是什么？
- 哪些是稳定业务阶段？
- 哪些只是局部实现？
- 哪些逻辑属于同一个业务概念？
- 执行关系和数据依赖是什么？

默认选择：

| 问题 | 优先表达 |
| --- | --- |
| 局部行为、判断、算法 | Function |
| 明确的顺序业务阶段 | Functional Composition |
| 简单局部控制组合 | 两层左右的 Composition |
| 稳定业务子流程 | Named Flow |
| 本质为非线性关系网络 | Graph |
| 大型 Graph | Subgraph / Hierarchical Graph |

这里的 Functional Composition 不要求某个 `pipeline()` API。
普通函数的显式顺序调用如果已经清楚，就不必额外包装。

这不是固定升级链。
Graph 不是比 Composition 更高级的抽象。

## 4. Flow-centric and Node-centric

### Flow-centric

当执行顺序是主要信息时，让主流程连续可读：

```ts
pipeline(
  prepare,
  research,
  verify,
)
```

### Node-centric

当节点及其转移关系是主要信息时，
让节点行为与局部转移一起表达：

```ts
verify: step(verify)
  .next("publish")
  .when(verificationFailed, "repair")
```

两者可以分层组合。
例如顶层表达业务阶段，某个阶段内部使用 Graph。

以上 API 均为表达示例，不要求项目实现同名接口。

## 5. Load References When Needed

根据当前任务加载对应参考。
一个任务涉及多个方面时，可以加载多份；不默认一次加载全部。

### 流程表达

涉及顺序流程、函数组合、局部控制、深层嵌套、
Named Flow 或 Fluent API 取舍时，
在提出具体方案前读取：

[Flow Expression](references/flow-expression.md)

重点保留：

- 普通控制流不是结构问题；
- 两层组合是认知预算；
- 稳定业务概念通过 Named Flow 下沉；
- 不为减少括号制造碎片函数。

### Graph 表达

涉及是否采用 Graph、节点转移、条件路径、
节点复杂度或子图设计时，
在提出具体方案前读取：

[Graph Expression](references/graph-expression.md)

重点保留：

- Node-centric + Local Transition；
- 默认路径与条件偏离语义分开；
- Default First；
- 大型 Graph 使用业务子图渐进披露；
- Human-facing Structure 不等于 Runtime Structure。

### 模块与抽象边界

涉及目录组织、业务归属、技术中间层、
跨模块修改或运行时基础设施时，
在提出具体方案前读取：

[Module Organization](references/module-organization.md)

重点保留：

- 业务能力优先；
- 明确主要阅读入口；
- 不机械地按流程步骤建目录；
- 不增加无语义转发层；
- 不提前搭建基础设施。

参考文档是对应场景下的执行指导，不只是延伸阅读。
项目约束与默认建议冲突时，说明实际收益和代价。

## 6. Existing Project First

进入已有项目时：

1. 理解已有结构和实际调用链；
2. 判断已有抽象是否合理；
3. 优先复用合理结构；
4. 只解决真实存在的结构问题。

不要为了符合本 Skill：

- 创建新的 Pipeline Framework；
- 发明新的 DSL；
- 强制 Graph 化；
- 大规模重构已有合理代码；
- 为统一形式增加无意义抽象。

本 Skill 负责结构表达判断，不代替架构共识。

需要共同澄清需求、模块职责或重大取舍时，
结合 architecture-co-design 的协作方法；
不要为局部调整强制启动完整架构讨论。

讨论设计不等于授权修改。

## 7. LLM Design Procedure

按任务规模裁剪，不机械展示每一步。

### Step 1 — Describe the Business Flow

有代码时，读取相关入口和一条代表性真实调用链。
无代码时，明确样本属于设计假设。

先用业务语言描述：

prepare
→ research
→ analyze
→ verify
→ publish

同时识别关键数据依赖、副作用和失败路径。
不要立即设计 Class。

### Step 2 — Identify Structure Type

判断主要结构属于：

local behavior / sequence / parallel / branch / loop / graph

区分业务结构与实现技术。
根据判断加载对应参考文档。

### Step 3 — Choose the Simplest Representation

优先使用已有的合理表达。

增加 Named Flow、Graph、Subgraph 或模块边界前，
说明它解决了哪个具体理解或修改问题。

### Step 4 — Check Locality

检查理解一个行为是否需要跨多个位置查找。

让行为与相关控制关系尽量局部内聚，
但不要破坏真实职责边界。

### Step 5 — Check Readability

展示必要的顶层调用或局部前后对比。

不进入实现，能否说明主要业务流程？
顶层是否混杂不同抽象层次？
每次深入是否获得有意义的信息？

如果不能，重新组织结构。

### Step 6 — Check Complexity

检查：

- 三层以上组合和明显括号树；
- 单节点大量 transition；
- 巨型 Graph；
- 无业务语义的 Named Flow；
- 多层纯转发对象。

按问题选择 Function、Named Flow、Subgraph 或模块边界，
不要用同一种手段处理所有复杂度。

### Step 7 — Check Abstraction Cost and Change Scope

选择一个高概率变化，推演受影响的位置与契约。
没有真实变化信息时，标明这是验证假设。

检查：

- 相关规则是否集中；
- 无关职责是否被牵连；
- 新抽象是否减少了总理解成本；
- wrapper、service、manager、handler、factory 是否有真实职责。

删除无语义价值的抽象，但保留真实边界。

阅读与变化推演不等于编译、测试或运行验证。

## 8. Preserve Execution Semantics

结构优化不能隐式改变：

- 输入输出和外部契约；
- 数据依赖与副作用顺序；
- 权限、业务校验与安全保护；
- 事务边界；
- 异常传播、超时、取消与重试；
- 并发、幂等与资源生命周期。

例如把顺序调用改为并行执行，属于行为变化，
不能仅以代码更简洁为理由实施。

顶层无需展开所有细节，
但重要执行约束必须能通过接口、命名或邻近说明追踪。

## 9. Review Checklist

按当前任务选用：

- [ ] 顶层能否直接看出业务主线？
- [ ] 阅读顺序是否接近执行顺序，非线性关系是否清楚？
- [ ] Composition 是否控制在两层左右的认知预算内？
- [ ] Named Flow 是否具有真实业务语义？
- [ ] 局部判断是否被不必要地 DSL 化？
- [ ] Graph 是否确实用于非线性关系？
- [ ] Node 与相关 Transition 是否局部内聚？
- [ ] 自定义示例语义中的 `.next()` 是否始终表示默认路径？
- [ ] `.when()` 是否清晰表达条件偏离？
- [ ] 大型 Graph 是否需要拆成业务 Subgraph？
- [ ] 是否存在无意义技术中间层？
- [ ] 修改一个能力是否主要局限在所属模块？
- [ ] 是否为未来扩展提前创建了基础设施？
- [ ] 是否沿用了项目已有的合理抽象？
- [ ] 是否保持既有行为和关键执行语义？

无需为了输出检查清单而逐项向用户汇报。

## 10. Output and Stop Conditions

默认提供：

- 具体结构问题，或无需调整的结论；
- 最小设计样本；
- 主要收益、代价和修改范围；
- 必要的待确认事项与验证状态。

已有结构主线清楚、职责合理、修改集中时，
保持现状是合法结论。

最终优先级：

业务语义
→ 执行顺序
→ 局部内聚
→ 渐进披露
→ 阅读路径
→ 最少必要抽象
→ 扩展能力

不要为了架构感牺牲可读性。
不要为了声明式发明不必要的 DSL。
不要为了 Runtime 方便，让开发者直接阅读 Runtime 数据结构。

最终目标：

开发者能够沿着代码结构，
自然地理解系统是如何运行的。

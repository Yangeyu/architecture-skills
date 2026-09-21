# Graph Expression

本文件用于 Graph 选型、节点转移和层级化 Graph 设计。

以下 DSL 是 Human-facing 表达示例，不要求项目实现。
已有框架的 API 与执行契约优先；
不要根据示例链式调用顺序推断已有框架的行为。

## 1. When to Use Graph

Graph 用于问题本身具有明显非线性关系时，例如：

- 多路径转移；
- 相互关联的回环；
- 条件跳转；
- 多节点依赖；
- 状态迁移；
- 动态执行路径。

存在一个 if 或 loop，不足以证明需要 Graph。

不要仅因为 Pipeline 出现复杂度就立即升级 Graph。
优先考虑 Named Flow + Hierarchical Composition。

当节点及其转移、依赖关系本身成为主要信息时，
Graph 才更自然。

## 2. Node-centric + Local Transition

Human-facing Graph 优先采用：

Node-centric + Local Transition

节点行为与该节点的转移关系放在一起。

```ts
graph("analysis", {
  prepare: step(prepare)
    .next("research"),

  research: step(research)
    .next("analyze"),

  analyze: step(analyze)
    .next("verify")
    .when(qualityInsufficient, "research"),

  verify: step(verify)
    .next("publish")
    .when(verificationFailed, "repair"),

  repair: step(repair)
    .next("verify"),

  publish: step(publish),
})
```

阅读单个节点即可理解：

执行什么
+
默认去哪
+
什么情况下改变路径

例如：

```ts
verify: step(verify)
  .next("publish")
  .when(verificationFailed, "repair")
```

表达：

verify
├── default → publish
└── verificationFailed → repair

## 3. Graph Locality

避免在人工维护的业务表达中，
把 Node 和 Edge 完全分离：

```ts
nodes: {
  verify,
  repair,
  publish,
}

edges: [
  ["verify", "publish"],
  ["verify", "repair", verificationFailed],
  ["repair", "verify"],
]
```

这种结构更接近 Runtime Representation，
但要求开发者跨区域重建节点行为。

Human-facing Graph 优先让：

Node
+
Default Transition
+
Conditional Transition

局部内聚。

这不是禁止底层保存独立 nodes / edges，
也不是要求改写已有框架。

需要全局拓扑视图时，可以生成或提供辅助视图，
避免维护两套互相漂移的事实来源。

## 4. Default Transition

在本文件的示例约定中：

`.next(target)` 表示正常情况下的默认执行路径。

`.when(condition, target)` 表示满足条件时，
偏离默认路径的转移。

```ts
analyze: step(analyze)
  .next("verify")
  .when(qualityInsufficient, "research")
```

理解为：

analyze
├── qualityInsufficient → research
└── default             → verify

默认路径不是“先执行 next，再执行 when”。

不要让 `.next()` 同时承担默认路径、
错误捕获、重试和异常 fallback 等不同语义。

业务结果触发的条件转移，
也不能自动等同于捕获执行异常。

## 5. Default First

节点定义优先先声明主路径，再声明偏离路径：

```ts
step(verify)
  .next("publish")
  .when(verificationFailed, "repair")
```

保持项目内一致。

这样快速扫描 `.next()` 可以看到主路径连接，
继续阅读 `.when()` 才进入条件偏离。

这是阅读约定，不意味着 Graph 一定只有一条线性主链，
也不代表条件判断的执行优先级由声明位置决定。

## 6. Make Transition Semantics Explicit

设计新的 Graph API 时，不能只有好看的调用样例。

至少明确：

- 从哪里开始，如何结束；
- 条件读取节点执行前还是执行后的状态；
- 多个条件同时满足时如何选择；
- 没有匹配条件时是否走默认路径；
- 没有默认路径时，是结束、等待还是错误；
- 执行异常与业务条件转移如何区分；
- 回环如何更新状态、终止或被取消。

本文件示例表达单节点完成后的条件路由意图，
不是一套完整的调度器协议。

已有框架中应依据其真实契约进行设计，
不能擅自套用示例语义。

## 7. Graph Local Complexity

单个节点不应承担大量 transition。

简单：

```ts
step(verify)
  .next("publish")
  .when(verificationFailed, "repair")
```

如果逐渐变成：

```ts
step(verify)
  .next("publish")
  .when(failed, "repair")
  .when(timeout, "retry")
  .when(needsHuman, "review")
  .when(missingData, "research")
  .when(cancelled, "cancel")
```

说明需要检查局部复杂度和语义混杂。

优先判断：

1. 是否可以提取领域决策函数？
2. 是否存在更高层业务状态？
3. 是否应该提取 Subgraph？

不要只是把全部条件藏进一个不透明的 `route()`。
提取后仍应能追踪决策依据及可能目标。

超时、取消等信号是否属于业务路由，
必须由真实执行契约决定，不能仅为统一形式混在一起。

## 8. Hierarchical Graph

大型 Graph 不应通过一个巨大 Node Map 表达。

例如：

analysis
├── 30 nodes
├── 50 transitions
└── multiple loops

节点数量不是机械阈值。
问题是读者是否必须同时理解过多业务概念和转移关系。

将稳定业务阶段提升为 Subgraph：

```ts
graph("analysis", {
  prepare: step(prepare)
    .next("research"),

  research: subgraph(researchFlow)
    .next("analyze"),

  analyze: step(analyze)
    .next("report"),

  report: subgraph(reportFlow)
    .next("publish"),

  publish: step(publish),
})
```

顶层恢复为：

prepare → research → analyze → report → publish

进入 researchFlow 或 reportFlow 后，
再理解内部 Graph。

Subgraph 应具有明确的：

- 业务职责；
- 输入输出；
- 完成及失败方式；
- 对外可见的状态与副作用。

不要按节点数量任意切块，
或通过大量跨子图跳转破坏边界。

## 9. Human-facing Structure ≠ Runtime Structure

不要把 Runtime 最方便的数据结构直接暴露给开发者。

Human-facing 可以是：

```ts
pipeline(
  prepare,
  research,
  verify,
)
```

也可以是：

```ts
graph("analysis", {
  prepare: step(prepare).next("research"),
  research: step(research).next("verify"),
  verify: step(verify),
})
```

底层可以统一转换为：

Workflow Definition
→ Graph IR
→ Scheduler / Runtime

Human-facing Representation 和 Runtime Representation
是两个不同的设计问题。

优先保证业务代码可读，
再让 Runtime 使用适合执行的数据结构。

“可以转换为 Graph IR”不意味着必须创建 IR 或 Runtime。
仅在真实需求出现时引入。

## 10. Graph Review

检查：

- Graph 是否比函数与 Named Flow 更自然？
- 单个节点的行为和转移能否一起理解？
- 默认路径与条件偏离是否明确？
- 条件优先级和失败语义是否真实确定？
- 主路径连接能否快速扫描？
- 是否有难以理解的高复杂度节点？
- 子图是否对应稳定业务阶段？
- 是否把 Runtime 的便利转嫁成业务阅读成本？

Graph 的目标不是显得更强大，
而是让本来就非线性的业务关系更容易理解。

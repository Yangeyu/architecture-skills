# Flow Expression

本文件用于顺序流程、函数组合、局部控制和 Named Flow 设计。
以下 API 为表达示例，不是要求项目实现的框架接口。

## 1. Local Logic → Function

局部行为、判断、算法和循环优先使用普通函数。

```ts
async function resolveResult(ctx) {
  const result = await infer(ctx)

  if (hasToolCalls(result)) {
    return executeTools(result)
  }

  return complete(result)
}
```

正常的 if、switch、for、return、try/catch 不是结构问题。

不要为了声明式消灭普通控制流。
如果普通函数已经最清楚，就使用普通函数。

## 2. Sequential Flow → Functional Composition

具有明确业务阶段的流程，优先让阶段连续组合：

```ts
const analysis = pipeline(
  prepare,
  research,
  analyze,
  verify,
  persist,
)
```

阅读顺序就是：

prepare → research → analyze → verify → persist

也可以通过显式调用表达：

```ts
async function analysis(input) {
  const context = await prepare(input)
  const evidence = await research(context)
  const result = await analyze(evidence)
  const verified = await verify(result)
  return persist(verified)
}
```

选择依据是流程和数据传递是否清楚，
不是是否使用了 `pipeline()`。

项目已有合理机制时，可以使用少量稳定结构原语：

- pipeline；
- parallel；
- branch；
- loop。

不要为了应用本 Skill 创建 Workflow Framework。

## 3. Two-Level Composition Budget

默认最多使用两层清晰的函数组合。

```ts
const analysis = pipeline(
  prepare,

  parallel(
    researchWeb,
    researchDatabase,
  ),

  analyze,
  persist,
)
```

可以直接理解为：

prepare
→ [researchWeb + researchDatabase]
→ analyze
→ persist

两层是认知复杂度预算，不是机械的括号计数。

核心判断：

阅读当前代码时，能否直接理解执行结构，
而不必同时追踪多套嵌套控制规则？

不要通过机械提取碎片函数来满足数字要求。

## 4. Avoid Deep Composition

避免让组合形成明显括号树：

```ts
pipeline(
  prepare,

  loop(
    pipeline(
      infer,

      branch(hasToolCalls, {
        true: executeTools,
        false: complete,
      }),
    ),
  ),

  persist,
)
```

按顺序判断：

1. 是否存在值得命名的稳定业务子流程？
2. 是否应该让局部逻辑回归普通函数？
3. 问题是否本质上已经是非线性关系网络？

不要仅因为括号变多就立即采用 Graph。

## 5. Named Flow

当一组行为形成稳定业务概念时，提取 Named Flow。

```ts
const agentExecution = loop(
  agentIteration,
  { until: completed },
)

const workflow = pipeline(
  prepare,
  agentExecution,
  persist,
)
```

局部复杂度继续下沉：

```ts
async function agentIteration(ctx) {
  const result = await infer(ctx)

  if (hasToolCalls(result)) {
    return executeTools(result)
  }

  return complete(result)
}
```

顶层保持：

prepare → agentExecution → persist

进入 agentExecution 后才理解 Agent 内部行为。

Named Flow 是业务层级，不要求特殊类型、基类或运行时。
普通函数也可以承担 Named Flow。

### Naming

推荐：

- research；
- contextPreparation；
- agentExecution；
- verification；
- reportGeneration。

避免：

- innerFlow；
- subPipeline；
- flow1；
- processFlow；
- handlerFlow。

提取前检查：

- 是否能用稳定业务语言解释它？
- 调用方是否无需理解内部步骤？
- 深入后是否能获得一个完整子流程？
- 是否只是为了减少括号或转发参数？

不要为了拆分而创建无语义 Named Flow。

## 6. Hierarchical Composition Before Graph

复杂流程优先考虑：

Named Flow + Hierarchical Composition

如果普通函数和有业务名称的子流程已经清楚，
就不需要把整个流程改成 Graph。

只有当节点及其转移关系更自然地表达问题时，
才读取 [Graph Expression](graph-expression.md) 并评估 Graph。

## 7. Fluent API

Fluent 不是默认结构表达原则。

不要因为追求声明式而主动创建：

```ts
workflow()
  .then(...)
  .when(...)
  .parallel(...)
  .then(...)
```

如果 Functional Composition 更直接，就使用它。

Fluent 更适合：

- Configuration；
- Builder；
- Incremental Construction；
- Node-local Graph Transition。

例如：

```ts
step(verify)
  .next("publish")
  .when(verificationFailed, "repair")
```

这里 Fluent 有价值，
因为相关 transition 属于同一个 Node。

判断标准：

是否让相关语义更加局部和连续？

而不是：

是否可以使用链式 API？

## 8. Execution Contract Check

采用组合机制时，确认已有实现如何处理：

- 阶段输入输出；
- 并行结果汇合；
- 分支返回；
- 循环状态更新与退出；
- 错误、取消和重试。

不能根据 API 名称猜测执行语义。

以上循环示例只表达结构；
实际实现必须有明确的完成条件及适用的终止保护。

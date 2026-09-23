# Flow Expression

以下是结构样例，不是待实现的框架。业务类型与能力契约沿用项目定义；
后续片段展示已绑定依赖后的内部行为，不要求拼接成同一文件。

## 1. 一个流程同时表达阶段、数据与策略

假设报告输入包含 `topic`、`requirements`、`format`，研究允许对约定的可恢复错误使用缓存。
`ReportInput`、`ReportCapabilities` 表示已有业务类型，此处省略类型声明，集中展示阅读结构：

```ts
function createReport({
  prepareQueries,
  research,
  readCachedEvidence,
  analyzeEvidence,
  renderReport,
}: ReportCapabilities) {
  return function generateReport(input: ReportInput) {
    const flow = pipeline(
      prepareQueries,

      // 缓存回退是本流程的策略，不是 research 隐含的行为。
      withFallback(research, readCachedEvidence),

      evidence => analyzeEvidence(evidence, input.requirements),
      analysis => renderReport(analysis, input.format),
    )

    return flow(input.topic)
  }
}
```

这个样例同时落实四件事：

- 创建入口显式绑定外部能力，行为内部保留完整阶段。
- 匿名函数与闭包让附加参数在使用处可见，无需把所有数据塞入统一 Context。
- 回退策略在对应阶段可见，策略内部实现继续下沉。
- 空行区分获取证据与后续处理，注释补充策略归属，不逐行复述代码。

这里假设 `pipeline` 类型安全且支持异步：依次等待完成，将结果传给下一阶段，失败则停止并传播。
`research` 与缓存读取都接收查询并返回相容证据；仅约定的可恢复研究错误触发回退，
取消、权限失败不在回退范围，缓存失败继续传播。这些是样例契约，不是 API 名称自带的保证。

参数不同不是放弃组合的理由；保持真实签名，在需要的阶段就地衔接。
若衔接代码淹没阶段或难以如实表达资源边界，再在对应局部采用显式调用。
策略包装承载实际执行意义，不是应删除的无语义转发；也不必给每个调用添加包装。

## 2. 沿阅读路径继续展开

进入上例的 `research`，继续看到检索与汇合，而不是一个不透明的通用执行器：

```ts
const research = pipeline(
  parallel(
    searchWeb,
    searchDatabase,
  ),

  mergeEvidence,
)
```

两路检索接收相同查询，输出各自的证据；`mergeEvidence` 接收汇合结果，不依赖隐式共享状态。
进入 `searchDatabase` 后，仍可按阶段展开：

```ts
const searchDatabase = pipeline(
  buildDatabaseQuery,
  fetchDatabasePages,

  parseDatabaseRecords,
  deduplicateEvidence,
)
```

再进入分页实现时，用清楚的局部循环表达分页状态和退出条件。
组合与普通函数都可出现在各层，不规定“顶层组合、内部命令式”。
有完整业务含义的子流程即 Named Flow；名称帮助展开，不自动要求新文件、基类或运行时。

并发之前确认任务确实独立、可共享哪些输入，以及副作用是否冲突。
明确结果如何对应任务、何时汇合、并发数量，以及失败后其他任务是继续、等待还是取消。
`Promise.all` 拒绝后不会自动取消其他任务；`parallel` 也不能仅凭名字推断有取消或限流能力。

## 3. 局部控制保持平坦

避免让多层 `if / for` 或组合括号树承载所有细节。
用卫语句排除例外，用完整子行为承接内层工作，而不是把原嵌套原样搬进新名字：

```ts
async function publishReadyReports(reports) {
  for (const report of reports) {
    if (!report.ready) continue

    // 必须逐份等待提交，保持既有发布顺序。
    await publishReport(report)
  }
}

async function publishReport(report) {
  if (!canPublish(report)) return

  const rendered = await renderReport(report)
  await persistReport(rendered)
}
```

集合遍历与单份报告的完整行为分别可读。浅层卫语句不等于多层控制树；
展平时保留校验顺序、副作用与清理，特别注意 `return`、`continue`、`break` 的作用范围。

同样，Agent 循环可将一次推理及结果处理命名为 `agentIteration`，父层只表达重复与退出：

```ts
const agentExecution = loop(
  agentIteration,
  { until: completed },
)
```

深入 `agentIteration` 后仍应看清推理、工具调用或完成判断。
循环必须有真实的状态推进、完成条件与适用的终止保护，不能靠命名隐藏控制复杂度。
业务层级可以继续展开，不把避免嵌套变成目录或调用链的固定层数限制。

## 4. 选择工具并核对执行契约

`pipeline`、`parallel`、`branch`、`loop` 分别表达顺序、并发、条件与重复，名称服从项目实际 API。
节点及其转移成为主要信息时，读取 [Graph Expression](graph-expression.md)，而非按括号数升级 Graph。
Fluent 可用于让组合、配置或转移更局部连续，不以链式外观决定设计。

采用工具或调整表达时，按实际实现检查：

- 输入输出类型、异步完成值与跨阶段依赖；
- 分支返回、循环状态和退出，策略适用范围与失败传播；
- 并发汇合、在途任务处理、超时、取消、重试与补偿；
- 副作用顺序、事务、资源所有权与清理。

保留闭包捕获值的生命周期与可变性约束，不用类型断言或无语义适配掩盖不兼容。
移出原有策略须保持行为；新增回退、改变重试或将顺序改为并行属于行为变化。

优先复用已有能力，缺少支撑时可提供所需的最小组合工具，并验证其承诺的契约。
组合支撑不等于调度、持久化或恢复运行时；普通函数或现有库足够时，就停在那里。

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

## 2. 主流程用组合，策略用链式，业务路径显式分支

以下独立场景由研究流程内部准备查询，不与上一节接收查询的 `research` 直接互换。
只对网络检索设置超时、重试和缓存策略；合并后，证据不足则补充一次检索：

```ts
const research = pipeline(
  prepareQueries,

  parallel(
    policy(searchWeb)
      .timeout(5_000)
      .retry({ maxAttempts: 3 })
      .fallback(readWebCache)
      .build(),

    searchDatabase,
  ),

  mergeEvidence,

  branch(needsMoreEvidence, {
    then: supplementEvidence,
    else: evidence => evidence,
  }),
)
```

主流程用 `pipeline` 扫描阶段，同一任务的多策略用 Fluent 展开，优于多层 `withFallback(withRetry(...))` 包装。
策略就放在相关任务旁边，不为了单纯缩短主流程而另起 `resilientSearchWeb` 等别名；完整业务子流程仍可独立命名。
业务条件优先用 `branch` 展示路径；标题整理等局部计算，普通函数与组合都可接受。

样例假设策略链每一步包装前面的行为，`build()` 返回阶段函数：单次尝试超时 5 秒，
对约定可恢复错误最多尝试 3 次，耗尽后用同一查询读取缓存；取消、权限错误直接传播，缓存失败也传播。
数值只属于此假设场景，不能套用到其他业务。核对超时是否中止在途任务，不能把 Promise 拒绝视为资源已清理。

两路检索接收相同查询；`mergeEvidence` 接收按来源对应的汇合结果，不依赖隐式共享状态。
`branch` 根据合并证据只执行选中的一个分支，两路都返回相容的证据类型，失败向外传播。
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

## 3. 当前阅读单元不出现第三层嵌套

用户认可上一节的信息密度，边界是最多两层组合/控制嵌套：

- `pipeline` 是第一层，内部并列的 `parallel`、`branch` 是第二层。
- 平直的策略链与 `{ maxAttempts: 3 }` 等参数配置不是新增控制层；函数定义本身也不计入。
- 匿名函数不豁免内部控制流：其中继续出现的 `if / for` 或组合结构仍要计层。
- 若写成 `pipeline → parallel → pipeline`，把内层完整检索行为命名为子流程，父层引用它；
  深入子流程后仍遵守当前阅读单元的边界。不要仅为了计数创建无语义转发或把嵌套藏在配置里。

这个限制针对局部理解负担，不是全系统只能有两层目录或调用。
普通控制流同样避免多层 `if / for` 交织，用卫语句排除例外，用完整子行为承接内层工作：

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
默认由函数组合表达主流程，由就地 Fluent 链表达多策略；节点转移也可用 Fluent 保持局部性。
表达偏好不替代执行契约，也不要求新建一套同名 API。

采用工具或调整表达时，按实际实现检查：

- 输入输出类型、异步完成值与跨阶段依赖；
- 分支返回、循环状态和退出，策略适用范围与失败传播；
- 并发汇合、在途任务处理、超时、取消、重试与补偿；
- 副作用顺序、事务、资源所有权与清理。

保留闭包捕获值的生命周期与可变性约束，不用类型断言或无语义适配掩盖不兼容。
移出原有策略须保持行为；新增回退、改变重试或将顺序改为并行属于行为变化。

优先复用已有能力，缺少支撑时可提供所需的最小组合工具，并验证其承诺的契约。
组合支撑不等于调度、持久化或恢复运行时；普通函数或现有库足够时，就停在那里。

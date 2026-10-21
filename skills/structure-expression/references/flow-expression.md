# Flow Expression

阅读或编写每一级行为时，先判断它是在组织多个业务阶段，还是在完成局部算法或具体操作：
前者优先用函数组合展开顺序、并发、分支与重复，后者直接实现。进入子流程后继续作同样判断。
以下片段展示数据衔接、策略和语义留白，业务类型与能力契约沿用项目定义；
依赖已在组装时绑定，不要求将所有片段拼成同一文件或实现一套框架。

## 1. 跨阶段复用数据：可变 Context 累积状态

当后续阶段需要同时使用证据、分析等多个中间结果时，优先用流程 Context 承载。
串行阶段原地更新自己负责的字段，再返回同一个对象，而不是反复包装或 `{ ...ctx }` 复制：

```ts
// 片段中的 search、analyzeEvidence 等外部能力已在组装时绑定。
async function research(ctx: ReportContext) {
  ctx.evidence = await search(ctx.queries)

  return ctx
}

async function analyze(ctx: ReportContext) {
  ctx.analysis = await analyzeEvidence(
    ctx.evidence,
    ctx.input.requirements,
  )

  return ctx
}

const report = pipeline(
  prepareQueries,
  research,

  analyze,
  render, // 读取证据和分析结果，写入 ctx.output，再返回 ctx。
)

function generateReport(input: ReportInput) {
  return report(createReportContext(input))
}
```

此处阶段契约是读取已有字段、写入阶段结果并返回 Context；`pipeline` 仍只传递阶段的实际返回值，
不能假设返回 `void` 的阶段会自动保留 Context。每次执行创建自己的实例，避免请求间状态串扰。
`ReportContext`、初始化函数及阶段类型沿用真实业务定义；字段何时可读、由谁写入必须可追踪，
用类型或明确前置检查保证，不靠全部可选字段和非空断言掩盖错误顺序。

这是一种流程状态表达，不是让所有领域共用一个万能对象，也不改变外部依赖的显式注入方式。
重试、回退可能看到失败阶段留下的状态，应明确本阶段结果的写入时机及需要重置的字段，不能假设自动回滚。

### 并发先收集，成功汇合后集中写入

以下片段展开一次来源收集行为。分支只读所需输入、返回自己的结果，不直接修改共享 Context：

```ts
async function collectSources(ctx: ResearchContext) {
  const [web, database] = await Promise.all([
    searchWeb(ctx.queries),
    searchDatabase(ctx.queries),
  ])

  // 两路都成功后，才写入本组结果。
  ctx.webEvidence = web
  ctx.databaseEvidence = database

  return ctx
}
```

任一路失败时，不执行这组字段写入；之前阶段已写入的状态与外部副作用不会因此回滚。
`Promise.all` 也不会自动取消其他任务。使用 `parallel` 时遵守同一数据约定：先取得汇合结果，
再显式写入并返回本次 Context，不能把结果数组直接当作 Context 或假定工具会替你合并。

### 简单数据流仍可直接衔接

下面是独立的直接传值样例，各阶段只需要上一步结果和原始输入，不需要保留全部中间结果。
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

- 创建入口绑定稳定的业务能力，报告依赖完整的 research，不承担其内部来源的组装；行为内部保留完整阶段。
- 匿名函数与闭包让原始输入的附加参数在使用处可见；需要复用多个中间结果时采用前述 Context 形式。
- 回退策略在对应阶段可见，策略内部实现继续下沉。
- 查询准备和研究同属获取证据，连续排列；空行将它们与分析、渲染区分，注释说明缓存策略归属。

这里假设 `pipeline` 类型安全且支持异步：依次等待完成，将结果传给下一阶段，失败则停止并传播。
`research` 与缓存读取都接收查询并返回相容证据；仅约定的可恢复研究错误触发回退，
取消、权限失败不在回退范围，缓存失败继续传播。这些是样例契约，不是 API 名称自带的保证。

创建函数返回执行函数用于区分依赖绑定与业务调用，不要求每个子流程都采用工厂形式；
直接参数或现有闭包已经表达清楚时沿用即可。日志的应用配置与单次执行关联见第 4 节。

保持真实签名，在阶段衔接处表达参数关系。组合若需要反复搬运参数或遮住资源边界，
先检查行为契约，再在相应局部使用清楚的直接实现。策略包装应承担真实执行语义。

## 2. 各层组合阶段，策略与业务路径就地展开

以下独立场景由研究流程内部准备查询，不与上一节接收查询的 `research` 直接互换。
只对网络检索设置超时、重试和缓存策略；合并后，证据不足则补充一次检索，记录最终证据数量。
业务能力已绑定，logger 来自应用统一日志入口，导入路径仅为示意：

```ts
import { logger } from "./logging"

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

  tap(evidence =>
    logger.info({
      event: "research.completed",
      count: evidence.length,
    }),
  ),
)
```

这里依次展开查询准备、并发检索、证据整理与事实记录。合并与按需补充共同完成证据整理，
相邻排列；意图转换处留白。网络策略紧邻对应任务，逐行呈现作用域与顺序。
`branch` 显式表达补充路径；标题 trim 和默认值这类字段计算直接写在所属函数内。

样例约定 `build()` 返回阶段函数：单次尝试超时 5 秒，对约定可恢复错误最多尝试 3 次，
耗尽后用同一查询读取缓存；取消、权限错误直接传播，缓存失败也传播。
数值只属于此假设场景，不能套用到其他业务。核对超时是否中止在途任务，不能把 Promise 拒绝视为资源已清理。

两路检索接收相同查询；`mergeEvidence` 接收按来源对应的汇合结果，不依赖隐式共享状态。
`branch` 根据合并证据只执行选中的一个分支，两路都返回相容的证据类型，失败向外传播。

进入 `searchDatabase` 后，继续用组合展开获取与处理两个区段：

```ts
const searchDatabase = pipeline(
  buildDatabaseQuery,
  fetchDatabasePages,

  parseDatabaseRecords,
  deduplicateEvidence,
)
```

继续进入 `fetchDatabasePages`，检查游标推进、退出条件与资源释放，用局部循环直接实现。
若分页中还混有鉴权、业务补全或持久化等完整阶段，先明确它们的执行边界，再按实际关系组合。
这条阅读路径在具体操作处结束，不能停在 `research` 或 `searchDatabase` 的名称上；
行为命名、文件拆分和是否需要组合分别判断。

并发之前确认任务确实独立、共享输入是否保持只读，以及外部副作用是否冲突。
本节采用返回值汇合；若衔接可变 Context，遵循第一节的集中写入方式。
明确结果如何对应任务、何时汇合、并发数量，以及失败后其他任务是继续、等待还是取消。
`Promise.all` 拒绝后不会自动取消其他任务；`parallel` 也不能仅凭名字推断有取消或限流能力。

## 3. 当前阅读单元不出现第三层嵌套

局部组合与控制最多嵌套两层，复杂度沿完整行为展开：

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

## 4. 日志：统一能力、作用域上下文与业务事实

日志参与架构设计，先明确要回答的业务或排障问题，再选择产生位置与交付语义：

| 内容 | 归属与表达 |
| --- | --- |
| 格式、级别、输出后端 | 应用或运行时统一配置，模块使用统一日志入口 |
| 事件含义、数量与决策依据 | 业务行为直接记录，或用 tap 观察中间值 |
| 耗时、执行状态与失败 | 有价值的操作边界，复用观察包装、执行钩子或 Span |
| requestId、runId 与分支字段 | 执行入口建立作用域，内部读取当前上下文，并发扩展保持隔离 |
| 必须持久化的操作记录 | 业务步骤或事务，明确失败与交付保证 |
| 随计算返回的解释 | 计算结果，需要组合累积时可使用 Writer |

### 应用共享日志入口，执行作用域隔离关联字段

应用级 logger 可以共享，不需要作为每个业务函数的参数。
单次执行字段保存在异步或 Fiber 作用域中，日志入口在调用时读取；
应用共享配置与请求隔离是两种生命周期，不能把当前 requestId 写入共享 logger 的可变字段。
已有上下文机制时直接复用；跨进程或消息边界需要显式传递关联信息并在接收端建立作用域。

沿用第 2 节的研究行为，边界观测在组装时绑定，本次关联在执行入口建立：

```ts
import { observe, withLogContext } from "./logging"

const observedResearch = observe("research", research)

function runResearch(topic: string, runId: string) {
  return withLogContext({ runId }, () => observedResearch(topic))
}
```

`observe`、`withLogContext` 表示项目的观测与作用域能力，不要求引入这些名称的框架。
本例约定后者在回调及其异步调用链内提供关联字段，返回回调结果，并与其他执行隔离；
`observe` 与业务中的 logger 使用同一上下文。日志入口在每次记录时读取当前作用域，
不在流程组装时捕获某个请求的 logger，因此同一流程可以并发复用。

并发分支需要来源等附加字段时各自扩展作用域，不修改共享标签对象；
业务 Context 继续保存业务中间结果，不承担日志服务和关联字段的逐层传递。
可复用库、独立运行实例或宿主要求不同日志实现时，可通过模块边界注入；
缺少作用域能力且显式传递更清楚时也可采用该方式，不机械禁止注入或为此重建流程。

### tap 记录事实，边界观测记录执行

第 2 节的 tap 等待日志回调完成、忽略其返回值，再传递原 evidence，回调不修改业务数据。
它观察成功值，不能代替失败、取消和完整耗时观测；直接调用 logger 仍是副作用，
采用 IO／Effect 模型时由对应运行时执行，函数组合本身不保证纯函数。

边界观测从实际调用开始覆盖异步生命周期，记录最终状态与耗时，返回原结果或传播原错误。
支持取消的项目需保留其独立语义。tap 和观察包装不自动隔离日志失败：
普通诊断输出由日志适配层确定失败策略，本例约定其失败不覆盖业务结果。
异步缓冲、刷新和退出处理按后端契约决定，排队不等于可靠送达。

策略外的观测记录重试与回退后的最终结果；单次尝试在策略内部观测。
重试、回退事实由策略执行处记录，携带阶段与 attempt 等信息，业务提供错误分类。
第一次尝试失败而第二次成功，应能区分尝试失败与阶段成功，耗时范围与边界一致。
同一错误由负责最终报告的边界完整记录，内部只补充有价值的事实，避免层层重复堆栈。

### 可靠记录与计算说明

审批及审计必须一起保存时，使用 validateApproval → persistApprovalWithAudit 等显式业务流程，
由持久化行为承担事务保证；跨系统记录按实际交付与恢复契约设计。
普通诊断日志、tap 和 Writer 都不能代替这些保证。
返回给用户的规则解释可以随计算结果返回，需要组合累积时再采用 Writer，
无需把运行日志全部累积到业务返回值里。

这些选择可参考 [Effect 的日志作用域](https://effect.website/docs/v4/observability/logging)、
[Node.js 的异步上下文日志示例](https://nodejs.org/api/async_context.html#class-asynclocalstorage) 与
[log4cats 的能力注入](https://typelevel.org/log4cats/#logging-using-capabilities)。按项目运行模型选择，
不从某个社区实现推导出所有模块必须使用同一种接入方式。

## 5. 选择工具并核对执行契约

`pipeline`、`parallel`、`branch`、`loop` 分别表达顺序、并发、条件与重复，名称服从项目实际 API。
节点及其转移成为主要信息时，读取 [Graph Expression](graph-expression.md)，而非按括号数升级 Graph。
阶段、策略和节点转移的表达选定后，按工具的真实实现核对执行语义。

重点检查：

- 输入输出类型、异步完成值与跨阶段依赖，Context 的字段读写前提及每次执行的隔离；
- 分支返回、循环状态和退出，策略作用于单次尝试还是整个操作、组合顺序及失败传播；
- 并发汇合、在途任务处理、超时、取消、重试与补偿；
- 副作用顺序、事务、资源所有权与清理；
- tap 的异步等待与保留值、日志上下文传播与并发隔离、记录失败策略和可靠交付要求。

保留闭包捕获值的生命周期与可变性约束，不用类型断言或无语义适配掩盖不兼容。
移出原有策略须保持行为；新增回退、改变重试或将顺序改为并行属于行为变化。

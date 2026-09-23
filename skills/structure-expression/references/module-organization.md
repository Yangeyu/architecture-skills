# Module Organization

用两个场景区分：**需要立即表达的语义边界**，以及**随信息密度调整的内部细分**。

## 1. 命令系统：机制与成员从一开始分开

```text
commands/
├── index.ts                 # 选择成员并绑定依赖
├── contracts.ts             # 必要的共同契约
├── catalog.ts               # 发现、匹配、帮助与补全
├── dispatch.ts              # 公共执行协调
└── builtins/                # 可增长的内置命令集合
    ├── copy.ts              # 简单但完整的成员
    └── export/              # 内部有多个实质组成的成员
        ├── index.ts         # 定义与完整流程
        ├── markdown.ts
        └── html.ts
```

`commands/` 父层表达相对稳定的系统组成，`builtins/` 承载增长的具体命令。
即使只有少量命令也保留集合边界；必要组装或公共契约仍可随真实需求变化。
读整体看父层与组装，读管理规则看机制，读某个命令直接进入成员。

`copy.ts` 与 `export/` 都是完整成员，不必统一成目录。成员应集中元数据、参数解释和行为，
避免散成定义表、动作表和多层装配回调。外部动态命令可沿已有来源接入；别名不必另建成员。
此样例不要求普通模块都具备 catalog、dispatch 或独立契约文件。

## 2. 报告研究：完整能力先分层，内部细分看密度

```text
reports/
├── generate.ts
├── research/
│   ├── index.ts             # 研究流程与短小局部函数
│   ├── search-web.ts
│   └── search-database.ts
└── render.ts
```

`research/` 揭示报告的一项组成，并提供集中阅读和扩展的位置，不只是减少根目录文件。
内部只有少量组成时，不必立刻增加 `sources/`。来源增多、混排妨碍扫描时，再整理为：

```text
research/
├── index.ts
└── sources/
    ├── web.ts
    ├── database.ts
    ├── documents.ts
    └── archive.ts
```

这次展开的收益是降低当前层的信息密度，不是达到某个文件数阈值。
短小、局部使用且没有独立扩展预期的 `prepareQueries`、`mergeEvidence` 可留作同文件函数；
有实际独立职责或丰富实现时再拆分。**值得命名的步骤，不等于值得独立定位的成员。**

## 3. 通过显式依赖组装成员

外部协作在组装入口连接，成员保留完整行为。以下假设对话能力提供可复制文本，
已有异步 `pipeline` 依次传递结果并传播失败：

```ts
// commands/builtins/copy.ts
type CopyDependencies = {
  readConversation: (id: string) => Promise<string>
  writeClipboard: (content: string) => Promise<void>
}

export function createCopyCommand({
  readConversation,
  writeClipboard,
}: CopyDependencies) {
  const execute = pipeline(
    readConversation,
    writeClipboard,
  )

  return { name: "copy", execute }
}
```

```ts
// commands/index.ts，省略来自实际所属模块的导入。
const copy = createCopyCommand({
  readConversation,
  writeClipboard,
})

const builtins = [copy]
```

创建函数在此表达依赖绑定，即使只有一个实现也有价值。普通依赖对象和显式成员数组即可，
无需容器、服务定位器或层层工厂；类型、常量和内部实现仍可正常导入。
注入时保留接收者绑定、资源所有权与生命周期，不给每个局部函数传递全部能力。

机制使用成员契约并承载共同规则，不能硬编码成员的领域行为；
复制命令使用对话和剪贴板能力，不因此接管它们的规则和状态。
行为入口的阶段、策略与局部控制见 [Flow Expression](flow-expression.md)，不为目录逐级创建转发。

## 4. 用变化检查边界

| 变化 | 自然修改位置 | 检查点 |
| --- | --- | --- |
| 新增内置命令 | 成员与必要组装 | 无关成员和机制不因增长被迫修改 |
| 扩充命令内部实现 | 对应文件或成员目录 | 不为对称调整其他成员外形 |
| 修改共同匹配规则 | catalog 及测试 | 不逐个修改成员的领域行为 |
| 增加研究来源 | 现有来源位置，必要时再分组 | 不牵连其他报告能力 |

真实契约变化可以跨模块传播，避免的是无关牵连。
纯定位问题可以只整理目录；职责分散时才需要收拢职责、依赖与入口。
测试关注成员行为、共同规则与必要的跨边界流程，而不只是旧文件是否消失。

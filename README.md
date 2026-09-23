# Architecture Skills

面向阅读、修改与人机协作的两个独立 Skill：同仓维护，按需加载，协同演进。

| Skill | 职责 | 典型场景 |
| --- | --- | --- |
| [architecture-co-design](skills/architecture-co-design/SKILL.md) | 澄清需求、讨论模块边界与取舍，共同收敛方案 | 模块怎么拆、目录怎么组织、代码太碎、修改牵连过多 |
| [structure-expression](skills/structure-expression/SKILL.md) | 让目录与代码贴合阅读偏好：组成清楚、阶段连续、控制流平坦、细节逐层展开 | 目录与成员集合、模块粒度、阶段组合与数据衔接、视觉组织、Graph 转移 |

## 配合方式

- 需求、职责或边界尚未明确：共创负责收敛，结构 Skill 提供设计依据。
- 已确认方案并开始实现：结构 Skill 指导表达，不重复启动完整架构讨论。
- 局部可读性调整：可以单独使用结构 Skill。
- 发现需要改变职责或扩大范围：只重新讨论受影响的决策。

共同使用时，复用同一份调查、设计样本与阅读/变更推演，不重复执行两套完整流程。结构偏好不自动推翻已确认方案，也不替代实际项目约束。

两个 Skill 独立可用，不需要第三个管理 Skill。`references/` 根据各自 `SKILL.md` 的条件加载，不默认一次读完。

本仓库不提供强制 Pipeline DSL 或 Workflow Runtime。结构表达可以复用普通函数、已有库或必要的小型组合工具；不要因为示例 API 而引入执行框架。

## 目录

```text
skills/
├── architecture-co-design/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   └── references/
│       ├── dialogue-examples.md
│       └── design-agreement.md
└── structure-expression/
    ├── SKILL.md
    └── references/
        ├── flow-expression.md
        ├── graph-expression.md
        └── module-organization.md
scripts/check.py          # 无第三方依赖的基础文档检查
tests/evaluation.md       # 手动行为验证场景，不是自动通过的测试
```

## 安装到本地 skills 目录

推荐克隆仓库，再将两个 Skill 目录分别链接到 `~/.agents/skills/`。仓库是唯一维护源，安装目录只负责加载。

```sh
gh repo clone Yangeyu/architecture-skills
cd architecture-skills
python3 scripts/check.py
```

以下命令适用于 macOS / Linux，要求两个目标名称尚未安装。它会先检查冲突，不覆盖已有目录或链接。已有安装应先备份到 `~/.agents/skills/` 之外，再执行。

```sh
(
  set -eu
  repo="$(pwd -P)"
  destination="$HOME/.agents/skills"
  mkdir -p "$destination"

  for name in architecture-co-design structure-expression; do
    test -f "$repo/skills/$name/SKILL.md"
    if [ -e "$destination/$name" ] || [ -L "$destination/$name" ]; then
      printf '目标已存在，请先检查并备份：%s\n' "$destination/$name" >&2
      exit 1
    fi
  done

  for name in architecture-co-design structure-expression; do
    ln -s "$repo/skills/$name" "$destination/$name"
  done
)
```

安装后确认客户端技能目录中出现两个名称，并分别尝试加载主文件及参考文档。客户端可能需要刷新或重启；本仓库不假定所有客户端都支持符号链接。

如果客户端不支持链接，在备份旧安装后复制 `skills/<name>/` 到配置目录。仍只编辑仓库文件，更新时重新安装，避免维护两份不同内容。

### 调用与客户端配置

- 手动入口：`/architecture-co-design`、`/structure-expression`（客户端支持斜杠调用时）。
- 两个 Skill 当前的 frontmatter 都允许自动调用，并保留手动入口。
- 本机 Harness 使用 `SKILL.md` 的 `disable-model-invocation` 与 `user-invocable` 字段。
- `architecture-co-design/agents/openai.yaml` 是迁移前已有的 Codex 配置，原样保留；它不能替代 Harness 的 frontmatter 配置。

### 更新与卸载

在仓库中执行：

```sh
git pull --ff-only
python3 scripts/check.py
```

链接安装会指向更新后的仓库文件；运行中的客户端仍可能缓存内容，需要重新加载。仓库有未提交修改时，先检查并处理这些修改，不使用强制重置覆盖它们。

不要移动或删除仓库后继续保留旧链接。卸载时先确认目标确实是本仓库的符号链接，再用 `unlink` 移除链接；不要递归删除仓库源文件。需要回退时，恢复安装前保留的备份。

## 维护与验证

1. 只在 `skills/` 下维护 Skill 正文、参考文档和客户端配置。
2. 原则与默认取向的实质改变应单独说明理由，不借精简悄悄弱化设计主张。
3. 跨 Skill 的修改同时检查协作边界，避免重复询问、重复推演或结构偏好越权。
4. 运行 `python3 scripts/check.py`，检查必要元信息、Markdown 链接、代码块闭合与异常控制字符。
5. 根据变更选择 [行为验证场景](tests/evaluation.md)，记录观察结果；基础文档检查不代表 LLM 行为已经验证。
6. 使用 Git commit 记录改动及理由。稳定版本再使用 tag，不把初次迁移视为已验证的稳定发布。

`check.py` 是针对本仓库格式的轻量检查，不是通用 YAML 解析器、完整 Markdown 校验器或客户端兼容性测试。

## 仓库范围与许可

初始迁移按私有仓库管理，保留现有 Skill 内容，不附带自动更新器、发布平台或运行时框架。

尚未选择开源许可证；公开发布或授权再分发前，应先由维护者明确许可范围，再添加对应 `LICENSE`。

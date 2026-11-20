# Orchestrator

[English](README.md) | 简体中文

面向 **Antigravity 单模型会话**的双阶段“规划与执行”（Plan and Execute）编排插件——将主干规划会话（`Trunk Session`）与单个受控绑定的原生执行子代理（`Execution Subagent`）配对，通过无损且受上下文压缩边界约束的 `Living Memory Window` 窗口同步实现跨轮记忆继承。

---

## 安装方式（纯 Skill 包）

`orchestrator` 仅包含根目录 [plugin.json](plugin.json) 与独立自包含的 [skills/orchestrator/](skills/orchestrator/SKILL.md) 目录——V1 版本不包含任何捆绑 `rules/` 目录、启动钩子（startup hooks）、常驻后台进程（sidecar）或非 Antigravity 客户端清单。

- **作为 Antigravity 纯 Skill 插件安装**：直接克隆至 Antigravity 插件目录（`git clone https://github.com/titicheck/dual-brain-orchestrator.git ~/.gemini/config/plugins/orchestrator`），或运行 `agy plugin install <path>`。
- **作为独立 Skill 使用**：将 `skills/orchestrator` 软链接或复制到 Antigravity 的 skills 目录中。
- **零配置斜杠命令调用**：在任意未配置规则的 Antigravity 对话框中直接输入 `/orchestrator`，即可按内置默认 `flash` 档位运行同一套统一工作流。

---

## 共享工程规则接入与静态档位优先级

### 标准规则接入片段（`< 1,000` 字节）

将以下片段写入你的共享工程规则库 `AGENTS.md`（或全局 `~/.gemini/GEMINI.md`）即可；日常项目只需引用该共享规则库，**无需**在项目自身配置文件中单独添加任何 `orchestrator` 条目（英文版片段见 [README.md](README.md)）：

```markdown
## Orchestrator

仅在由人类发起的顶层单模型会话（含上下文压缩后）中，且未暴露精确小写 `exit_plan_mode`/`enter_plan_mode`、非 `/swarm` 流程时，于规划或执行涉及文件/状态修改与外部副作用的任务，或处理已绑定 `Execution Subagent` 回报时加载 `orchestrator`（遵循其 `SKILL.md`）。绑定执行子代理档位锁死为静态 `orchestrator-tier:` 规则（口头模型请求绝不覆盖；单项目可在工作区 `AGENTS.md` 声明同名指令覆盖）。

orchestrator-tier: flash
```

### 静态档位作用域优先级（`orchestrator-tier:`）

执行子代理档位仅接受 `flash`、`pro`、`flash_lite` 或 `inherit`，并严格按以下具体度从高到低从静态规则解析（对话中的口头模型请求不会更改该档位）：

1. 工作区本地 `AGENTS.md` / `GEMINI.md`
2. 全局直写 `~/.gemini/GEMINI.md`
3. `@[...]` 导入的共享工程规则（如 `engineering-kit/rules/AGENTS.md`）
4. 内置默认值 `"flash"`

若仅需为单个项目覆盖执行档位，只需在该项目的 `AGENTS.md` 中添加一行：

```markdown
orchestrator-tier: pro
```

---

## 架构与跨客户端扩展边界

- [skills/orchestrator/SKILL.md](skills/orchestrator/SKILL.md) — `Trunk Session` 控制循环、有序准入闸门（Entry Gate）、三路入站路由、Official Part 2 规划与 Part 7 `[plan review]`。
- [skills/orchestrator/references/execution-protocol.md](skills/orchestrator/references/execution-protocol.md) — 与宿主解耦的单阶段 `Execution Subagent` 执行协议（Official Parts 4、5 及适配的 Part 6）。
- [skills/orchestrator/references/harnesses.md](skills/orchestrator/references/harnesses.md) — Antigravity V1 宿主绑定（`invoke_subagent`、`send_message`、`manage_subagents`、同级 `logAbsoluteUri`、`sync_memory.py` CLI）及面向 Claude Code / Codex 的预留未来客户端适配接缝。
- [skills/orchestrator/scripts/sync_memory.py](skills/orchestrator/scripts/sync_memory.py) — 零第三方依赖的 Python 3 标准库同步 CLI（`check-origin`、`sync`、`bind`、`reset`）。

---

## 验证方法

### 自动化测试套件（`Seam 1` + `Seam 2A`）

```powershell
py -3 -m unittest discover -s tests -v
```
*（POSIX 系统请使用 `python3 -m unittest discover -s tests -v`。）*

### `Seam 2B` — Antigravity 实机冒烟验证与原生对比清单

在 V1 上运行以下 4 项交互式 Antigravity 检查，并与原生 `Orchestrator` 并排对比：

1. **无条件退让原生 Orchestrator**：在暴露精确小写 `exit_plan_mode` / `enter_plan_mode` 的 `Orchestrator (Carbon)` / `Orchestrator (Neon)` / `Orchestrator (Argon)` 会话中触发编码任务与 `/orchestrator ...`；确认原生同线程热切换完整运行，且零 `sync_memory.py` 调用、零额外派发 `Execution Subagent`。
2. **防递归、压缩后纯问答直答与三路路由**：确认子代理与 `[swarm]`/`[board]` worker 在实时会话及压缩后均保持单阶段（`check-origin` 对 `"SUBAGENT"` 或 `"UNKNOWN"` 故障闭锁），压缩后的纯问答回合零 CLI 子进程调用，平行 `Isolated Subagent` 的 `[Message]` 回复保留在 `Trunk Session`，以及被取代的孤儿 `Execution Subagent` 被忽略/终止。
3. **静态档位锁与 Approve-First / `[plan review]` 连续性**：确认共享规则接入与未配置 `/orchestrator` 锁定在 `"flash"`（忽略对话中的 `"use pro"`），在工作区 `AGENTS.md` 添加 `orchestrator-tier: pro` 会触发 `tier != bound_tier` 的 `SPAWN_NEW` 轮换，且 Approve-First / 中途取消 / `[plan review]` 均平稳衔接不丢失活跃状态。
4. **平行 `Isolated Subagent` 正交性**：在运行 `flash` 档 `Execution Subagent` 的前沿单模型 `Trunk Session` 中调用 `egm-*` / `research` / `code-review`，确认这些 `Isolated Subagent` 零 `Living Memory Window` 注入且完全不受 `orchestrator-tier:` 影响。

# Develop DSH Plugin

一个指导 AI 编码助手开发 **DeepSeek Harness 仓外插件**的 Skill：从需求与扩展点选择，到实现、打包、真实组合验证和卸载检查。

它来自对 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) 开发历史、架构文档与 Agent Notes 的研究，以及实际插件开发中的经验。覆盖 Host / Client 边界、Cordis 服务与事件、模型工具、会话回放、UI slot、主题和安装通道。

An agent skill for building and reviewing out-of-tree DeepSeek Harness plugins. Includes an extension-point guide, package contracts, a failure casebook, a minimal Host template, and Python scaffolding/audit helpers.

## 安装与使用

把整个仓库安装为一个 skill 目录。例如，使用 DSH 的用户级 skills 目录：

```bash
mkdir -p ~/.dsh/skills
git clone https://github.com/hanlinlibham/develop-dsh-plugin.git \
  ~/.dsh/skills/develop-dsh-plugin
```

其他支持 `SKILL.md` 的编码助手，可以把该目录放进其技能发现路径，或直接让助手读取 [SKILL.md](SKILL.md)。保留 `references/`、`assets/` 和 `scripts/` 的相对位置。

示例指令：

> 使用 develop-dsh-plugin，先调查目标 DSH 版本的官方与社区能力，再为我的需求设计、开发并验证一个可独立卸载的插件。

本包提供开发指导和辅助脚本，安装本包不会向运行中的 DSH 挂载产品插件。

## 内容

| 入口 | 用途 |
|---|---|
| [SKILL.md](SKILL.md) | 研究、设计、实现、验收的完整工作流 |
| [扩展点选择](references/seam-router.md) | 服务、事件、工具、slot 与主题的职责边界 |
| [包合同](references/package-contract.md) | exports、依赖、工具、Client 与安装合同 |
| [验收与案例](references/validation-and-casebook.md) | 验证矩阵和真实开发中的失败模式 |
| [0.2.2 开发迁移说明](references/runtime-0.2.2.md) | 已核对的版本、接口变化、官方来源和验证边界 |
| [Host 模板](assets/minimal-host-plugin/) | 一个最小模型工具插件的源码模板 |
| [脚手架](scripts/scaffold_plugin.py) | 使用显式版本生成插件；拒绝覆盖已有内容 |
| [静态审计](scripts/audit_plugin.py) | 检查包结构、导出、依赖和构建文件 |

## 辅助脚本

辅助脚本只依赖 Python 3.10+ 标准库。当前 Host 模板已针对 **DSH 0.2.2-rc.1 / Cordis 4.1.0 / Node.js >=24.9.0** 验证（2026-11-07）；其他版本须先核对模板 API 与依赖。

从**实际目标运行时**取得精确版本后：

```bash
python3 scripts/scaffold_plugin.py ./dsh-plugin-example \
  --package-name dsh-plugin-example \
  --dsh-version "$TARGET_DSH_VERSION" \
  --cordis-version "$TARGET_CORDIS_VERSION" \
  --dry-run
```

确认输出后去掉 `--dry-run`。构建生成的插件，再检查其包结构：

```bash
python3 scripts/audit_plugin.py ./dsh-plugin-example \
  --dsh-version "$TARGET_DSH_VERSION" --require-built
```

运行辅助脚本的回归检查：

```bash
python3 -B scripts/test_scripts.py
```

## 版本与验证边界

这里的经验与示例来自特定版本的实践，未承诺兼容所有 DSH 版本。当前版本仍是 RC。开发时应重新核对目标运行时的服务、事件和 slot 合同，并区分发布 tag 与 `master` 上尚未发布的变化。

CI 会在干净环境生成插件并安装依赖，执行类型检查、构建、真实工具注册与执行、取消及卸载测试。静态审计支持多 patch bundle 和 peer/dev 依赖检查，但不求解 SemVer 范围。上述检查仍不等于完整 Loader、模型会话、回放或浏览器验收；这些按 Skill 的验证矩阵完成。

临时使用 `cordis_inspect_*` / `cordis_define` / `cordis_run` 定义运行时插件时，应使用目标 DSH 提供的动态插件工作流。

## 更新

已安装的副本可以这样更新：

```bash
git -C ~/.dsh/skills/develop-dsh-plugin pull --ff-only
```

每次 push / PR 执行脚本测试和 Gitleaks 扫描，也可以在 Actions 页面手动触发。当前没有定时同步任务。

维护者检查 DSH 的合同变化，修订相关指导和模板，验证后提交。更新时只包含本 Skill 的公开文件，不同步其他工作区内容或历史。

贡献前请运行脚本测试，并说明影响的 DSH 版本与实际验证范围。请勿提交凭据、内部域名、用户数据或机器专属配置。

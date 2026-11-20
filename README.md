# OpenEmber CLI

独立的 `ember` 命令行工具仓库，供 **OpenEmber** / **EmberLite** 等工程共用。该工具本身只做“通用编排”：**具体项目差异由项目仓库内的固定入口脚本与 CMake/Kconfig 配置承担**。

本仓库提供：

- `scripts/ember`：主命令
- `scripts/completions/ember.bash`：子命令补全功能

工程命令（包括 `menuconfig --product`、`defconfig`、`savedefconfig`、`update`、`build` 和 `run`）优先转发给所选工程的 OpenEmber 核心 `scripts/ember`，由该核心版本解释参数与执行构建；安装和环境注册仍由本仓库管理。工程可通过当前目录及其父目录、`OPENEMBER_ROOT` 或已选择的环境定位。安装不会把核心命令复制到本仓库，因此核心更新后无需重新复制命令实现。没有可转发的核心入口时，保留原有通用构建流程。

补全在终端启动时载入。更新本仓库后，已打开的 Bash 终端执行 `source <(ember completion bash)` 即可刷新；新终端自动载入。

## 目录约定

`ember` 需要定位到一个“工程根目录”，并假设该工程根目录包含：

- `CMakeLists.txt`
- `scripts/kconfig/menuconfig.sh`
- `scripts/kconfig/genconfig.sh`

`ember` 不关心工程内部有哪些组件/third_party/目标，只负责调用这些入口脚本 + 调用 CMake。

## 快速开始

直接在工程根目录执行（无需安装到全局）：

```bash
/path/to/<project>/scripts/ember build
```

或使用本仓库的脚本并通过环境/路径指向目标工程（见下文“环境管理”）。

## 安装（可选）

在本仓库目录中执行：

```bash
./scripts/ember install
```

它会把 `ember` 软链接安装到 `~/.local/bin/ember`（默认）并把 PATH/completion 片段写入 `~/.bashrc`（与 OpenEmber/EmberLite 内置脚本行为一致）。

注意：如果你同时从多个工程执行 `ember install`，会因为全局命令名相同而互相覆盖；推荐统一只安装本仓库的 `ember`，并通过 env 管理选择目标工程。

---

## ember CLI 使用手册

本页描述 `ember` 脚本的**完整使用方法**。EmberLite 与 OpenEmber 的 `ember` 命令保持一致（已同步 env 管理子命令）。

### 快速开始

在工程根目录执行（框架根：含 `CMakeLists.txt` 与 `scripts/kconfig/menuconfig.sh`；产品根：含 `CMakeLists.txt` 与 `openember/scripts/kconfig/menuconfig.sh`）：

```bash
./scripts/ember build
```

如果你不在工程根目录，也可以先注册环境再使用（见下文 “环境管理”）。

### 环境变量

- **`OPENEMBER_ROOT`**：显式指定工程根目录（优先级最高；框架根或产品根）
- **`OPENEMBER_ORIGIN`** / **`OPENEMBER_CUSTOM`**：由 `ember` 自动导出——origin=框架源码树（Kconfig srctree），custom=产品仓（若与 origin 不同）
- **`OPENEMBER_BUILD_DIR`**：默认构建目录名（默认：`build`）
- **`OPENEMBER_JOBS`**：并行编译任务数（默认：可用逻辑 CPU 数的一半，向下取整，至少 1、最多 8）；`-j/--jobs` 优先
- **`CARGO_BUILD_JOBS`**：Cargo 专用并行度覆盖值；未设置时跟随所选构建并行度
- **`OPENEMBER_KCONFIG_NONINTERACTIVE=1`**：menuconfig 以非交互方式生成默认 `.config`
- **`OPENEMBER_KCONFIG_FRONTENDS_DIR`**：覆盖 kconfig-frontends 解压/安装目录（否则下载到 `.kconfig-frontends/`）

### 环境管理（nvm-like）

用于在“当前不在工程目录”的情况下仍能运行 `ember build/update/...`。

#### ember add

注册一个环境名 → 工程根目录：

```bash
ember add emberlite /path/to/emberlite
ember add openember /path/to/openember
```

#### ember list

列出已注册环境（当前环境前面有 `*`）：

```bash
ember list
```

示例输出：

```text
* emberlite -> /path/to/emberlite
  openember -> /path/to/openember
```

#### ember use

选择当前默认环境：

```bash
ember use emberlite
```

#### ember del

删除一个已注册的环境（如果删除的正是当前环境，会同时清空 current）：

```bash
ember del emberlite
```

#### ember current

打印当前环境名（若未设置则无输出）：

```bash
ember current
```

#### 存储位置

环境注册信息保存在：

- `~/.openember/ember/envs/<name>`：文件内容为工程根目录路径
- `~/.openember/ember/current`：当前环境名

### Kconfig / CMake 工作流

#### ember menuconfig

交互式配置（或在无 TTY/CI 下生成默认配置）：

```bash
ember menuconfig            # 默认 build/
ember menuconfig out/build  # 指定 build_dir
```

产生：

- `<build_dir>/.config`
- 同时会在该命令后自动运行 `genconfig`（通过脚本组合）

首次运行会准备 `kconfig-frontends-nox`（若系统未安装），下载解压到工程根目录的 `.kconfig-frontends/`。

#### ember genconfig

将 `<build_dir>/.config` 映射为 `<build_dir>/config.cmake`（CMake 缓存变量片段）：

```bash
ember genconfig
ember genconfig out/build
```

#### ember update（configure）

配置（`cmake -S -B`）：

```bash
ember update
ember configure   # 兼容别名
```

并下载或更新第三方库（如果有需要）。

#### ember build

完整构建流程：

```bash
ember build
ember build out/build
ember build -j 4
ember build out/build --jobs=4
```

行为：

- 若 `<build_dir>/.config` 不存在：自动以非交互方式生成默认配置
- 若 `<build_dir>/config.cmake` 不存在：自动生成
- 随后执行：`cmake -S <root> -B <build_dir>` + `cmake --build <build_dir> -j<jobs>`

并行度优先级：`-j N` / `-jN` / `--jobs N` / `--jobs=N` > `OPENEMBER_JOBS` >
`min(8, max(1, floor(可用逻辑 CPU 数 / 2)))`。显式值可超过默认的 8；
仅接受正整数，零、负数和非整数会在配置/构建前拒绝。
同一策略也适用于 `ember all`。

CLI 向子进程传递 `CMAKE_BUILD_PARALLEL_LEVEL=<jobs>`，并在没有显式 Cargo
覆盖值时设置 `CARGO_BUILD_JOBS=<jobs>`，避免嵌套 CMake/Cargo 沿用全核默认。
两项有效值都会在启动时打印；这是各工具的任务并行度，不是进程树总 CPU 配额。
这些设置属于开发机器，不写入产品 Kconfig 或 defconfig。

#### ember all

全流程（交互式 menuconfig + update + build）：

```bash
ember all
```

#### ember clean

删除构建目录：

```bash
ember clean
ember clean out/build
```

### 补全与安装

#### ember completion bash

输出 bash completion 脚本：

```bash
ember completion bash
```

#### ember install / uninstall

将 `ember` 脚本以符号链接方式安装到 PATH（默认 `~/.local/bin/ember`），并在 `~/.bashrc` 写入 PATH 与 completion 片段：

```bash
ember install
ember install --prefix /custom/bin
```

卸载：

```bash
ember uninstall
ember uninstall --prefix /custom/bin
```

注意：多个工程都执行 `ember install` 时，会因全局命令名相同而互相覆盖；此时建议**不要全局安装**，直接在工程根目录运行 `./scripts/ember`，或使用 “环境管理” 的 `add/use` 来切换默认工程。

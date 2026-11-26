# 麦设

`zeyr.mai-profile` · 静态人设档案与隐私留白。

开发基线 MaiBot 1.4.8 / SDK 2.23.0。可独立安装，其他 zeyr 插件仅通过公开 API 自动联动。

首批已实现：结构化公开/私有/触发字段、隐私边界、触发词摘要、`get_snapshot` API、`query_self_profile` 工具，以及仅基于真实入站文本的轻量 Hook 注入。不会在入口拦截消息，也不会返回 `private` 字段。

配置默认名单为空。模板和字段内容写入实例 `config.toml`，源码仓只保留通用默认值。`show_advanced` 可折叠高级渲染项；运行状态不写入仓库。

仍需在已升级的真实 MaiBot 1.4.8 宿主上做 Hook/组件验收，当前离线测试不等同于生产上线。

安装时将整个目录同步到宿主 plugins；运行 config.toml 由 SDK 生成。实例名单、个人资料和密钥只填运行配置，不提交。

检查：`python -m pytest`，开发依赖见 pyproject.toml。

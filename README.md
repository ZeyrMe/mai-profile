# 麦设

`zeyr.mai-profile` · 静态人设档案与隐私留白。

开发基线 MaiBot 1.4.8 / SDK 2.23.0。可独立安装，其他 zeyr 插件仅通过公开 API 自动联动。

首批已实现：结构化公开/私有/触发字段、隐私边界、触发词摘要、`get_snapshot` API、`query_self_profile` 工具，以及仅基于真实入站文本的轻量 Hook 注入。不会在入口拦截消息，也不会返回 `private` 字段。

配置默认名单为空。模板和字段内容写入实例 `config.toml`，源码仓只保留通用默认值。`show_advanced` 可折叠高级渲染项；运行状态不写入仓库。

仍需在已升级的真实 MaiBot 1.4.8 宿主上做 Hook/组件验收，当前离线测试不等同于生产上线。

安装时将整个目录同步到宿主 plugins；运行 config.toml 由 SDK 生成。实例名单、个人资料和密钥只填运行配置，不提交。

检查：`python -m pytest`，开发依赖见 pyproject.toml。


## v2.5 第一批：范围与原生控制台

新增独立 `[scope]`：mode 默认 all；groups / privates / users 接受 `group:标识` / `private:标识` / `user:标识`，可带平台前缀（默认 qq）。mode=whitelist 只允许命中对象；mode=blacklist 排除命中对象；all 允许所有对象。exclude 始终优先。allow_private=false 仅放行名单明确指定的私聊，主动私聊仍需单独配置目标。

可用 `@set:名称` / `@tag:名称` 复用 mai-circle 集合/标签；缺席时按空集合降级，不影响直接对象。受限模式在没有真实会话身份时跳过业务，消息仍正常进入宿主。重启后的会话身份缓存由入站消息恢复。

WebUI 配置页提供运行状态面板与“刷新公共集合缓存”按钮，不调用模型、不发送聊天。范围分组默认折叠；字段采用中文标签与结构化条目卡片。

trigger_words 字典改为 trigger_rules 主题/关键词列表，旧配置自动转换。

本批只升级公共基础设施，完整 v2.5 的业务能力尚未全部实现。旧配置保持可读，Runner 规范化写回后采用新结构；回退旧代码前需恢复相应配置快照。实例 config.toml 仍不进入 Git。

## 0.2.0 · v2.5 业务增量

结构化/公开文本两种规格、basic_fields/routine_note/likes_and_dislikes/guarded_entries；未设定事实返回 unset。disclosure=private 永不返回真实值，shy 清晰度仅由真实相关入站消息推进，同 message_id 去重，按会话和用户隔离并随时间衰减。工具/API 只读，不推进松口；未填写 teaser 时不会自动泄露原文轮廓。控制台可重置全部进度。

## 未发布 · v2.5 Batch 1

- 新增独立 scope、群/私聊身份判定与公共集合软联动。
- 新增原生状态面板和缓存刷新按钮；改进中文结构化配置，兼容旧格式。
- 完整业务升级仍按后续批次实施，本批未部署到运行卷。

# 0.1.0

首次开发版本；运行验收前不发布正式 Release。

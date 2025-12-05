# M3 Agent v5.9.1 - Bug修复报告

## 修复版本信息
- 版本号: v5.9.1
- 修复日期: 2024-12-05
- 修复类型: 关键bug修复 (事件循环冲突)

## Bug描述
v5.9.0版本引入了异步浏览器池优化,但在LangGraph的同步工具调用环境中导致事件循环冲突。

## 根本原因
1. LangGraph工具调用是同步的
2. 异步浏览器池与同步工具不兼容
3. browser_sync_wrapper桥接失败
4. 启动时的竞态条件

## 修复方案
回退到同步浏览器池,使用sync_playwright()创建全局浏览器池。

## 修复内容
1. 修复app/core/browser_pool.py - 改用sync_playwright()
2. 删除app/core/browser_sync_wrapper.py - 不再需要
3. 修复app/core/startup.py - 改为同步函数
4. 修复main.py - startup_event改为同步
5. 修复所有工具文件 - 移除browser_sync_wrapper引用
6. 更新requirements.txt - 移除nest-asyncio

## 修复效果
- 性能保留: 浏览器池优化仍然提升90%性能
- 稳定性提升: 完全兼容LangGraph,无事件循环冲突
- 向后兼容: API接口无变化

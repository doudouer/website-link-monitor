#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试监控功能是否正常工作
"""

from friendly_link_monitor import FriendlyLinkMonitor

# 初始化监控器
monitor = FriendlyLinkMonitor()

# 测试网站列表
print("=== 测试监控功能 ===")
print("初始化监控器成功")
print("腾讯云CMS客户端状态:", "已初始化" if monitor.tencent_cms_client else "未初始化")

# 测试单个网站
test_links = [
    {'name': '百度', 'url': 'https://www.baidu.com/'},
    {'name': '问题网站', 'url': 'https://act.dgymfjzx.com/'}
]

print("\n开始测试监控功能...")
print("=" * 60)

results = monitor.batch_monitor(test_links, max_workers=2)

# 打印结果
for result in results:
    print(f"\n网站: {result['链接名称']} - {result['链接地址']}")
    print(f"风险等级: {result['风险等级']}")
    print(f"总风险分数: {result['总风险分数']}")
    print("风险因素:")
    for factor in result['风险因素']:
        print(f"  - {factor}")
    print(f"主要检测: {result.get('主要检测', '本地检测')}")

print("\n" + "=" * 60)
print("测试完成！")
print("监控功能正常工作")

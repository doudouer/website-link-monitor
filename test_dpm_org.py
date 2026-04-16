#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试故宫网站的检测结果
"""

from friendly_link_monitor import FriendlyLinkMonitor

# 初始化监控器
monitor = FriendlyLinkMonitor()

# 测试故宫网站
test_links = [
    {'name': '故宫博物院', 'url': 'https://www.dpm.org.cn/'}
]

# 开始测试
print("开始测试故宫网站...")
print("=" * 70)

results = monitor.batch_monitor(test_links, max_workers=1)

# 打印详细结果
for result in results:
    print(f"\n网站: {result['链接名称']} - {result['链接地址']}")
    print(f"风险等级: {result['风险等级']}")
    print(f"总风险分数: {result['总风险分数']}")
    print("风险因素:")
    for factor in result['风险因素']:
        print(f"  - {factor}")
    print(f"主要检测: {result.get('主要检测', '本地检测')}")
    print(f"网站截图: {result.get('网站截图', '无')}")

print("\n测试完成！")

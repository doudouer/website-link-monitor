#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试腾讯云API返回结果
"""

from friendly_link_monitor import FriendlyLinkMonitor

# 初始化监控器
monitor = FriendlyLinkMonitor()

# 测试网站列表（包含不同类型的网站）
test_links = [
    {'name': '正常网站', 'url': 'https://www.baidu.com/'},
    {'name': '问题网站1', 'url': 'https://act.dgymfjzx.com/'},
    {'name': '问题网站2', 'url': 'https://uxj2.vip/'}
]

# 开始测试
print("开始测试腾讯云API返回结果...")
print("=" * 70)

results = monitor.batch_monitor(test_links, max_workers=3)

# 打印详细结果
for result in results:
    print(f"\n网站: {result['链接名称']} - {result['链接地址']}")
    print(f"风险等级: {result['风险等级']}")
    print(f"总风险分数: {result['总风险分数']}")
    print("风险因素:")
    for factor in result['风险因素']:
        print(f"  - {factor}")
    print(f"主要检测: {result.get('主要检测', '本地检测')}")

print("\n测试完成！")

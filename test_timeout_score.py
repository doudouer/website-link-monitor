#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试访问超时的风险分数
"""

from friendly_link_monitor import FriendlyLinkMonitor

def test_timeout_score():
    """测试访问超时的风险分数"""
    monitor = FriendlyLinkMonitor()
    
    # 测试一个可能会超时的网站
    test_link = {
        'name': '中国电影博物馆',
        'url': 'https://www.cnfm.org.cn/'
    }
    
    print("开始测试访问超时的风险分数...")
    print(f"测试网站: {test_link['name']} - {test_link['url']}")
    
    # 监控链接
    result = monitor.monitor_link(test_link)
    
    # 打印结果
    print("\n测试结果:")
    print(f"风险等级: {result['风险等级']}")
    print(f"总风险分数: {result['总风险分数']}")
    print("风险因素:")
    for factor in result['风险因素']:
        print(f"  - {factor}")
    
    # 检查是否包含超时风险因素
    timeout_factor = any('访问超时' in factor for factor in result['风险因素'])
    if timeout_factor:
        print("\n✓ 检测到访问超时风险因素")
    else:
        print("\n✗ 未检测到访问超时风险因素")

if __name__ == "__main__":
    test_timeout_score()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试特定网站的检测
"""

from friendly_link_monitor import FriendlyLinkMonitor
import os

def test_specific_site():
    """测试特定网站"""
    print("=== 测试特定网站 ===")
    
    monitor = FriendlyLinkMonitor()
    
    # 测试网站
    test_link = {
        'name': '测试网站',
        'url': 'http://1659774.mz42.com/index.phtml?FID=1659774'
    }
    
    print(f"\n正在检测: {test_link['url']}")
    result = monitor.monitor_link(test_link)
    
    print(f"\n=== 检测结果 ===")
    print(f"风险分数: {result['总风险分数']}")
    print(f"风险等级: {result['风险等级']}")
    print(f"\n风险因素:")
    for factor in result['风险因素']:
        print(f"  - {factor}")
    
    # 检查截图
    if '网站截图' in result and result['网站截图']:
        print(f"\n截图路径: {result['网站截图']}")
        if os.path.exists(result['网站截图']):
            print("✓ 截图存在")

if __name__ == '__main__':
    test_specific_site()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的代码
"""

from friendly_link_monitor import FriendlyLinkMonitor

def test_tencent_api():
    """测试腾讯云API"""
    print("=== 测试修复后的腾讯云API ===")
    
    monitor = FriendlyLinkMonitor()
    
    # 1. 测试文本审核
    print("\n1. 测试文本审核...")
    text_result = monitor.check_content_security("这是一段正常的测试文本")
    print(f"   结果: {text_result}")
    
    # 2. 测试图片审核
    print("\n2. 测试图片审核...")
    import os
    screenshot_dir = 'screenshots'
    if os.path.exists(screenshot_dir):
        files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
        if files:
            test_image = os.path.join(screenshot_dir, files[0])
            print(f"   使用图片: {test_image}")
            image_result = monitor.check_image_security(test_image)
            print(f"   结果: {image_result}")
        else:
            print("   没有找到截图")
    else:
        print("   screenshots目录不存在")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_tencent_api()

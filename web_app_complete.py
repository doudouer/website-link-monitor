#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
友谊链接监控系统 - Web应用
功能：检测友谊链接安全性，识别非法内容网站
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import sys
import json
import base64
from datetime import datetime
from io import BytesIO

app = Flask(__name__)
CORS(app)

from friendly_link_monitor import FriendlyLinkMonitor

monitor = FriendlyLinkMonitor()

def extract_friendly_links_smart(url):
    """智能提取友情链接"""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse
    import re
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        seen = set()
        base_domain = urlparse(url).netloc
        
        def get_root_domain(domain):
            parts = domain.split('.')
            if len(parts) >= 2:
                if parts[-1] in ['cn', 'com', 'net', 'org', 'gov', 'edu']:
                    if len(parts) >= 3 and parts[-2] in ['com', 'net', 'org', 'gov', 'edu']:
                        return '.'.join(parts[-3:])
                    return '.'.join(parts[-2:])
                return '.'.join(parts[-2:])
            return domain
        
        base_root = get_root_domain(base_domain)
        
        def is_valid_friendly_link(href, text):
            if not href or not href.startswith('http'):
                return False
            href_domain = urlparse(href).netloc
            if href_domain == base_domain:
                return False
            href_root = get_root_domain(href_domain)
            if base_root == href_root:
                return False
            exclude = ['beian', 'miit', 'weibo.com', 'weibo.cn', 'weixin.qq.com', 'mp.weixin', 'twitter.com', 'facebook.com', 'instagram.com']
            for p in exclude:
                if p in href.lower():
                    return False
            return True
        
        keywords = ['友情链接', '友情连接', '合作链接', '合作伙伴', '友情', 'links', 'partner', 'friend', '相关链接', '常用链接']
        
        for keyword in keywords:
            elements = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
            for elem in elements:
                parent = elem.parent
                if parent:
                    container = parent.parent if parent.parent else parent
                    for a in container.find_all('a', href=True):
                        href = a.get('href')
                        text = a.get_text(strip=True)
                        if is_valid_friendly_link(href, text) and href not in seen:
                            links.append({'name': text or href, 'url': href, 'source': f'关键词: {keyword}'})
                            seen.add(href)
        
        if not links or len(links) < 5:
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                text = a.get_text(strip=True)
                if is_valid_friendly_link(href, text) and href not in seen:
                    links.append({'name': text or href, 'url': href, 'source': '外部链接'})
                    seen.add(href)
        
        return links
    except Exception as e:
        print(f"爬取失败: {e}")
        return []

@app.route('/')
def index():
    return render_template('index_complete.html')

@app.route('/api/crawl', methods=['POST'])
def crawl_links():
    """爬取友情链接"""
    data = request.json
    url = data.get('url', '')
    selector = data.get('selector', '')
    
    print(f"爬取请求: url={url}")
    
    if not url:
        return jsonify({'success': False, 'error': '请输入网站地址'})
    
    try:
        links = extract_friendly_links_smart(url)
        print(f"提取到 {len(links)} 个链接")
        return jsonify({'success': True, 'links': links, 'count': len(links)})
    except Exception as e:
        print(f"爬取失败: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check', methods=['POST'])
def check_links():
    """批量检查链接"""
    data = request.json
    links = data.get('links', [])
    
    if not links:
        return jsonify({'success': False, 'error': '没有链接需要检查'})
    
    print(f"开始检查 {len(links)} 个链接")
    
    results = monitor.batch_monitor(links, max_workers=2)
    
    stats = {'total': len(results), 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for r in results:
        if r['风险等级'] == 'CRITICAL': stats['critical'] += 1
        elif r['风险等级'] == 'HIGH': stats['high'] += 1
        elif r['风险等级'] == 'MEDIUM': stats['medium'] += 1
        else: stats['low'] += 1
    
    return jsonify({'success': True, 'results': results, 'statistics': stats})

@app.route('/screenshots/<filename>')
def get_screenshot(filename):
    """获取截图"""
    try:
        filepath = os.path.join('screenshots', filename)
        if os.path.exists(filepath):
            return send_file(filepath)
        return jsonify({'success': False, 'error': '截图不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

if __name__ == '__main__':
    os.makedirs('reports', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('screenshots', exist_ok=True)
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
友情链接监控系统
功能：
1. 检查友情链接的可访问性
2. 检测网站内容变化
3. 识别非法内容（赌博、成人、钓鱼等）
4. 检查域名状态（是否过期、是否被转让）
5. 监控网站跳转
6. 生成监控报告
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import whois
from datetime import datetime, timedelta, timezone
import json
import csv
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import base64

class FriendlyLinkMonitor:
    """友情链接监控器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 截图保存目录
        self.screenshot_dir = 'screenshots'
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        
        # 非法内容关键词
        self.illegal_keywords = {
            'gambling': {
                'keywords': ['赌', '博彩', '彩票', '投注', '百家乐', 'casino', 'bet', 'gambl', 'poker', 'slot'],
                'score': 100,
                'label': '赌博'
            },
            'adult': {
                'keywords': ['porn', 'xxx', 'adult video', 'adult movie', 'sex video', 'nude', '色情', '成人视频', '成人电影', '情色', '激情视频', 'av电影', 'av视频'],
                'score': 100,
                'label': '成人内容'
            },
            'phishing': {
                'keywords': ['密码错误', '账号异常', '紧急验证', '账户冻结', '安全验证'],
                'score': 80,
                'label': '钓鱼'
            },
            'fraud': {
                'keywords': ['中奖', '免费领取', '刷单', '兼职', '日赚', '躺赚'],
                'score': 70,
                'label': '诈骗'
            }
        }
        
        # 可疑顶级域名
        self.suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.wang', '.vip', '.club']
        
        # 监控结果
        self.results = []
    
    def check_domain_status(self, url):
        """检查域名状态"""
        result = {
            'domain': '',
            'is_expired': False,
            'is_transferred': False,
            'expiry_date': None,
            'days_until_expiry': None,
            'registrar': None,
            'risk_score': 0,
            'risk_factors': []
        }
        
        try:
            domain = urlparse(url).netloc
            result['domain'] = domain
            
            # 查询WHOIS信息
            w = whois.whois(domain)
            
            # 检查注册商
            if w.registrar:
                result['registrar'] = w.registrar
            
            # 检查过期时间
            if w.expiration_date:
                if isinstance(w.expiration_date, list):
                    expiry_date = w.expiration_date[0]
                else:
                    expiry_date = w.expiration_date
                
                # 处理时区问题：将带时区的datetime转换为不带时区
                if hasattr(expiry_date, 'tzinfo') and expiry_date.tzinfo is not None:
                    from datetime import timezone
                    # 转换为本地时区，然后移除时区信息
                    expiry_date = expiry_date.astimezone(timezone.utc).replace(tzinfo=None)
                
                result['expiry_date'] = expiry_date.strftime('%Y-%m-%d')
                
                days_until_expiry = (expiry_date - datetime.now()).days
                result['days_until_expiry'] = days_until_expiry
                
                if days_until_expiry < 0:
                    result['is_expired'] = True
                    result['risk_score'] += 100
                    result['risk_factors'].append('域名已过期')
                elif days_until_expiry < 30:
                    result['risk_score'] += 50
                    result['risk_factors'].append(f'域名即将过期（{days_until_expiry}天后）')
                elif days_until_expiry < 90:
                    result['risk_score'] += 20
                    result['risk_factors'].append(f'域名将在{days_until_expiry}天后过期')
            
            # 检查更新时间（可能表示域名转让）
            if w.updated_date:
                if isinstance(w.updated_date, list):
                    updated_date = w.updated_date[0]
                else:
                    updated_date = w.updated_date
                
                # 处理时区问题
                if hasattr(updated_date, 'tzinfo') and updated_date.tzinfo is not None:
                    from datetime import timezone
                    updated_date = updated_date.astimezone(timezone.utc).replace(tzinfo=None)
                
                days_since_update = (datetime.now() - updated_date).days
                
                if days_since_update < 30:
                    result['is_transferred'] = True
                    result['risk_score'] += 40
                    result['risk_factors'].append('域名近期更新（可能已转让）')
            
        except Exception as e:
            # WHOIS查询失败不作为风险因素，只记录信息
            result['risk_factors'].append(f'WHOIS查询失败（可能是网络问题）')
        
        return result
    
    def check_website_content(self, url):
        """检查网站内容"""
        result = {
            'is_accessible': False,
            'title': '',
            'final_url': url,
            'has_redirect': False,
            'redirect_chain': [],
            'keywords_found': [],
            'risk_score': 0,
            'risk_factors': []
        }
        
        try:
            # 访问网站
            response = self.session.get(url, timeout=15, allow_redirects=True)
            
            result['is_accessible'] = True
            result['final_url'] = response.url
            
            # 检查跳转是否可疑
            if response.url != url:
                result['has_redirect'] = True
                for hist in response.history:
                    result['redirect_chain'].append(hist.url)
                
                # 判断跳转是否可疑
                from urllib.parse import urlparse
                original_domain = urlparse(url).netloc.lower()
                final_domain = urlparse(response.url).netloc.lower()
                
                # 移除www前缀进行比较
                original_main = original_domain.replace('www.', '')
                final_main = final_domain.replace('www.', '')
                
                # 如果跳转到完全不同的域名，可能是风险
                if original_main != final_main:
                    # 检查是否跳转到可疑域名
                    suspicious_patterns = ['casino', 'bet', 'gambl', 'porn', 'xxx', 'adult', 'sex']
                    is_suspicious = any(p in final_domain for p in suspicious_patterns)
                    
                    if is_suspicious:
                        result['risk_score'] += 100
                        result['risk_factors'].append(f'⚠️ 跳转到可疑域名: {final_domain}')
                    else:
                        # 普通外部跳转，只记录不加分
                        result['risk_factors'].append(f'跳转到外部域名: {final_domain}')
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取标题
            result['title'] = soup.title.string.strip() if soup.title else ''
            
            # 检查JavaScript跳转
            import re
            js_redirect_patterns = [
                r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']',
                r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                r'location\.replace\s*\(\s*["\']([^"\']+)["\']',
                r'location\.href\s*=\s*["\']([^"\']+)["\']',
                r'targetUrl\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\s*=\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in js_redirect_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                for target_url in matches:
                    if target_url.startswith('http://') or target_url.startswith('https://'):
                        from urllib.parse import urlparse
                        target_domain = urlparse(target_url).netloc.lower()
                        original_domain = urlparse(url).netloc.lower()
                        
                        # 提取主域名（去掉所有子域名前缀）
                        def get_main_domain(domain):
                            parts = domain.split('.')
                            if len(parts) >= 2:
                                # 常见的子域名前缀
                                prefixes = ['www', 'm', 'wap', '3g', 'mobile', 'app', 'api', 'cdn', 'static']
                                for prefix in prefixes:
                                    if domain.startswith(prefix + '.'):
                                        domain = domain[len(prefix)+ 1:]
                                        break
                                return domain
                            return domain
                        
                        original_main = get_main_domain(original_domain)
                        target_main = get_main_domain(target_domain)
                        
                        if original_main != target_main:
                            # 检查是否跳转到可疑域名
                            js_suspicious_patterns = ['casino', 'bet', 'gambl', 'porn', 'xxx', 'adult', 'sex', 'qyjhcx', 'el2', 'beisimei']
                            is_suspicious = any(p in target_domain for p in js_suspicious_patterns)
                            
                            if is_suspicious:
                                result['risk_score'] += 100
                                result['risk_factors'].append(f'⚠️ JavaScript跳转到可疑域名: {target_domain}')
                            else:
                                result['risk_factors'].append(f'JavaScript跳转到外部域名: {target_domain}')
                            result['has_redirect'] = True
                            result['redirect_chain'].append(target_url)
                        break
            
            # ===== 智能风险评估算法 =====
            # 第一步：提取网站结构信息
            text = soup.get_text().lower()
            html_text = response.text.lower()
            
            # 获取标题和描述（权重最高）
            title_text = result['title'].lower() if result['title'] else ''
            description = ''
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc.get('content', '').lower()
            
            # 提取导航菜单内容
            nav_text = ''
            nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=lambda x: x and any(k in str(x).lower() for k in ['nav', 'menu', 'header', '导航', '栏目']))
            for nav in nav_elements[:5]:
                nav_text += ' ' + nav.get_text().lower()
            
            # 提取小标题
            headings_text = ''
            for tag in ['h1', 'h2', 'h3', 'h4']:
                headings = soup.find_all(tag)
                for h in headings[:10]:
                    headings_text += ' ' + h.get_text().lower()
            
            # 合并结构文本
            structure_text = nav_text + ' ' + headings_text
            
            # 第二步：关键词分级检测
            # 高风险关键词（明确的博彩/色情品牌，单独出现即可判定）
            high_risk_keywords = {
                'gambling': ['casino', '百家乐', '威尼斯人', '太阳城', '葡京', '新葡京', 'bet365', 'betwin', '188bet', 'betvictor', 'betway', 'betonline', '澳门赌场', '皇冠现金网', '金沙赌场', '赢波网', '傥士咀', '赌波', '波经', '盘口网', '推介网', '赌球', '博球'],
                'adult': ['porn', 'xxx', 'sex video', 'nude', '色情', '成人视频', '成人电影', '淫秽', '乱伦', '裸聊', '性爱视频', 'av电影', 'av视频', '黄片', '约炮', '一夜情', '援交', '卖淫', '嫖娼', '招嫖']
            }
            
            # 中风险关键词（需要组合验证）
            medium_risk_keywords = {
                'gambling': ['赌', '博彩', '彩票', '投注', 'bet', 'slot', 'poker', 'gambl', '必赢', '必胜', '至尊', '豪赢', '赢钱', '提现', '充值', '返水', '返利', '赢波', '足球盘口', '澳门足球', '足球推介', '足球推荐网', '足球咨询', '波胆', '赔率', '让球', '大小球', '滚球', '走地', '亚盘', '欧盘', '水位', '注单', '代理加盟', '招商加盟', '会员注册', '盘口', '推介', '足球'],
                'adult': ['情色', '激情视频', '黄色', '偷拍', '自拍', '走光', '裸体', '黑料', '吃瓜', '爆料', '网红翻车', '明星八卦', '娱乐八卦', '大瓜', '瓜王', '每日大赛', 'mrds', '实时吃瓜'],
                'phishing': ['密码错误', '账号异常', '紧急验证', '账户冻结', '安全验证', '请验证您的身份', '您的账户存在风险', '立即验证', '账户将被冻结'],
                'fraud': ['中奖', '免费领取', '刷单', '兼职', '日赚', '躺赚', '轻松赚钱', '快速致富', '高回报', '零风险', '保本保息', '日入过万']
            }
            
            # 第三步：检测高风险关键词（标题/导航中出现直接判定）
            for category, keywords in high_risk_keywords.items():
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    # 标题/描述中出现
                    if keyword_lower in title_text or keyword_lower in description:
                        result['keywords_found'].append({
                            'category': category,
                            'keyword': keyword,
                            'label': '赌博' if category == 'gambling' else '成人内容',
                            'location': '标题/描述'
                        })
                        result['risk_score'] += 100
                        result['risk_factors'].append(f'⚠️ 标题/描述发现高风险关键词: {keyword}')
                        break
                    # 导航/栏目中出现
                    elif keyword_lower in structure_text:
                        result['keywords_found'].append({
                            'category': category,
                            'keyword': keyword,
                            'label': '赌博' if category == 'gambling' else '成人内容',
                            'location': '导航/栏目'
                        })
                        result['risk_score'] += 100
                        result['risk_factors'].append(f'⚠️ 导航/栏目发现高风险关键词: {keyword}')
                        break
            
            # 第四步：检测中风险关键词（需要组合验证）
            found_medium_keywords = {'gambling': [], 'adult': [], 'phishing': [], 'fraud': []}
            for category, keywords in medium_risk_keywords.items():
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    # 标题/描述中出现（权重高）
                    if keyword_lower in title_text or keyword_lower in description:
                        found_medium_keywords[category].append({'keyword': keyword, 'location': '标题/描述', 'score': 50})
                    # 导航/栏目中出现（权重中）
                    elif keyword_lower in structure_text:
                        found_medium_keywords[category].append({'keyword': keyword, 'location': '导航/栏目', 'score': 40})
                    # 正文中出现（权重低）
                    elif keyword_lower in text or keyword_lower in html_text:
                        found_medium_keywords[category].append({'keyword': keyword, 'location': '正文', 'score': 15})
            
            # 第五步：组合验证（同一类别多个关键词才判定）
            for category, found_list in found_medium_keywords.items():
                if len(found_list) >= 2:
                    # 多个关键词组合，风险更高
                    keywords_str = ', '.join([k['keyword'] for k in found_list[:3]])
                    total_score = sum(k['score'] for k in found_list)
                    result['risk_score'] += min(total_score, 100)  # 上限100分
                    result['risk_factors'].append(f'发现多个{category}相关关键词: {keywords_str}')
                    for k in found_list:
                        result['keywords_found'].append({
                            'category': category,
                            'keyword': k['keyword'],
                            'label': category,
                            'location': k['location']
                        })
                elif len(found_list) == 1:
                    # 单个关键词，只有标题/导航才加分
                    k = found_list[0]
                    if k['location'] in ['标题/描述', '导航/栏目']:
                        result['risk_score'] += k['score']
                        result['keywords_found'].append({
                            'category': category,
                            'keyword': k['keyword'],
                            'label': category,
                            'location': k['location']
                        })
                        result['risk_factors'].append(f'{k["location"]}发现{category}关键词: {k["keyword"]}')
                    # 正文中的单个中风险关键词不加分
            
            # 第六步：检测正常网站特征（降低误判）
            normal_features = ['icp', '备案', '工信部', '公安机关', '版权所有', 'copyright', '©', '政府', 'edu', 'org', 'gov.cn']
            normal_count = sum(1 for f in normal_features if f in text or f in html_text)
            if normal_count >= 2:
                result['risk_score'] = max(0, result['risk_score'] - 20)
                result['risk_factors'].append('✓ 检测到正规网站特征')
            
            # 检查HTTPS - 不加分，只做提示
            if not response.url.startswith('https'):
                result['risk_factors'].append('提示: 未使用HTTPS')
            
        except requests.exceptions.Timeout:
            # 超时不应该直接判定为无法访问，可能是网络问题
            result['risk_factors'].append('访问超时（可能是网络波动）')
            result['risk_score'] += 5
        except requests.exceptions.ConnectionError as e:
            result['risk_factors'].append(f'连接错误: {str(e)[:50]}')
            result['risk_score'] += 10
        except requests.exceptions.SSLError:
            result['risk_factors'].append('SSL证书异常')
            result['risk_score'] += 40
        except Exception as e:
            result['risk_factors'].append(f'访问异常: {str(e)[:50]}')
            result['risk_score'] += 5
        
        return result
    
    def check_domain_features(self, url):
        """检查域名特征"""
        result = {
            'domain': '',
            'risk_score': 0,
            'risk_factors': []
        }
        
        try:
            domain = urlparse(url).netloc
            result['domain'] = domain
            
            # 检查可疑顶级域名
            for tld in self.suspicious_tlds:
                if domain.endswith(tld):
                    result['risk_score'] += 50
                    result['risk_factors'].append(f'使用可疑顶级域名: {tld}')
            
            # 检查域名长度
            if len(domain) > 50:
                result['risk_score'] += 20
                result['risk_factors'].append('域名异常长')
            
            # 检查数字比例
            digit_ratio = sum(c.isdigit() for c in domain) / max(len(domain), 1)
            if digit_ratio > 0.4:
                result['risk_score'] += 30
                result['risk_factors'].append(f'域名包含大量数字 ({digit_ratio:.1%})')
            
        except Exception as e:
            result['risk_factors'].append(f'域名分析异常: {str(e)}')
        
        return result
    
    def take_screenshot(self, url, name):
        """获取网站截图"""
        screenshot_path = None
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            import os
            
            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1280,800')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-browser-side-navigation')
            
            # 云端环境使用Chromium
            chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
            if os.path.exists(chrome_bin):
                chrome_options.binary_location = chrome_bin
            
            # 创建浏览器实例
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(90)  # 增加超时时间到90秒
            
            try:
                driver.get(url)
                time.sleep(3)  # 增加等待时间到3秒
                
                # 生成截图文件名
                safe_name = re.sub(r'[^\w\-]', '_', name)[:50]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_filename = f'{safe_name}_{timestamp}.png'
                screenshot_path = os.path.join(self.screenshot_dir, screenshot_filename)
                
                # 确保目录存在
                if not os.path.exists(self.screenshot_dir):
                    os.makedirs(self.screenshot_dir)
                
                # 保存截图
                driver.save_screenshot(screenshot_path)
                print(f"✓ 截图已保存: {screenshot_path}")
                
            finally:
                driver.quit()
                
        except ImportError:
            print("⚠️ Selenium未安装，跳过截图")
        except Exception as e:
            print(f"截图失败: {str(e)[:200]}")
        
        return screenshot_path
    
    def monitor_link(self, link_info):
        """监控单个友情链接（Web应用接口）"""
        name = link_info.get('name', '')
        url = link_info.get('url', '')
        
        print(f"正在检查: {name} - {url}")
        
        result = {
            '链接名称': name,
            '链接地址': url,
            '检查时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '总风险分数': 0,
            '风险等级': 'LOW',
            '风险因素': [],
            '域名状态': {},
            '网站内容': {},
            '域名特征': {}
        }
        
        # 1. 检查域名特征
        domain_result = self.check_domain_features(url)
        result['域名特征'] = domain_result
        result['总风险分数'] += domain_result['risk_score']
        result['风险因素'].extend(domain_result['risk_factors'])
        
        # 2. 检查网站内容
        content_result = self.check_website_content(url)
        result['网站内容'] = content_result
        result['总风险分数'] += content_result['risk_score']
        result['风险因素'].extend(content_result['risk_factors'])

        # 如果HTTP失败且不是HTTPS，尝试HTTPS
        if url.startswith('http://') and not content_result.get('is_accessible', False):
            https_url = url.replace('http://', 'https://')
            content_result_https = self.check_website_content(https_url)
            if content_result_https.get('is_accessible', False):
                result['网站内容'] = content_result_https
                result['总风险分数'] += content_result_https['risk_score']
                result['风险因素'].extend(content_result_https['risk_factors'])
                url = https_url

        # 3. 检查域名状态（WHOIS查询较慢，可选）
        if result['总风险分数'] > 0 or link_info.get('check_whois', False):
            domain_status = self.check_domain_status(url)
            result['域名状态'] = domain_status
            result['总风险分数'] += domain_status['risk_score']
            result['风险因素'].extend(domain_status['risk_factors'])

        # 4. 获取网站截图（所有网站都截图，便于人工审核）
        # 如果HTTP截图失败，尝试HTTPS
        screenshot_path = self.take_screenshot(url, name)
        if not screenshot_path and url.startswith('http://'):
            screenshot_path = self.take_screenshot(url.replace('http://', 'https://'), name)
        result['网站截图'] = screenshot_path
        
        # 确定风险等级
        if result['总风险分数'] >= 100:
            result['风险等级'] = 'CRITICAL'
        elif result['总风险分数'] >= 70:
            result['风险等级'] = 'HIGH'
        elif result['总风险分数'] >= 40:
            result['风险等级'] = 'MEDIUM'
        else:
            result['风险等级'] = 'LOW'
        
        return result
    
    def batch_monitor(self, links, max_workers=3):
        """批量监控友情链接"""
        print(f"\n开始监控 {len(links)} 个友情链接...")
        print("="*70)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_link = {executor.submit(self.monitor_link, link): link for link in links}
            
            for future in as_completed(future_to_link):
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 显示进度
                    risk_level = result['风险等级']
                    risk_score = result['总风险分数']
                    print(f"  ✓ {result['链接名称']} - 风险等级: {risk_level} (分数: {risk_score})")
                    
                except Exception as e:
                    print(f"  ✗ 监控失败: {e}")
                
                # 延时避免请求过快
                time.sleep(0.5)
        
        return results
    
    def generate_report(self, results, output_file='friendly_link_monitor_report.xlsx'):
        """生成监控报告"""
        import pandas as pd
        from openpyxl import load_workbook
        from openpyxl.drawing.image import Image as XLImage
        from openpyxl.styles import Alignment
        
        # 准备数据
        data = []
        for result in results:
            data.append({
                '链接名称': result['链接名称'],
                '链接地址': result['链接地址'],
                '风险等级': result['风险等级'],
                '总风险分数': result['总风险分数'],
                '风险因素': '; '.join(result['风险因素']),
                '网站标题': result['网站内容'].get('title', ''),
                '最终URL': result['网站内容'].get('final_url', ''),
                '是否跳转': '是' if result['网站内容'].get('has_redirect', False) else '否',
                '是否可访问': '是' if result['网站内容'].get('is_accessible', False) else '否',
                '域名过期时间': result['域名状态'].get('expiry_date', ''),
                '域名剩余天数': result['域名状态'].get('days_until_expiry', ''),
                '注册商': result['域名状态'].get('registrar', ''),
                '网站截图': result.get('网站截图', ''),
                '检查时间': result['检查时间']
            })
        
        # 生成Excel报告
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        # 添加截图到Excel
        try:
            wb = load_workbook(output_file)
            ws = wb.active
            
            # 调整列宽
            ws.column_dimensions['M'].width = 30  # 截图列
            
            # 插入截图
            for idx, result in enumerate(results, start=2):
                screenshot_path = result.get('网站截图')
                if screenshot_path and os.path.exists(screenshot_path):
                    try:
                        img = XLImage(screenshot_path)
                        img.width = 200
                        img.height = 150
                        cell_address = f'M{idx}'
                        ws.add_image(img, cell_address)
                        ws.row_dimensions[idx].height = 120
                    except Exception as e:
                        print(f"插入截图失败: {e}")
            
            wb.save(output_file)
        except Exception as e:
            print(f"Excel截图处理失败: {e}")
        
        print(f"\n✓ 监控报告已生成: {output_file}")
        
        # 生成HTML报告
        html_file = output_file.replace('.xlsx', '.html')
        self.generate_html_report(results, html_file)
    
    def generate_html_report(self, results, output_file):
        """生成HTML可视化报告"""
        total_links = len(results)
        critical_links = sum(1 for r in results if r['风险等级'] == 'CRITICAL')
        high_links = sum(1 for r in results if r['风险等级'] == 'HIGH')
        medium_links = sum(1 for r in results if r['风险等级'] == 'MEDIUM')
        low_links = sum(1 for r in results if r['风险等级'] == 'LOW')
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>友情链接监控报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ 
            text-align: center; 
            color: #333; 
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary {{ 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{ 
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{ color: #666; font-size: 14px; margin-bottom: 10px; }}
        .summary-card .number {{ font-size: 36px; font-weight: bold; color: #333; }}
        .summary-card.critical .number {{ color: #e74c3c; }}
        .summary-card.high .number {{ color: #e67e22; }}
        .summary-card.medium .number {{ color: #f39c12; }}
        .summary-card.low .number {{ color: #27ae60; }}
        
        table {{ 
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{ 
            background: #34495e;
            color: white;
            padding: 15px 10px;
            text-align: left;
            font-weight: 500;
        }}
        td {{ 
            padding: 12px 10px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{ background: #f8f9fa; }}
        
        .risk-critical {{ background-color: #ffebee !important; }}
        .risk-high {{ background-color: #fff3e0 !important; }}
        .risk-medium {{ background-color: #fffde7 !important; }}
        .risk-low {{ background-color: #e8f5e9 !important; }}
        
        .badge {{ 
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-critical {{ background: #e74c3c; color: white; }}
        .badge-high {{ background: #e67e22; color: white; }}
        .badge-medium {{ background: #f39c12; color: white; }}
        .badge-low {{ background: #27ae60; color: white; }}
        
        .url-link {{ 
            color: #3498db;
            text-decoration: none;
            word-break: break-all;
        }}
        .url-link:hover {{ text-decoration: underline; }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 友情链接监控报告</h1>
        
        <div class="summary">
            <div class="summary-card">
                <h3>监控链接数</h3>
                <div class="number">{total_links}</div>
            </div>
            <div class="summary-card critical">
                <h3>严重风险</h3>
                <div class="number">{critical_links}</div>
            </div>
            <div class="summary-card high">
                <h3>高风险</h3>
                <div class="number">{high_links}</div>
            </div>
            <div class="summary-card medium">
                <h3>中等风险</h3>
                <div class="number">{medium_links}</div>
            </div>
            <div class="summary-card low">
                <h3>低风险</h3>
                <div class="number">{low_links}</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 50px;">序号</th>
                    <th style="width: 150px;">链接名称</th>
                    <th style="width: 250px;">链接地址</th>
                    <th style="width: 80px;">风险等级</th>
                    <th style="width: 80px;">风险分数</th>
                    <th style="width: 300px;">风险因素</th>
                    <th style="width: 200px;">网站截图</th>
                    <th style="width: 150px;">检查时间</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for idx, result in enumerate(results, 1):
            risk_level = result['风险等级']
            risk_class = f'risk-{risk_level.lower()}'
            badge_class = f'badge-{risk_level.lower()}'
            
            # 处理截图
            screenshot_html = ''
            screenshot_path = result.get('网站截图')
            if screenshot_path and os.path.exists(screenshot_path):
                # 使用相对路径
                screenshot_rel = os.path.relpath(screenshot_path, os.path.dirname(output_file))
                screenshot_html = f'<img src="{screenshot_rel}" style="max-width: 180px; max-height: 120px; border: 1px solid #ddd; border-radius: 4px;" onclick="window.open(this.src)" title="点击查看大图">'
            
            html += f"""
                <tr class="{risk_class}">
                    <td>{idx}</td>
                    <td>{result['链接名称']}</td>
                    <td><a href="{result['链接地址']}" class="url-link" target="_blank">{result['链接地址']}</a></td>
                    <td><span class="badge {badge_class}">{risk_level}</span></td>
                    <td>{result['总风险分数']}</td>
                    <td>{'; '.join(result['风险因素'][:3])}</td>
                    <td>{screenshot_html}</td>
                    <td>{result['检查时间']}</td>
                </tr>
"""
        
        html += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>风险等级说明: CRITICAL(严重) ≥ 100分 | HIGH(高) ≥ 70分 | MEDIUM(中) ≥ 40分 | LOW(低) < 40分</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ HTML报告已生成: {output_file}")
    
    def save_baseline(self, results, baseline_file='friendly_link_baseline.json'):
        """保存基线数据（用于对比变化）"""
        baseline = {}
        
        for result in results:
            url = result['链接地址']
            baseline[url] = {
                'name': result['链接名称'],
                'title': result['网站内容'].get('title', ''),
                'final_url': result['网站内容'].get('final_url', ''),
                'check_time': result['检查时间']
            }
        
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 基线数据已保存: {baseline_file}")
    
    def compare_with_baseline(self, results, baseline_file='friendly_link_baseline.json'):
        """与基线数据对比变化"""
        if not os.path.exists(baseline_file):
            print("基线文件不存在，跳过对比")
            return
        
        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
        
        changes = []
        
        for result in results:
            url = result['链接地址']
            
            if url in baseline:
                old_data = baseline[url]
                
                # 检查标题变化
                old_title = old_data.get('title', '')
                new_title = result['网站内容'].get('title', '')
                
                if old_title != new_title:
                    changes.append({
                        'url': url,
                        'name': result['链接名称'],
                        'type': '标题变化',
                        'old': old_title,
                        'new': new_title
                    })
                
                # 检查URL跳转变化
                old_final_url = old_data.get('final_url', '')
                new_final_url = result['网站内容'].get('final_url', '')
                
                if old_final_url != new_final_url:
                    changes.append({
                        'url': url,
                        'name': result['链接名称'],
                        'type': '跳转变化',
                        'old': old_final_url,
                        'new': new_final_url
                    })
        
        if changes:
            print("\n⚠️  检测到以下变化:")
            for change in changes:
                print(f"  - {change['name']}: {change['type']}")
                print(f"    旧: {change['old']}")
                print(f"    新: {change['new']}")
        else:
            print("\n✓ 未检测到明显变化")


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              友情链接监控系统 v1.0                            ║
║                                                               ║
║  功能：监控友情链接安全 → 检测非法内容 → 生成监控报告        ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # 友情链接列表（示例）
    friendly_links = [
        {'name': '示例网站1', 'url': 'https://example1.com', 'check_whois': True},
        {'name': '示例网站2', 'url': 'https://example2.com', 'check_whois': False},
        # 添加更多友情链接...
    ]
    
    # 从文件读取友情链接
    import pandas as pd
    
    links_file = 'friendly_links.xlsx'  # 友情链接文件
    
    if os.path.exists(links_file):
        df = pd.read_excel(links_file)
        friendly_links = []
        
        for _, row in df.iterrows():
            friendly_links.append({
                'name': row.get('链接名称', ''),
                'url': row.get('链接地址', ''),
                'check_whois': row.get('检查WHOIS', False)
            })
        
        print(f"从文件读取到 {len(friendly_links)} 个友情链接\n")
    else:
        print("提示: 未找到友情链接文件，使用示例数据")
        print(f"请创建文件 {links_file}，包含列: 链接名称, 链接地址, 检查WHOIS\n")
    
    # 创建监控器
    monitor = FriendlyLinkMonitor()
    
    # 执行监控
    results = monitor.batch_monitor(friendly_links, max_workers=2)
    
    # 生成报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'friendly_link_monitor_report_{timestamp}.xlsx'
    
    monitor.generate_report(results, report_file)
    
    # 保存基线
    baseline_file = 'friendly_link_baseline.json'
    monitor.save_baseline(results, baseline_file)
    
    # 对比基线
    monitor.compare_with_baseline(results, baseline_file)
    
    # 打印摘要
    print("\n" + "="*70)
    print("监控摘要:")
    print("="*70)
    
    total = len(results)
    critical = sum(1 for r in results if r['风险等级'] == 'CRITICAL')
    high = sum(1 for r in results if r['风险等级'] == 'HIGH')
    medium = sum(1 for r in results if r['风险等级'] == 'MEDIUM')
    low = sum(1 for r in results if r['风险等级'] == 'LOW')
    
    print(f"监控链接总数: {total}")
    print(f"严重风险: {critical}")
    print(f"高风险: {high}")
    print(f"中等风险: {medium}")
    print(f"低风险: {low}")
    
    if critical > 0 or high > 0:
        print("\n⚠️  发现高风险链接，请立即处理！")
        for r in results:
            if r['风险等级'] in ['CRITICAL', 'HIGH']:
                print(f"  - {r['链接名称']}: {r['链接地址']}")
                print(f"    风险因素: {'; '.join(r['风险因素'][:3])}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()

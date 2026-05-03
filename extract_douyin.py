# -*- coding: utf-8 -*-
"""
抖音视频下载器 - 从抖音分享页提取视频地址，无水印下载

使用方法:
    python extract_douyin_v2.py <抖音分享链接或视频链接>

示例:
    python extract_douyin_v2.py https://v.douyin.com/Chg8rMhuxGk/
    python extract_douyin_v2.py https://www.douyin.com/video/7633314702449554842

依赖:
    pip install requests

更新日志:
    v2.0 (2026-05-03) - 修复抖音JS反爬验证问题
    - 使用iPhone UA获取重定向，绕过JS验证页面
    - 支持多种视频URL提取模式
    - 提取视频ID、标题、作者信息
"""

import re
import os
import sys
import argparse
import requests


def extract_video_info(share_url):
    """从抖音分享链接提取视频信息"""
    
    headers_mobile = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    print(f"[1/3] 获取分享页: {share_url[:60]}...")
    
    try:
        # Step 1: 获取重定向后的URL
        resp = requests.get(share_url, headers=headers_mobile, timeout=30, allow_redirects=True)
        final_url = resp.url
        print(f"      重定向到: {final_url[:80]}...")
        
        # 从重定向URL提取视频ID
        video_id = ""
        m_id = re.search(r'/video/(\d+)', final_url)
        if m_id:
            video_id = m_id.group(1)
            print(f"      视频ID: {video_id}")
        else:
            # 从原始URL尝试提取
            m_id = re.search(r'/video/(\d+)', share_url)
            if m_id:
                video_id = m_id.group(1)
                print(f"      视频ID: {video_id}")
        
        # Step 2: 用重定向后的URL获取实际页面
        resp2 = requests.get(final_url, headers=headers_mobile, timeout=30)
        html = resp2.text
        print(f"      获取HTML: {len(html)} 字节")
        
    except Exception as e:
        print(f"[ERROR] 获取失败: {e}")
        return None
    
    # 修复Unicode转义
    html_fixed = html.replace('\\u002F', '/').replace('\\/', '/').replace('\\u0026', '&')
    
    # 方式1: 标准play_addr模式
    video_url = None
    m = re.search(r'"play_addr":\{"uri":"[^"]+","url_list":\["(https?://[^"]+)"', html_fixed)
    if m:
        video_url = m.group(1)
        print(f"      [模式1] 找到play_addr")
    
    # 方式2: 备用play_addr模式（带不同前缀）
    if not video_url:
        m = re.search(r'"play_addr_.*?":\{"uri":"[^"]+","url_list":\["(https?://[^"]+)"', html_fixed)
        if m:
            video_url = m.group(1)
            print(f"      [模式2] 找到play_addr变体")
    
    # 方式3: playUrl字段
    if not video_url:
        m = re.search(r'"playUrl":"(https?://[^"]+)"', html_fixed)
        if m:
            video_url = m.group(1)
            print(f"      [模式3] 找到playUrl")
    
    # 方式4: video_url字段
    if not video_url:
        m = re.search(r'"video_url":"(https?://[^"]+)"', html_fixed)
        if m:
            video_url = m.group(1)
            print(f"      [模式4] 找到video_url")
    
    # 方式5: 直接找mp4链接
    if not video_url:
        urls = re.findall(r'https://[^"\'>\s]+\.mp4[^"\'>\s]*', html_fixed)
        if urls:
            video_url = urls[0]
            print(f"      [模式5] 找到mp4链接")
    
    if not video_url:
        print("[FAIL] 未找到视频地址")
        print("      可能原因: 视频已删除/私密/需要登录")
        return None
    
    # 清理URL
    video_url = video_url.replace('\\u0026', '&').replace('\\/', '/')
    
    # 替换playwm为play（无水印）
    if 'playwm' in video_url:
        video_url = video_url.replace('playwm', 'play')
        print("      已转换为无水印版本")
    
    # 获取标题
    title = ""
    m2 = re.search(r'"desc":"([^"]*)"', html_fixed)
    if m2:
        title = m2.group(1)
    
    # 获取作者
    author = ""
    m3 = re.search(r'"nickname":"([^"]*)"', html_fixed)
    if m3:
        author = m3.group(1)
    
    print(f"[2/3] 提取成功!")
    if title:
        print(f"      标题: {title[:60]}")
    if author:
        print(f"      作者: {author}")
    
    return {
        'video_url': video_url,
        'title': title,
        'author': author,
        'video_id': video_id
    }


def download_video(video_info, save_dir=None):
    """下载视频到指定目录"""
    
    if save_dir is None:
        save_dir = os.path.join(os.path.expanduser("~"), "Desktop", "抖音视频")
    
    os.makedirs(save_dir, exist_ok=True)
    
    # 生成文件名
    safe_title = re.sub(r'[\\/:*?"<>|]', '_', video_info['title'][:40]) if video_info['title'] else "douyin_video"
    if video_info['video_id']:
        filename = f"{video_info['video_id']}_{safe_title}.mp4"
    else:
        filename = f"{safe_title}.mp4"
    
    filepath = os.path.join(save_dir, filename)
    
    print(f"[3/3] 下载视频...")
    print(f"      保存到: {filepath}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://www.douyin.com/',
    }
    
    try:
        resp = requests.get(video_info['video_url'], headers=headers, timeout=180, stream=True)
        resp.raise_for_status()
        
        total_size = 0
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                total_size += len(chunk)
        
        size_mb = total_size / (1024.0 * 1024.0)
        
        if total_size > 10000:
            print(f"[SUCCESS] 下载成功!")
            print(f"          文件: {filename}")
            print(f"          大小: {size_mb:.2f} MB")
            print(f"          路径: {filepath}")
            return filepath
        else:
            print(f"[FAIL] 文件太小 ({total_size} bytes)，下载失败")
            os.remove(filepath)
            return None
            
    except Exception as e:
        print(f"[FAIL] 下载失败: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return None


def main():
    parser = argparse.ArgumentParser(description='抖音视频下载器 - 无水印')
    parser.add_argument('url', help='抖音分享链接或视频链接')
    parser.add_argument('-o', '--output', help='保存目录 (默认: ~/Desktop/抖音视频)')
    args = parser.parse_args()
    
    url = args.url.strip()
    
    # 验证URL
    if 'douyin.com' not in url:
        print("[ERROR] 请提供有效的抖音链接")
        sys.exit(1)
    
    print("=" * 50)
    print("抖音视频下载器 v2.0 (无水印)")
    print("=" * 50)
    
    # 提取视频信息
    video_info = extract_video_info(url)
    if not video_info:
        sys.exit(1)
    
    # 下载视频
    result = download_video(video_info, args.output)
    if not result:
        sys.exit(1)
    
    print("=" * 50)


if __name__ == '__main__':
    main()

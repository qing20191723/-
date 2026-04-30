# -*- coding: utf-8 -*-
"""
抖音视频下载器 - 从抖音分享页提取视频地址并下载（无水印）

用法:
    python extract_douyin.py <抖音分享链接>
    
示例:
    python extract_douyin.py https://v.douyin.com/Chg8rMhuxGk/
    python extract_douyin.py https://www.douyin.com/video/7633314702449554842

依赖:
    pip install requests

注意:
    本脚本从抖音分享页HTML中提取 play_addr 视频地址直接下载，
    绕过抖音API的认证要求，实现无水印下载。
"""

import re
import os
import sys
import argparse
import requests

# 从分享页HTML中提取视频信息和下载地址
def extract_video_info(share_url):
    """从抖音分享链接提取视频信息"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    print(f"[1/3] 访问分享页: {share_url[:60]}...")
    
    try:
        resp = requests.get(share_url, headers=headers, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
        print(f"      获取HTML: {len(html)} 字节")
    except Exception as e:
        print(f"[ERROR] 访问失败: {e}")
        return None
    
    # 修复 Unicode 转义
    html_fixed = html.replace('\\u002F', '/').replace('\\/', '/')
    
    # 提取视频ID
    video_id = ""
    m_id = re.search(r'/video/(\d+)', html_fixed)
    if m_id:
        video_id = m_id.group(1)
        print(f"      视频ID: {video_id}")
    
    # 提取 play_addr 视频URL
    m = re.search(r'"play_addr":\{"uri":"[^"]+","url_list":\["(https?://[^"]+)"', html_fixed)
    if not m:
        print("[FAIL] 未找到 play_addr 视频地址")
        # 尝试其他模式
        m = re.search(r'"play_addr_.*?":\{"uri":"[^"]+","url_list":\["(https?://[^"]+)"', html_fixed)
    
    if not m:
        print("[FAIL] 所有提取模式均失败")
        return None
    
    video_url = m.group(1)
    # 将 playwm 替换为 play（去掉水印）
    video_url = video_url.replace('playwm', 'play')
    
    # 提取标题
    title = ""
    m2 = re.search(r'"desc":"([^"]*)"', html_fixed)
    if m2:
        title = m2.group(1)
    
    # 提取作者
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
        'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
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
            print(f"[FAIL] 文件过小 ({total_size} bytes)，可能下载失败")
            os.remove(filepath)
            return None
            
    except Exception as e:
        print(f"[FAIL] 下载失败: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return None


def main():
    parser = argparse.ArgumentParser(description='抖音视频下载器（无水印）')
    parser.add_argument('url', help='抖音分享链接或视频链接')
    parser.add_argument('-o', '--output', help='保存目录（默认: 桌面/抖音视频）')
    args = parser.parse_args()
    
    url = args.url.strip()
    
    # 验证URL
    if 'douyin.com' not in url:
        print("[ERROR] 请提供有效的抖音链接")
        sys.exit(1)
    
    print("=" * 50)
    print("抖音视频下载器 (无水印)")
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

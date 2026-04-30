# -*- coding: utf-8 -*-
"""
抖音视频下载脚本 v2.0
使用 api.douyin.wtf 免费API解析下载
支持: 抖音分享链接、短网址、正常网址
用法: python download_douyin_v2.py <抖音链接> [保存目录]
"""
import urllib.parse
import urllib.request
import json
import subprocess
import os
import re
import sys

def get_video_data(url):
    """调用API获取视频信息"""
    encoded = urllib.parse.quote(url, safe="")
    api = f"https://api.douyin.wtf/api/hybrid/video_data?url={encoded}&minimal=false"
    
    req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())

def download_video(video_url, filepath):
    """下载视频文件"""
    result = subprocess.run(
        ["curl", "-L", "-o", filepath, "-s", "-H", "User-Agent: Mozilla/5.0", "--max-time", "180", video_url],
        capture_output=True,
        timeout=200
    )
    return os.path.exists(filepath) and os.path.getsize(filepath) > 10000

def main():
    if len(sys.argv) < 2:
        print("用法: python download_douyin_v2.py <抖音链接> [保存目录]")
        print("示例: python download_douyin_v2.py https://v.douyin.com/xxxxx/")
        sys.exit(1)
    
    url = sys.argv[1]
    save_dir = sys.argv[2] if len(sys.argv) > 2 else r"D:\AI绘画\抖音视频\抖音热门视频"
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"链接: {url}")
    print("=" * 50)
    
    # 获取视频数据
    print("正在解析...")
    data = get_video_data(url)
    
    if data.get("code") != 200:
        print(f"解析失败: {data}")
        sys.exit(1)
    
    video_data = data["data"]
    author = video_data.get("author", {})
    nickname = author.get("nickname", "unknown")
    title = video_data.get("desc", "") or video_data.get("title", "")
    
    print(f"作者: {nickname}")
    print(f"标题: {title[:60] if title else '(无标题)'}")
    
    # 获取下载链接
    video_url = None
    for path in ["video.play_addr.url_list", "nva.play_addr.url_list"]:
        keys = path.split(".")
        obj = video_data
        for k in keys:
            obj = obj.get(k, {}) if isinstance(obj, dict) else {}
        if isinstance(obj, list) and obj:
            video_url = obj[0].replace("\\u002F", "/").replace("\\/", "/")
            break
    
    if not video_url:
        # 尝试download API
        print("尝试直接下载API...")
        encoded = urllib.parse.quote(url, safe="")
        dl_api = f"https://api.douyin.wtf/api/download?url={encoded}&prefix=true&with_watermark=false"
        dl_req = urllib.request.Request(dl_api, headers={"User-Agent": "Mozilla/5.0"})
        dl_resp = urllib.request.urlopen(dl_req, timeout=120)
        
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', f"{nickname}_{title[:20]}")
        filename = f"{safe_name}.mp4" if title else f"douyin_{nickname}.mp4"
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, "wb") as f:
            while True:
                chunk = dl_resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"\n[成功] {filename}")
            print(f"大小: {size_mb:.2f} MB")
            print(f"路径: {filepath}")
        else:
            print("下载失败")
            os.remove(filepath) if os.path.exists(filepath) else None
            sys.exit(1)
        return
    
    # 下载
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', f"{nickname}_{title[:20]}")
    filename = f"{safe_name}.mp4" if title else f"douyin_{nickname}.mp4"
    filepath = os.path.join(save_dir, filename)
    
    print(f"\n正在下载: {filename}")
    if download_video(video_url, filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"\n[成功] {filename}")
        print(f"大小: {size_mb:.2f} MB")
        print(f"路径: {filepath}")
    else:
        print("下载失败")
        sys.exit(1)

if __name__ == "__main__":
    main()

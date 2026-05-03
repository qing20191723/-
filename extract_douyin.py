# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(errors='replace')
"""
抖音视频下载器 v2.0 - 使用iPhone UA获取重定向，绕过JS反爬验证

使用方法:
    python extract_douyin.py <抖音分享链接或视频链接> [保存目录]

示例:
    python extract_douyin.py https://v.douyin.com/Chg8rMhuxGk/
    python extract_douyin.py https://www.douyin.com/video/7633314702449554842 D:\videos
"""
import re, os, sys, urllib.request, http.cookiejar, json

def extract_douyin(url, save_dir):
    # 创建cookie和opener
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    # Step 1: 用iPhone UA获取分享链接的重定向
    share_req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
    })
    try:
        resp = opener.open(share_req, timeout=15)
        redirect_url = resp.geturl()
        print("Redirect URL: " + redirect_url[:100])
        html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print("[ERROR] Failed to fetch redirect URL: " + str(e))
        return False

    # Step 2: 如果重定向到iesdouyin.com，用同样UA再次请求
    if 'iesdouyin.com' in redirect_url:
        try:
            req2 = urllib.request.Request(redirect_url, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
            })
            resp2 = opener.open(req2, timeout=15)
            html = resp2.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print("[WARN] Failed to fetch iesdouyin page, using redirect page: " + str(e))

    # 修复unicode转义
    html = html.replace('\\u002F', '/').replace('\\/', '/')

    # 提取视频ID
    vid = None
    m_vid = re.search(r'video/(\d+)', redirect_url)
    if m_vid:
        vid = m_vid.group(1)
    if not vid:
        m_vid = re.search(r'/(\d{15,})', html)
        if m_vid:
            vid = m_vid.group(1)
    print("Video ID: " + (vid or "not found"))

    # 提取视频标题
    title = ""
    m_title = re.search(r'"desc"\s*:\s*"([^"]{1,200})"', html)
    if m_title:
        title = m_title.group(1)
        print("Title: " + title[:80])

    # 提取作者
    m_author = re.search(r'"nickname"\s*:\s*"([^"]+)"', html)
    if m_author:
        print("Author: " + m_author.group(1))

    # 提取视频URL - 多种模式
    video_url = None

    # 模式1: play_addr url_list (无水印)
    m1 = re.search(r'"play_addr"\s*:\s*\{[^}]*"url_list"\s*:\s*\[\s*"([^"]+)"', html)
    if m1:
        video_url = m1.group(1)

    # 模式2: playUrl
    if not video_url:
        m2 = re.search(r'"playUrl"\s*:\s*"(https?://[^"]+)"', html)
        if m2:
            video_url = m2.group(1)

    # 模式3: video_url
    if not video_url:
        m3 = re.search(r'"video_url"\s*:\s*"(https?://[^"]+)"', html)
        if m3:
            video_url = m3.group(1)

    # 模式4: 所有视频CDN URL
    if not video_url:
        m4 = re.search(r'(https://[^"]*?/video/[^"]+\.mp4[^"]*)', html)
        if m4:
            video_url = m4.group(1)

    if not video_url:
        print("[FAIL] No video URL found")
        return False

    # 去水印: playwm -> play
    video_url = video_url.replace('playwm', 'play')
    print("Video URL: " + video_url[:100] + "...")

    # 构建文件名
    if title:
        safe_title = re.sub(r'[\[\]\\/:*?"<>|]', '_', title[:50])
    elif vid:
        safe_title = vid
    else:
        safe_title = "douyin_video"
    
    # 如果作者名存在，添加到文件名
    m_author2 = re.search(r'"nickname"\s*:\s*"([^"]+)"', html)
    if m_author2:
        author = re.sub(r'[\[\]\\/:*?"<>|]', '_', m_author2.group(1)[:20])
        filename = author + "_" + safe_title + ".mp4"
    else:
        filename = safe_title + ".mp4"

    filepath = os.path.join(save_dir, filename)
    print("Downloading to: " + filepath)

    # 下载视频
    try:
        req_dl = urllib.request.Request(video_url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'
        })
        resp_dl = opener.open(req_dl, timeout=120)
        data = resp_dl.read()
        
        with open(filepath, 'wb') as f:
            f.write(data)
        
        size_mb = len(data) / (1024.0 * 1024.0)
        print("[SUCCESS] Downloaded!")
        print("File: " + filepath)
        print("Size: %.2f MB" % size_mb)
        return True
    except Exception as e:
        print("[FAIL] Download error: " + str(e))
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_douyin.py <douyin_url> [save_dir]")
        sys.exit(1)
    
    url = sys.argv[1]
    save_dir = sys.argv[2] if len(sys.argv) > 2 else r"D:\AI绘画\抖音视频\抖音热门视频"
    os.makedirs(save_dir, exist_ok=True)
    
    success = extract_douyin(url, save_dir)
    sys.exit(0 if success else 1)

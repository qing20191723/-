# 抖音视频下载工具

从抖音分享页提取视频地址并下载（无水印）。

## 文件说明

| 文件 | 说明 |
|------|------|
| `extract_douyin.py` | ✅ 当前可用 - 从HTML提取play_addr直接下载 |
| `download_douyin_v2.py` | ⚠️ 已失效 - 依赖外部API |

## 使用方法

### 安装依赖

```bash
pip install requests
```

### 下载视频

```bash
# 使用分享链接
python extract_douyin.py https://v.douyin.com/Chg8rMhuxGk/

# 指定保存目录
python extract_douyin.py https://v.douyin.com/Chg8rMhuxGk/ -o D:\下载
```

### 工作原理

1. 访问抖音分享链接（自动跟随重定向）
2. 从HTML中用正则提取 `play_addr` 视频地址
3. 将 `playwm` 替换为 `play`（去除水印）
4. 直接下载视频文件

## 注意事项

- 分享链接格式：`https://v.douyin.com/xxxxx/`
- 视频链接格式：`https://www.douyin.com/video/xxxxxxxxx`
- 部分视频可能因抖音页面结构变化而提取失败
- 如遇失败，请提 Issue 反馈

## 更新记录

- 2026-04-30: 创建 extract_douyin.py，基于HTML提取play_addr方案
- 之前的 download_douyin_v2.py 依赖的API已失效

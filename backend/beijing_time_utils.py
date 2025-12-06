"""
北京时间工具函数
v6.5.5: 所有时间使用北京时间(UTC+8)
"""
import pytz
from datetime import datetime

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

def get_beijing_time():
    """获取当前北京时间(带时区信息)"""
    return datetime.now(BEIJING_TZ)

def get_beijing_time_str(fmt="%Y-%m-%d %H:%M:%S"):
    """获取当前北京时间字符串"""
    return get_beijing_time().strftime(fmt)

def format_beijing_time(dt, fmt="%Y-%m-%d %H:%M:%S"):
    """格式化datetime对象为北京时间字符串"""
    if dt.tzinfo is None:
        # 如果没有时区信息,假设是UTC
        dt = pytz.utc.localize(dt)
    # 转换到北京时区
    beijing_dt = dt.astimezone(BEIJING_TZ)
    return beijing_dt.strftime(fmt)

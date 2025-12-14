import calendar
import re
from datetime import date
from typing import Dict


class ParamNormalizer:
    """参数规范化类，负责规范化日期和参数"""

    @staticmethod
    def normalize_date_str(val: str, is_end: bool = False) -> str:
        """规范化日期字符串，支持 '2025-10-01'、'2025-10'、'25-10'、'2025年10月'、'25年10月' 等"""
        if not val:
            return ""
        s = val.strip()
        # 中文格式替换
        s = s.replace("年", "-").replace("月", "-").replace("日", "")
        s = re.sub(r"-+", "-", s)
        s = s.strip("-")
        # 完整 yyyy-mm-dd
        m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
        if m:
            y, mth, d = map(int, m.groups())
        else:
            # yyyy-mm
            m = re.match(r"^(\d{4})-(\d{1,2})$", s)
            if m:
                y, mth = map(int, m.groups())
                d = None
            else:
                # yy-mm 或 yy-mm-dd
                m = re.match(r"^(\d{2})-(\d{1,2})(?:-(\d{1,2}))?$", s)
                if m:
                    y = 2000 + int(m.group(1))
                    mth = int(m.group(2))
                    d = int(m.group(3)) if m.group(3) else None
                else:
                    return val  # 保留原值
        if not (1 <= mth <= 12):
            return val
        if d is None:
            # 无具体日，起始用1号，结束用当月最后一天
            d = calendar.monthrange(y, mth)[1] if is_end else 1
        try:
            dt = date(y, mth, d)
        except Exception:
            return val
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def normalize_params(params: Dict) -> Dict:
        """规范化参数字典"""
        # 创建新字典，保留所有原始参数
        normalized = dict(params)

        # 处理 limit：默认20，非数字或None则重置为20，最大50
        limit_val = normalized.get("limit", 20)
        if not isinstance(limit_val, int) or limit_val is None:
            limit_val = 20
        if limit_val > 50:
            limit_val = 50
        if limit_val <= 0:
            limit_val = 20
        normalized["limit"] = limit_val

        # 规范化日期
        start_date = ParamNormalizer.normalize_date_str(normalized.get("start_date", ""), is_end=False)
        end_date = ParamNormalizer.normalize_date_str(normalized.get("end_date", ""), is_end=True)
        target_date = ParamNormalizer.normalize_date_str(normalized.get("target_date", ""), is_end=False)
        if start_date and not end_date:
            end_date = ParamNormalizer.normalize_date_str(start_date, is_end=True)
        if start_date:
            normalized["start_date"] = start_date
        if end_date:
            normalized["end_date"] = end_date
        if target_date:
            normalized["target_date"] = target_date

        return normalized



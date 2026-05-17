#!/usr/bin/env python3
"""
title_scenarizer.py - 亚马逊标题场景化改写工具

两种使用方式：
1. 作为 generate-html.py 的后处理：transform_boring_title(raw_title)
2. 作为 AI Prompt 的补充规则：直接读取 SYSTEM_PROMPT 补充到 System Prompt 中

使用示例（作为后处理）：
    from title_scenarizer import transform_boring_title
    new_title = transform_boring_title("Amazon Basics 垃圾桶哪款值得买")
    # → "极简工作室的低维护选择：Amazon Basics 不锈钢静音垃圾桶实测"

使用示例（Prompt 补充）：
    from title_scenarizer import SYSTEM_PROMPT
    # 将 SYSTEM_PROMPT 内容作为补充规则传给 AI
"""
import re
import os

# ============================================================
# 场景化改写 System Prompt（供 AI 调用时使用）
# ============================================================

SYSTEM_PROMPT = """# Role
你是一位精通 SEO 流量密码的科技博客独立开发者（Indie Hacker），专门为技术人员、远程办公人群（WFH）和极客群体撰写高转化率的 Amazon 联盟营销（Affiliate）导购文章。

# Objective
将输入的、千篇一律的传统导购标题（形如：Amazon Basics XXX哪款值得买），改写为具有【极客感】、【场景化】、【解决痛点】且符合 2026 年 Google Helpful Content 算法的高点击率标题。

# Target Audience
独立开发者、程序员、数码极客、追求高效率与极简生活的年轻职场人。

# Core Rules (铁律)
1. 严禁出现"哪款值得买"、"推荐"、"评测"、"深度横评"等采集感强烈的词汇。
2. 必须包含品牌词"Amazon Basics"或其核心产品名。
3. 必须符合【极客/独立开发/高效率/远程办公】的其中一个生活场景。
4. 严格禁止输出任何解释、标点符号包裹、或除最终标题外的任何文字。

# Scenario Mapping Matrix (场景映射规则)

## 1. 桌面/数码/办公类（如：显示器臂、笔记本支架、排插、线缆管理、桌面收纳）
   - 场景：生产力黑客、打造完美 Setup、无绳化、护颈/健康
   - 关键词：桌面美学、无线化、颈椎拯救、整洁、高效、拒绝线材地狱
   - 公式：[痛点/目标] + [产品核心词] + [实测/差异化]

## 2. 居家/收纳/清洁类（如：垃圾桶、床底收纳、洗衣篮、鞋柜、收纳盒）
   - 场景：极简主义（Minimalism）、低维护、不占用核心空间、懒人效率
   - 关键词：极简空间、隐藏式、低维护、空间管理、极客卧室
   - 公式：[空间/极简场景] + [产品核心词] + [差异化痛点解决]

## 3. 厨房/生活/个护类（如：厨刀套装、硅胶烘焙垫、空气净化器、加湿器）
   - 场景：深夜食堂、高效率下厨、极客养生、无脑维护
   - 关键词：深夜食堂、高效下厨、回血、硬核、懒人必备、程序员书房
   - 公式：[独立开发/极客场景] + [产品核心词] + [生活品质升级]

## 4. 洗衣/卫浴类（如：洗衣篮、晾衣架、毛巾架、浴垫）
   - 场景：高效动线、有限空间利用、懒人洗衣、整洁
   - 关键词：阳台收纳、浴室整洁、懒人洗衣动线、整洁干爽
   - 公式：[懒人/效率场景] + [产品核心词] + [生活痛点解决]

# 输出格式
只输出最终改写后的标题文本，不要包含任何前缀、后缀、引号。

# Few-Shot Examples
- Input: Amazon Basics 垃圾桶哪款值得买
- Output: 极简工作室的低维护选择：Amazon Basics 不锈钢静音垃圾桶实测

- Input: Amazon Basics 桌面收纳盒哪款值得买
- Output: 拒绝线材地狱：如何用 Amazon Basics 收纳盒拯救独立开发者的桌面

- Input: Amazon Basics 硅胶烘焙垫哪款值得买
- Output: 程序员的深夜高效下厨：免洗省时的 Amazon Basics 硅胶烘焙垫体验

- Input: Amazon Basics 厨刀套装哪款值得买？
- Output: 代码敲累了的无脑解压：Amazon Basics 高碳钢厨刀套装硬核上手

- Input: Amazon Basics 显示器臂
- Output: 拯救久坐颈椎：2026 程序员书房必备的 Amazon Basics 气压显示器支架

- Input: Amazon Basics 空气净化器 vs 加湿器——你应该买哪个？
- Output: 机房级舒适度？程序员书房的 Amazon Basics 空气净化器与加湿器选购指南

- Input: Amazon Basics 床底收纳哪款值得买
- Output: 小户型极简空间管理：Amazon Basics 隐藏式床底收纳箱实测

- Input: Amazon Basics 洗衣篮哪款值得买
- Output: 程序员的高效洗衣动线：Amazon Basics 折叠洗衣篮空间利用实测
"""


# ============================================================
# 场景关键词映射（用于代码级转换）
# ============================================================

# 产品类型 → 场景关键词 + 改写模板
SCENARIO_MAP = {
    # 桌面/数码/办公类
    "monitor arm": {
        "scenario": "拯救久坐颈椎",
        "keywords": ["桌面美学", "颈椎拯救", "显示器支架", "程序员书房", "生产力"],
        "template": "拯救久坐颈椎：{year} 程序员书房必备的 Amazon Basics 气压显示器支架"
    },
    "monitor-arm": {
        "scenario": "拯救久坐颈椎",
        "keywords": ["桌面美学", "颈椎拯救", "显示器支架", "程序员书房", "生产力"],
        "template": "拯救久坐颈椎：{year} 程序员书房必备的 Amazon Basics 气压显示器支架"
    },
    "laptop stand": {
        "scenario": "颈椎拯救+散热",
        "keywords": ["笔记本支架", "散热", "颈椎", "程序员书房", "桌面美学"],
        "template": "程序员书房的颈椎拯救方案：Amazon Basics 笔记本支架硬核实测"
    },
    "laptop-stand": {
        "scenario": "颈椎拯救+散热",
        "keywords": ["笔记本支架", "散热", "颈椎", "程序员书房", "桌面美学"],
        "template": "程序员书房的颈椎拯救方案：Amazon Basics 笔记本支架硬核实测"
    },
    "power strip": {
        "scenario": "拒绝线材地狱",
        "keywords": ["排插", "桌面美学", "用电安全", "无线化", "整洁"],
        "template": "拒绝线材地狱：Amazon Basics 排插让独立开发者桌面整洁的实测方案"
    },
    "power-strip": {
        "scenario": "拒绝线材地狱",
        "keywords": ["排插", "桌面美学", "用电安全", "无线化", "整洁"],
        "template": "拒绝线材地狱：Amazon Basics 排插让独立开发者桌面整洁的实测方案"
    },
    "desk organizer": {
        "scenario": "拒绝线材地狱",
        "keywords": ["桌面收纳", "线材管理", "整洁", "效率", "拒绝杂乱"],
        "template": "拒绝线材地狱：如何用 Amazon Basics 收纳盒拯救独立开发者的桌面"
    },
    "desk-organizer": {
        "scenario": "拒绝线材地狱",
        "keywords": ["桌面收纳", "线材管理", "整洁", "效率", "拒绝杂乱"],
        "template": "拒绝线材地狱：如何用 Amazon Basics 收纳盒拯救独立开发者的桌面"
    },
    "cable management": {
        "scenario": "拒绝线材地狱",
        "keywords": ["理线", "整洁", "桌面美学", "效率", "无线化"],
        "template": "独立开发者的桌面整洁指南：Amazon Basics 理线神器实测"
    },
    # 居家/收纳/清洁类
    "trash can": {
        "scenario": "极简工作室",
        "keywords": ["极简空间", "低维护", "静音", "整洁", "工作室"],
        "template": "极简工作室的低维护选择：Amazon Basics 不锈钢静音垃圾桶实测"
    },
    "trash-can": {
        "scenario": "极简工作室",
        "keywords": ["极简空间", "低维护", "静音", "整洁", "工作室"],
        "template": "极简工作室的低维护选择：Amazon Basics 不锈钢静音垃圾桶实测"
    },
    "under-bed storage": {
        "scenario": "极简空间管理",
        "keywords": ["极简空间", "隐藏式收纳", "小户型", "空间管理", "卧室整洁"],
        "template": "小户型极客的空间管理：Amazon Basics 隐藏式床底收纳实测"
    },
    "under-bed": {
        "scenario": "极简空间管理",
        "keywords": ["极简空间", "隐藏式收纳", "小户型", "空间管理", "卧室整洁"],
        "template": "小户型极客的空间管理：Amazon Basics 隐藏式床底收纳实测"
    },
    "laundry basket": {
        "scenario": "高效洗衣动线",
        "keywords": ["洗衣动线", "空间利用", "整洁", "懒人", "高效"],
        "template": "程序员的高效洗衣动线：Amazon Basics 折叠洗衣篮空间利用实测"
    },
    "laundry-basket": {
        "scenario": "高效洗衣动线",
        "keywords": ["洗衣动线", "空间利用", "整洁", "懒人", "高效"],
        "template": "程序员的高效洗衣动线：Amazon Basics 折叠洗衣篮空间利用实测"
    },
    "shoe rack": {
        "scenario": "玄关整洁",
        "keywords": ["玄关整洁", "空间管理", "极简", "门口", "有序"],
        "template": "独立开发者玄关术：Amazon Basics 鞋架让进门区域井井有条"
    },
    # 厨房/生活/个护类
    "knife set": {
        "scenario": "深夜食堂",
        "keywords": ["深夜食堂", "厨刀", "高效下厨", "程序员", "解压"],
        "template": "代码敲累了的无脑解压：Amazon Basics 高碳钢厨刀套装硬核上手"
    },
    "knife-set": {
        "scenario": "深夜食堂",
        "keywords": ["深夜食堂", "厨刀", "高效下厨", "程序员", "解压"],
        "template": "代码敲累了的无脑解压：Amazon Basics 高碳钢厨刀套装硬核上手"
    },
    "silicone baking mat": {
        "scenario": "深夜高效下厨",
        "keywords": ["深夜食堂", "免洗", "省时", "烘焙", "程序员"],
        "template": "程序员的深夜高效下厨：免洗省时的 Amazon Basics 硅胶烘焙垫体验"
    },
    "silicone-baking-mat": {
        "scenario": "深夜高效下厨",
        "keywords": ["深夜食堂", "免洗", "省时", "烘焙", "程序员"],
        "template": "程序员的深夜高效下厨：免洗省时的 Amazon Basics 硅胶烘焙垫体验"
    },
    "air purifier": {
        "scenario": "程序员书房舒适度",
        "keywords": ["空气净化", "程序员书房", "舒适度", "健康", "WFH"],
        "template": "WFH 程序员书房的空气健康管理：Amazon Basics 空气净化器实测"
    },
    "humidifier": {
        "scenario": "程序员书房舒适度",
        "keywords": ["加湿", "程序员书房", "舒适度", "健康", "WFH", "干燥"],
        "template": "独立开发者书房的干燥救星：Amazon Basics 加湿器与空气净化器选购指南"
    },
    "air-purifier": {
        "scenario": "程序员书房舒适度",
        "keywords": ["空气净化", "程序员书房", "舒适度", "健康", "WFH"],
        "template": "WFH 程序员书房的空气健康管理：Amazon Basics 空气净化器实测"
    },
    "humidifier": {
        "scenario": "程序员书房舒适度",
        "keywords": ["加湿", "程序员书房", "舒适度", "健康", "WFH", "干燥"],
        "template": "独立开发者书房的干燥救星：Amazon Basics 加湿器与空气净化器选购指南"
    },
    "shower head": {
        "scenario": "程序员浴室效率",
        "keywords": ["浴室", "高效", "舒适", "早起", "洗澡", "程序员"],
        "template": "程序员的高效晨间routine：Amazon Basics 节水花洒硬核体验"
    },
    "shower-head": {
        "scenario": "程序员浴室效率",
        "keywords": ["浴室", "高效", "舒适", "早起", "洗澡", "程序员"],
        "template": "程序员的高效晨间routine：Amazon Basics 节水花洒硬核体验"
    },
    "pillow": {
        "scenario": "程序员睡眠质量",
        "keywords": ["睡眠", "程序员", "休息", "舒适", "颈椎", "回血"],
        "template": "程序员的高质量睡眠方案：Amazon Basics 枕头选购避坑指南"
    },
    "storage container": {
        "scenario": "极简厨房",
        "keywords": ["厨房收纳", "极简", "整洁", "空间管理", "懒人"],
        "template": "独立开发者的极简厨房：Amazon Basics 收纳盒让储物井井有条"
    },
    "food storage": {
        "scenario": "极简厨房",
        "keywords": ["厨房收纳", "极简", "整洁", "空间管理", "懒人"],
        "template": "独立开发者的极简厨房：Amazon Basics 食品收纳盒实测"
    },
    "electric kettle": {
        "scenario": "程序员深夜能量站",
        "keywords": ["热水", "茶", "咖啡", "深夜", "程序员", "回血"],
        "template": "程序员深夜能量站：Amazon Basics 电热水壶的快速烧水实测"
    },
    "electric-kettle": {
        "scenario": "程序员深夜能量站",
        "keywords": ["热水", "茶", "咖啡", "深夜", "程序员", "回血"],
        "template": "程序员深夜能量站：Amazon Basics 电热水壶的快速烧水实测"
    },
    "toaster": {
        "scenario": "程序员早餐效率",
        "keywords": ["早餐", "吐司", "高效", "快速", "懒人", "程序员"],
        "template": "程序员的高效早餐方案：Amazon Basics 吐司炉对比横评"
    },
    "coffee maker": {
        "scenario": "程序员咖啡需求",
        "keywords": ["咖啡", "早茶", "程序员", "能量", "提神", "WFH"],
        "template": "WFH 程序员的咖啡续命方案：Amazon Basics 咖啡机横评"
    },
    "coffeemaker": {
        "scenario": "程序员咖啡需求",
        "keywords": ["咖啡", "早茶", "程序员", "能量", "提神", "WFH"],
        "template": "WFH 程序员的咖啡续命方案：Amazon Basics 咖啡机横评"
    },
}


_SLUG_KEYS = {
    # 桌面/数码/办公类
    'monitor-arm': ('monitor-arm', '显示器臂'),
    'monitor arm': ('monitor-arm', '显示器臂'),
    '显示器臂': ('monitor-arm', '显示器臂'),
    'laptop-stand': ('laptop-stand', '笔记本支架'),
    'laptop stand': ('laptop-stand', '笔记本支架'),
    '笔记本支架': ('laptop-stand', '笔记本支架'),
    'power-strip': ('power-strip', '排插'),
    'power strip': ('power-strip', '排插'),
    '排插': ('power-strip', '排插'),
    'desk-organizer': ('desk-organizer', '桌面收纳盒'),
    'desk organizer': ('desk-organizer', '桌面收纳盒'),
    '桌面收纳盒': ('desk-organizer', '桌面收纳盒'),
    '收纳盒': ('desk-organizer', '桌面收纳盒'),
    'cable management': ('cable-management', '理线'),
    'cable-management': ('cable-management', '理线'),
    '线材管理': ('cable-management', '理线'),
    # 居家/收纳/清洁类
    'trash-can': ('trash-can', '垃圾桶'),
    'trash can': ('trash-can', '垃圾桶'),
    '垃圾桶': ('trash-can', '垃圾桶'),
    'under-bed storage': ('under-bed-storage', '床底收纳'),
    'under-bed-storage': ('under-bed-storage', '床底收纳'),
    '床底收纳': ('under-bed-storage', '床底收纳'),
    'laundry-basket': ('laundry-basket', '洗衣篮'),
    'laundry basket': ('laundry-basket', '洗衣篮'),
    '洗衣篮': ('laundry-basket', '洗衣篮'),
    'shoe rack': ('shoe-rack', '鞋架'),
    'shoe-rack': ('shoe-rack', '鞋架'),
    '鞋架': ('shoe-rack', '鞋架'),
    # 厨房/生活/个护类
    'knife-set': ('knife-set', '厨刀套装'),
    'knife set': ('knife-set', '厨刀套装'),
    '厨刀套装': ('knife-set', '厨刀套装'),
    '厨刀': ('knife-set', '厨刀套装'),
    'silicone-baking-mat': ('silicone-baking-mat', '硅胶烘焙垫'),
    'silicone baking mat': ('silicone-baking-mat', '硅胶烘焙垫'),
    '硅胶烘焙垫': ('silicone-baking-mat', '硅胶烘焙垫'),
    '烘焙垫': ('silicone-baking-mat', '硅胶烘焙垫'),
    'air-purifier': ('air-purifier', '空气净化器'),
    'air purifier': ('air-purifier', '空气净化器'),
    '空气净化器': ('air-purifier', 'air-purifier'),
    'humidifier': ('humidifier', '加湿器'),
    '加湿器': ('humidifier', '加湿器'),
    'shower-head': ('shower-head', '花洒'),
    'shower head': ('shower-head', '花洒'),
    '花洒': ('shower-head', '花洒'),
    'pillow': ('pillow', '枕头'),
    '枕头': ('pillow', '枕头'),
    'storage-container': ('storage-container', '收纳盒'),
    'food-storage': ('food-storage', '食品收纳'),
    'electric-kettle': ('electric-kettle', '电热水壶'),
    'electric kettle': ('electric-kettle', '电热水壶'),
    '电热水壶': ('electric-kettle', '电热水壶'),
    'toaster': ('toaster', '吐司炉'),
    '吐司炉': ('toaster', '吐司炉'),
    'coffee-maker': ('coffee-maker', '咖啡机'),
    'coffee maker': ('coffee-maker', '咖啡机'),
    '咖啡机': ('coffee-maker', '咖啡机'),
}

SCENARIO_MAP = {
    # 桌面/数码/办公类
    'monitor-arm': {
        'scenario': '拯救久坐颈椎',
        'template': '拯救久坐颈椎：{year} 程序员书房必备的 Amazon Basics 气压显示器支架'
    },
    'laptop-stand': {
        'scenario': '颈椎拯救+散热',
        'template': '程序员书房的颈椎拯救方案：Amazon Basics 笔记本支架硬核实测'
    },
    'power-strip': {
        'scenario': '拒绝线材地狱',
        'template': '拒绝线材地狱：Amazon Basics 排插让独立开发者桌面整洁的实测方案'
    },
    'desk-organizer': {
        'scenario': '拒绝线材地狱',
        'template': '拒绝线材地狱：如何用 Amazon Basics 收纳盒拯救独立开发者的桌面'
    },
    'cable-management': {
        'scenario': '拒绝线材地狱',
        'template': '独立开发者的桌面整洁指南：Amazon Basics 理线神器实测'
    },
    # 居家/收纳/清洁类
    'trash-can': {
        'scenario': '极简工作室',
        'template': '极简工作室的低维护选择：Amazon Basics 不锈钢静音垃圾桶实测'
    },
    'under-bed-storage': {
        'scenario': '极简空间管理',
        'template': '小户型极客的空间管理：Amazon Basics 隐藏式床底收纳实测'
    },
    'laundry-basket': {
        'scenario': '高效洗衣动线',
        'template': '程序员的高效洗衣动线：Amazon Basics 折叠洗衣篮空间利用实测'
    },
    'shoe-rack': {
        'scenario': '玄关整洁',
        'template': '独立开发者玄关术：Amazon Basics 鞋架让进门区域井井有条'
    },
    # 厨房/生活/个护类
    'knife-set': {
        'scenario': '深夜食堂',
        'template': '代码敲累了的无脑解压：Amazon Basics 高碳钢厨刀套装硬核上手'
    },
    'silicone-baking-mat': {
        'scenario': '深夜高效下厨',
        'template': '程序员的深夜高效下厨：免洗省时的 Amazon Basics 硅胶烘焙垫体验'
    },
    'air-purifier': {
        'scenario': '程序员书房舒适度',
        'template': 'WFH 程序员书房的空气健康管理：Amazon Basics 空气净化器实测'
    },
    'humidifier': {
        'scenario': '程序员书房舒适度',
        'template': '独立开发者书房的干燥救星：Amazon Basics 加湿器与空气净化器选购指南'
    },
    'shower-head': {
        'scenario': '程序员浴室效率',
        'template': '程序员的高效晨间routine：Amazon Basics 节水花洒硬核体验'
    },
    'pillow': {
        'scenario': '程序员睡眠质量',
        'template': '程序员的高质量睡眠方案：Amazon Basics 枕头选购避坑指南'
    },
    'storage-container': {
        'scenario': '极简厨房',
        'template': '独立开发者的极简厨房：Amazon Basics 收纳盒让储物井井有条'
    },
    'food-storage': {
        'scenario': '极简厨房',
        'template': '独立开发者的极简厨房：Amazon Basics 食品收纳盒实测'
    },
    'electric-kettle': {
        'scenario': '程序员深夜能量站',
        'template': '程序员深夜能量站：Amazon Basics 电热水壶的快速烧水实测'
    },
    'toaster': {
        'scenario': '程序员早餐效率',
        'template': '程序员的高效早餐方案：Amazon Basics 吐司炉对比横评'
    },
    'coffee-maker': {
        'scenario': '程序员咖啡需求',
        'template': 'WFH 程序员的咖啡续命方案：Amazon Basics 咖啡机横评'
    },
}


def _extract_product_slug(title: str) -> str:
    """从标题提取产品核心词（用于查表）"""
    t = title.lower()
    # Remove "amazon basics" prefix
    t = re.sub(r'^amazon\s*basics?\s*', '', t)
    # Remove boring suffixes
    t = re.sub(r'\s*(哪款值得买|值得买|推荐|评测|横评|对比|哪个好|怎么样|是否值得|\?|？).*$', '', t)
    # Normalize separators
    t = re.sub(r'[-\s]+', '-', t)
    return t.strip().strip('-')



def transform_boring_title(raw_title: str, year: int = 2026) -> str:
    """
    将千篇一律的 Amazon Basics 导购标题转为场景化标题。
    
    转换逻辑：
    1. 从原始标题提取产品核心词（中英文均可）
    2. 通过双向映射表 _SLUG_KEYS 查到标准化 key
    3. 从 SCENARIO_MAP 查到模板，生成场景化标题
    4. 如果未命中，保留原始标题
    """
    # 尝试提取并查表
    slug = _extract_product_slug(raw_title)
    
    # 直接查 slug
    key = slug
    if key not in SCENARIO_MAP:
        # 尝试中文产品名查表
        for k, v in _SLUG_KEYS.items():
            std_key, chinese = v
            if chinese in raw_title or k in raw_title.lower():
                key = std_key
                break
    
    if key in SCENARIO_MAP:
        entry = SCENARIO_MAP[key]
        template = entry['template']
        result = template.format(year=year)
        return result
    
    # 未命中，不改写
    return raw_title


def detect_if_boring(title: str) -> bool:
    """
    检测标题是否属于"千篇一律的导购风"。
    如果检测到以下关键词，返回 True：
    - 哪款值得买
    - 推荐
    - 评测
    - 横评
    - 对比
    - 哪个好
    - 怎么样
    - 是否值得
    """
    boring_patterns = [
        '哪款值得买', '值得买', '推荐', '评测', '横评', '对比',
        '哪个好', '怎么样', '是否值得', '值得入手', '入手指南'
    ]
    t = title.lower()
    return any(p in t for p in boring_patterns)


if __name__ == '__main__':
    import sys
    test_titles = [
        "Amazon Basics 垃圾桶哪款值得买",
        "Amazon Basics 桌面收纳盒哪款值得买",
        "Amazon Basics 硅胶烘焙垫哪款值得买",
        "Amazon Basics 厨刀套装哪款值得买？",
        "Amazon Basics 显示器臂",
        "Amazon Basics 空气净化器 vs 加湿器——你应该买哪个？",
        "Amazon Basics 床底收纳哪款值得买",
        "Amazon Basics 洗衣篮哪款值得买",
        "Amazon Basics 笔记本支架",
        "Amazon Basics 电热水壶",
    ]
    
    print("=== 标题场景化改写测试 ===\n")
    for title in test_titles:
        new_title = transform_boring_title(title)
        is_boring = detect_if_boring(title)
        marker = "🔴" if is_boring else "🟢"
        print(f"{marker} 原始: {title}")
        if new_title != title:
            print(f"  ✅ 改写: {new_title}")
        else:
            print(f"  ➡️  保持: {new_title}")
        print()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速启动测试 - 验证程序可以正常初始化，不会因为常量名或字段名问题报错
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 60)
print("数据要素交易材料生成工具 - 启动测试")
print("=" * 60)

try:
    print("\n[1/5] 导入配置常量...")
    from config import TRADING_SCENARIOS as SCENES, UPDATE_FREQUENCIES, REQUIRED_MATERIALS
    print(f"  ✓ 交易场景: {len(SCENES)} 种")
    print(f"  ✓ 更新频率: {len(UPDATE_FREQUENCIES)} 种")
    print(f"  ✓ 必填材料: {len(REQUIRED_MATERIALS)} 种")
    for i, scene in enumerate(SCENES, 1):
        print(f"    {i}. {scene}")
except Exception as e:
    print(f"  ✗ 配置导入失败: {e}")
    sys.exit(1)

try:
    print("\n[2/5] 导入核心模块...")
    from core import (
        ProjectInfo, MaterialList, TemplateGenerator,
        ContentValidator, PackageOutput, RecordManager
    )
    print("  ✓ 所有核心模块导入成功")
except Exception as e:
    print(f"  ✗ 核心模块导入失败: {e}")
    sys.exit(1)

try:
    print("\n[3/5] 初始化核心对象...")
    pi = ProjectInfo()
    ml = MaterialList()
    tg = TemplateGenerator(pi, ml)
    cv = ContentValidator(pi, ml)
    rm = RecordManager()
    print("  ✓ 所有核心对象初始化成功")
except Exception as e:
    print(f"  ✗ 核心对象初始化失败: {e}")
    sys.exit(1)

try:
    print("\n[4/5] 测试字段名兼容性...")
    pi.scene = "金融风控"
    assert pi.trading_scene == "金融风控", "scene -> trading_scene 别名失败"
    
    pi.trading_scene = "市场营销"
    assert pi.scene == "市场营销", "trading_scene -> scene 别名失败"
    
    pi.usage_limits = "仅限内部使用"
    assert pi.usage_restrictions == "仅限内部使用", "usage_limits 别名失败"
    print("  ✓ 字段名兼容性测试通过")
except Exception as e:
    print(f"  ✗ 字段名兼容性测试失败: {e}")
    sys.exit(1)

try:
    print("\n[5/5] 测试序列化兼容性...")
    data = ml.to_dict()
    assert "items" in data, "to_dict 缺少 items 键"
    assert "materials" in data, "to_dict 缺少 materials 键"
    assert len(data["items"]) == len(data["materials"]), "items 和 materials 长度不一致"
    
    ml2 = MaterialList()
    ml2.from_dict(data)
    assert len(ml2.items) == len(ml.items), "from_dict 恢复失败"
    print("  ✓ 序列化兼容性测试通过")
except Exception as e:
    print(f"  ✗ 序列化兼容性测试失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ 所有启动测试通过！程序可以正常运行")
print("=" * 60)
print("\n启动命令: python main.py")

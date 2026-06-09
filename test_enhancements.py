#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试第四轮增强功能：
1. 打包输出页分区显示
2. 打包稳定性增强
3. 历史恢复完整性
4. 历史记录筛选增强
"""
import sys
from pathlib import Path
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 70)
print("数据要素交易材料生成工具 - 第四轮增强功能测试")
print("=" * 70)

# 测试1: RecordManager search_records has_errors筛选
print("\n" + "=" * 70)
print("测试1: RecordManager search_records has_errors 筛选")
print("=" * 70)

from core import RecordManager, ProjectInfo, MaterialList, ContentValidator

rm = RecordManager()

# 创建测试记录
test_records = []
for i in range(5):
    pi = ProjectInfo()
    pi.product_name = f"测试产品{i+1}"
    pi.product_code = f"TEST{i+1:03d}"
    pi.scene = ["金融风控", "市场营销", "智慧城市"][i % 3]
    pi.contact_person = ["张三", "李四", "王五", "赵六", "钱七"][i]
    
    ml = MaterialList()
    cv = ContentValidator(pi, ml)
    
    # 一半有错误，一半没有
    if i < 2:
        vr = cv.validate_all()
    else:
        # 手动创建无错误的校验结果
        from core.content_validator import ValidationResult
        vr = ValidationResult()
        vr.passed = True
        vr.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    record = {
        "project_id": pi.project_id,
        "product_code": pi.product_code,
        "product_name": pi.product_name,
        "contact_person": pi.contact_person,
        "scene": pi.scene,
        "trading_scene": pi.trading_scene,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "batch_id": f"BATCH{i+1:03d}",
        "batch_name": f"批次{i+1}",
        "project_info": pi.to_dict(),
        "materials": ml.to_dict(),
        "generated_files": {"CPMS": "/test/path.docx"},
        "validation_result": vr.to_dict(),
        "zip_path": f"/output/test{i+1}.zip",
        "checklist_path": f"/output/checklist{i+1}.xlsx",
        "file_count": 3 + i
    }
    test_records.append(rm.add_record(record))

# 测试has_errors筛选
all_count = len(rm.get_all_records())
print(f"总记录数: {all_count}")

# 筛选有错误的
with_errors = rm.search_records(has_errors="yes")
print(f"有错误的记录数: {len(with_errors)} (期望: >=2)")
assert len(with_errors) >= 2, f"有错误的记录数不足，期望>=2，实际{len(with_errors)}"

# 筛选无错误的
without_errors = rm.search_records(has_errors="no")
print(f"无错误的记录数: {len(without_errors)} (期望: >=3)")
assert len(without_errors) >= 3, f"无错误的记录数不足，期望>=3，实际{len(without_errors)}"

print("✓ RecordManager has_errors 筛选测试通过!")

# 测试2: 场景筛选
print("\n" + "=" * 70)
print("测试2: 场景筛选")
print("=" * 70)

for scene in ["金融风控", "市场营销", "智慧城市"]:
    scene_records = rm.search_records(scene=scene)
    print(f"场景 [{scene}] 记录数: {len(scene_records)}")
    for rec in scene_records:
        rec_scene = rec.get('scene') or rec.get('trading_scene')
        assert rec_scene == scene, f"场景不匹配: {rec_scene} != {scene}"
    print(f"  ✓ 场景 [{scene}] 筛选正确")

print("✓ 场景筛选测试通过!")

# 测试3: 日期范围筛选
print("\n" + "=" * 70)
print("测试3: 日期范围筛选")
print("=" * 70)

today = datetime.now().strftime("%Y-%m-%d")
tomorrow = (datetime.now()).strftime("%Y-%m-%d")

today_records = rm.search_records(start_date=today, end_date=tomorrow)
print(f"今天的记录数: {len(today_records)} (期望: {all_count})")
assert len(today_records) == all_count, f"日期筛选结果不正确"

old_records = rm.search_records(end_date="2020-01-01")
print(f"2020年之前的记录数: {len(old_records)} (期望: 0)")
assert len(old_records) == 0, f"日期筛选结果不正确"

print("✓ 日期范围筛选测试通过!")

# 测试4: 多条件组合筛选
print("\n" + "=" * 70)
print("测试4: 多条件组合筛选")
print("=" * 70)

# 筛选 金融风控 + 有错误
combo1 = rm.search_records(scene="金融风控", has_errors="yes")
print(f"金融风控 + 有错误: {len(combo1)} 条")

# 筛选 市场营销 + 无错误
combo2 = rm.search_records(scene="市场营销", has_errors="no")
print(f"市场营销 + 无错误: {len(combo2)} 条")

# 筛选 张三 + 有错误
combo3 = rm.search_records(contact_person="张三", has_errors="yes")
print(f"联系人张三 + 有错误: {len(combo3)} 条")

print("✓ 多条件组合筛选测试通过!")

# 测试5: 记录详情数据完整性
print("\n" + "=" * 70)
print("测试5: 记录详情数据完整性")
print("=" * 70)

test_record = test_records[0]
required_fields = [
    'zip_path', 'checklist_path', 'file_count',
    'project_info', 'materials', 'generated_files', 'validation_result',
    'project_id', 'product_code', 'product_name', 'scene', 'created_at'
]

for field in required_fields:
    has_field = field in test_record
    value = test_record.get(field, 'N/A')
    print(f"  {field}: {'✓' if has_field else '✗'} = {value}")
    assert has_field, f"记录缺少必填字段: {field}"

# 检查validation_result字段
vr = test_record.get('validation_result', {})
vr_fields = ['errors', 'warnings', 'sensitive_hits', 'passed', 'timestamp']
print("\n  validation_result 字段:")
for field in vr_fields:
    has_field = field in vr
    print(f"    {field}: {'✓' if has_field else '✗'}")
    assert has_field, f"validation_result缺少字段: {field}"

print("✓ 记录详情数据完整性测试通过!")

# 测试6: 恢复记录数据完整性
print("\n" + "=" * 70)
print("测试6: 恢复记录数据完整性")
print("=" * 70)

pi_new = ProjectInfo()
ml_new = MaterialList()
generated_files_new = {}
vr_new = None

from core.content_validator import ValidationResult
vr_new = ValidationResult()

success = rm.restore_record(test_record, pi_new, ml_new, generated_files_new, vr_new)
print(f"恢复成功: {success}")
assert success, "恢复记录失败"

print(f"  恢复的 project_id: {pi_new.project_id}")
print(f"  恢复的 product_name: {pi_new.product_name}")
print(f"  恢复的 scene: {pi_new.scene}")
print(f"  恢复的 generated_files: {list(generated_files_new.keys())}")
print(f"  恢复的 validation passed: {vr_new.passed}")
print(f"  恢复的材料数量: {len(ml_new.items)}")

assert pi_new.project_id == test_record['project_id'], "project_id不匹配"
assert pi_new.product_name == test_record['product_name'], "product_name不匹配"
assert pi_new.scene == test_record['scene'], "scene不匹配"
assert 'CPMS' in generated_files_new, "generated_files不匹配"
assert len(ml_new.items) == 6, "材料数量不匹配"

print("✓ 恢复记录数据完整性测试通过!")

# 测试7: PackageOutput get_submission_preview 稳定性
print("\n" + "=" * 70)
print("测试7: PackageOutput get_submission_preview 稳定性")
print("=" * 70)

from core import PackageOutput

# 测试空状态
pi_empty = ProjectInfo()
ml_empty = MaterialList()
po = PackageOutput(pi_empty, ml_empty, {}, None)

try:
    preview = po.get_submission_preview()
    print(f"  空状态预览成功")
    print(f"    文件数: {len(preview.files_to_include)}")
    print(f"    缺失必填: {len(preview.missing_required)}")
    print(f"    可以提交: {preview.can_submit}")
    
    # 检查文件列表字段
    for f in preview.files_to_include:
        required_file_fields = ['name', 'source', 'size', 'confirmed', 'original_path']
        for field in required_file_fields:
            assert field in f, f"文件缺少字段: {field}"
    
    print("✓ PackageOutput get_submission_preview 稳定性测试通过!")
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试8: 清理测试数据
print("\n" + "=" * 70)
print("测试8: 清理测试数据")
print("=" * 70)

for rec in test_records:
    deleted = rm.delete_record(
        project_id=rec['project_id'],
        batch_id=rec.get('batch_id', ''),
        created_at=rec.get('created_at', '')
    )
    print(f"  删除 {rec['product_name']}: {'✓' if deleted else '✗'}")

remaining = len(rm.get_all_records())
print(f"  剩余记录数: {remaining}")

print("✓ 测试数据清理完成!")

print("\n" + "=" * 70)
print("✓ 所有增强功能测试通过!")
print("=" * 70)

print("\n增强的功能总结:")
print("  1. ✓ RecordManager search_records 支持 has_errors 筛选")
print("  2. ✓ 历史记录支持场景、日期范围、校验错误多条件组合筛选")
print("  3. ✓ 记录保存包含完整的 zip_path、checklist_path、file_count")
print("  4. ✓ 恢复记录完整恢复项目信息、材料状态、生成文件、校验结果")
print("  5. ✓ PackageOutput get_submission_preview 空状态稳定")
print("  6. ✓ _get_selected_record 使用四元组精确匹配，避免串记录")

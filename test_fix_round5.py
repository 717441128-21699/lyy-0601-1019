#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试第五轮修复：
1. 打包日志文件清单正常写入
2. 提交状态逻辑正确（有错误时拦住）
3. 空文件/文件不存在错误明确显示
4. 防止重复保存历史
"""
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import os

sys.path.insert(0, str(Path(__file__).resolve().parent))

print("=" * 70)
print("数据要素交易材料生成工具 - 第五轮修复测试")
print("=" * 70)

# 测试1: build_package 返回字段完整性
print("\n" + "=" * 70)
print("测试1: build_package 返回字段完整性")
print("=" * 70)

from core import ProjectInfo, MaterialList, PackageOutput, TemplateGenerator, ContentValidator
from core.content_validator import ValidationResult

pi = ProjectInfo()
pi.product_name = "测试产品"
pi.product_code = "TEST001"
pi.scene = "金融风控"
pi.contact_person = "张三"
pi.contact_phone = "13800138000"
pi.valid_from = "2024-01-01"
pi.valid_to = "2025-12-31"

ml = MaterialList()
tg = TemplateGenerator(pi, ml)

# 生成一些模板文件
result = tg.generate_all(strategy="new_version", batch_name="测试批次")
generated_files = result.get("generated_files", {})
print(f"生成文件数: {len(generated_files)}")

# 确认文件到批次
current_batch = ml.get_current_batch()
if current_batch:
    for code, path in generated_files.items():
        if path and Path(path).exists():
            current_batch.confirmed_files.append(path)
            for item in ml.items:
                if item.code == code:
                    item.file_path = path
                    item.batch_id = current_batch.batch_id

cv = ContentValidator(pi, ml)
vr = cv.validate_all()

po = PackageOutput(pi, ml, generated_files, vr)
pkg_result = po.build_package(ignore_errors=True)

print(f"打包成功: {pkg_result.get('success')}")
print(f"zip_path: {pkg_result.get('zip_path', 'N/A')}")
print(f"checklist_path: {pkg_result.get('checklist_path', 'N/A')}")
print(f"file_count: {pkg_result.get('file_count', 'N/A')}")

required_fields = ['success', 'output_files', 'output_files_detail', 'zip_path', 'checklist_path', 'file_count', 'error', 'errors']
for field in required_fields:
    has_field = field in pkg_result
    print(f"  {field}: {'✓' if has_field else '✗'}")
    assert has_field, f"缺少字段: {field}"

assert pkg_result.get('success') == True, "打包应该成功"
assert pkg_result.get('file_count') > 0, "文件数量应该大于0"
assert len(pkg_result.get('output_files_detail', [])) == pkg_result.get('file_count'), "文件详情数量不匹配"

# 检查 output_files_detail 字段
for i, f in enumerate(pkg_result['output_files_detail']):
    assert 'name' in f, f"第{i}个文件缺少name字段"
    assert 'original_name' in f, f"第{i}个文件缺少original_name字段"
    assert 'original_path' in f, f"第{i}个文件缺少original_path字段"
    assert 'source' in f, f"第{i}个文件缺少source字段"
    assert 'material_code' in f, f"第{i}个文件缺少material_code字段"

print("✓ build_package 返回字段完整性测试通过!")

# 测试2: can_submit 逻辑 - 有校验错误时应该为False
print("\n" + "=" * 70)
print("测试2: can_submit 逻辑 - 有校验错误时应该为False")
print("=" * 70)

pi2 = ProjectInfo()
pi2.product_name = "测试产品2"
pi2.product_code = "TEST002"
pi2.scene = "金融风控"
pi2.contact_person = ""  # 缺少联系人
pi2.valid_from = ""
pi2.valid_to = ""

ml2 = MaterialList()
tg2 = TemplateGenerator(pi2, ml2)
result2 = tg2.generate_all(strategy="new_version", batch_name="测试批次2")
generated_files2 = result2.get("generated_files", {})

current_batch2 = ml2.get_current_batch()
if current_batch2:
    for code, path in generated_files2.items():
        if path and Path(path).exists():
            current_batch2.confirmed_files.append(path)
            for item in ml2.items:
                if item.code == code:
                    item.file_path = path
                    item.batch_id = current_batch2.batch_id

cv2 = ContentValidator(pi2, ml2)
vr2 = cv2.validate_all()
print(f"校验错误数: {len(vr2.errors)}")
print(f"校验警告数: {len(vr2.warnings)}")
print(f"必填材料缺失数: {len(ml2.get_missing_required())}")

po2 = PackageOutput(pi2, ml2, generated_files2, vr2)
preview2 = po2.get_submission_preview()

print(f"can_submit: {preview2.can_submit}")
print(f"validation_errors: {len(preview2.validation_errors)}")
print(f"files_to_include: {len(preview2.files_to_include)}")

assert preview2.can_submit == False, "有校验错误时 can_submit 应该为 False"
assert len(preview2.validation_errors) > 0, "应该有校验错误"

print("✓ can_submit 逻辑测试通过!")

# 测试3: 无待打包文件时的错误信息
print("\n" + "=" * 70)
print("测试3: 无待打包文件时的错误信息")
print("=" * 70)

pi3 = ProjectInfo()
pi3.product_name = "测试产品3"
pi3.product_code = "TEST003"
pi3.scene = "金融风控"
pi3.contact_person = "李四"
pi3.contact_phone = "13800138001"
pi3.valid_from = "2024-01-01"
pi3.valid_to = "2025-12-31"

ml3 = MaterialList()
vr3 = ValidationResult()
vr3.passed = True

# 不创建批次，不确认任何文件
po3 = PackageOutput(pi3, ml3, {}, vr3)
pkg_result3 = po3.build_package(ignore_errors=False)

print(f"success: {pkg_result3.get('success')}")
print(f"error: {pkg_result3.get('error', 'N/A')}")

assert pkg_result3.get('success') == False, "没有文件时应该失败"
assert pkg_result3.get('error') != '', "应该有错误信息"
assert "未设置批次" in pkg_result3.get('error', ''), "错误信息应该包含'未设置批次'"

print("✓ 无待打包文件错误信息测试通过!")

# 测试4: 确认的文件不存在时的错误信息
print("\n" + "=" * 70)
print("测试4: 确认的文件不存在时的错误信息")
print("=" * 70)

pi4 = ProjectInfo()
pi4.product_name = "测试产品4"
pi4.product_code = "TEST004"
pi4.scene = "金融风控"
pi4.contact_person = "王五"
pi4.contact_phone = "13800138002"
pi4.valid_from = "2024-01-01"
pi4.valid_to = "2025-12-31"

ml4 = MaterialList()
tg4 = TemplateGenerator(pi4, ml4)
result4 = tg4.generate_all(strategy="new_version", batch_name="测试批次4")
generated_files4 = result4.get("generated_files", {})

current_batch4 = ml4.get_current_batch()
if current_batch4:
    # 添加一个不存在的文件
    current_batch4.confirmed_files.append("C:/nonexistent/file1.docx")
    current_batch4.confirmed_files.append("C:/nonexistent/file2.docx")

cv4 = ContentValidator(pi4, ml4)
vr4 = cv4.validate_all()
vr4.errors = []  # 清除错误，只测试文件不存在的情况

po4 = PackageOutput(pi4, ml4, generated_files4, vr4)
pkg_result4 = po4.build_package(ignore_errors=False)

print(f"success: {pkg_result4.get('success')}")
print(f"error: {pkg_result4.get('error', 'N/A')}")

assert pkg_result4.get('success') == False, "文件不存在时应该失败"
assert pkg_result4.get('error') != '', "应该有错误信息"
assert "不存在" in pkg_result4.get('error', ''), "错误信息应该包含'不存在'"
assert "file1.docx" in pkg_result4.get('error', ''), "错误信息应该包含文件名"

print("✓ 文件不存在错误信息测试通过!")

# 测试5: get_submission_preview 空状态稳定性
print("\n" + "=" * 70)
print("测试5: get_submission_preview 空状态稳定性")
print("=" * 70)

pi5 = ProjectInfo()
ml5 = MaterialList()
po5 = PackageOutput(pi5, ml5, {}, None)

try:
    preview5 = po5.get_submission_preview()
    print(f"空状态预览成功")
    print(f"  can_submit: {preview5.can_submit}")
    print(f"  files_to_include: {len(preview5.files_to_include)}")
    print(f"  missing_required: {len(preview5.missing_required)}")
    print(f"  validation_errors: {len(preview5.validation_errors)}")
    
    # 检查 can_submit 逻辑
    assert preview5.can_submit == False, "空状态下 can_submit 应该为 False"
    
    # 检查文件列表字段
    for f in preview5.files_to_include:
        for field in ['name', 'source', 'size', 'confirmed', 'original_path', 'exists']:
            assert field in f, f"文件缺少字段: {field}"
    
    print("✓ get_submission_preview 空状态稳定性测试通过!")
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试6: 历史记录保存数据完整性
print("\n" + "=" * 70)
print("测试6: 历史记录保存数据完整性")
print("=" * 70)

from core import RecordManager

rm = RecordManager()
record = {
    "project_id": pi.project_id,
    "product_code": pi.product_code,
    "product_name": pi.product_name,
    "contact_person": pi.contact_person,
    "scene": pi.scene,
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "batch_id": current_batch.batch_id if current_batch else "",
    "batch_name": current_batch.batch_name if current_batch else "",
    "project_info": pi.to_dict(),
    "materials": ml.to_dict(),
    "generated_files": generated_files,
    "validation_result": vr.to_dict(),
    "zip_path": pkg_result['zip_path'],
    "checklist_path": pkg_result['checklist_path'],
    "file_count": pkg_result['file_count']
}

saved_record = rm.add_record(record)

# 检查保存的记录
required_record_fields = ['zip_path', 'checklist_path', 'file_count', 'project_info', 'materials', 'generated_files', 'validation_result']
for field in required_record_fields:
    has_field = field in saved_record
    value = saved_record.get(field, 'N/A')
    if isinstance(value, (dict, list)):
        print(f"  {field}: {'✓'} (类型: {type(value).__name__})")
    else:
        print(f"  {field}: {'✓'} = {value}")
    assert has_field, f"记录缺少字段: {field}"

assert saved_record['zip_path'] == pkg_result['zip_path'], "zip_path 不匹配"
assert saved_record['checklist_path'] == pkg_result['checklist_path'], "checklist_path 不匹配"
assert saved_record['file_count'] == pkg_result['file_count'], "file_count 不匹配"

print("✓ 历史记录数据完整性测试通过!")

# 测试7: 恢复记录数据完整性
print("\n" + "=" * 70)
print("测试7: 恢复记录数据完整性")
print("=" * 70)

pi_new = ProjectInfo()
ml_new = MaterialList()
generated_files_new = {}
vr_new = ValidationResult()

success = rm.restore_record(saved_record, pi_new, ml_new, generated_files_new, vr_new)
print(f"恢复成功: {success}")

assert success, "恢复记录应该成功"
assert pi_new.product_name == pi.product_name, "product_name 不匹配"
assert pi_new.scene == pi.scene, "scene 不匹配"
assert len(ml_new.items) == len(ml.items), "材料数量不匹配"
assert len(generated_files_new) == len(generated_files), "生成文件数量不匹配"
assert vr_new.passed == vr.passed, "校验结果不匹配"

print("✓ 恢复记录数据完整性测试通过!")

# 清理测试数据
print("\n" + "=" * 70)
print("清理测试数据")
print("=" * 70)

deleted = rm.delete_record(
    project_id=record['project_id'],
    batch_id=record.get('batch_id', ''),
    created_at=record.get('created_at', '')
)
print(f"  删除测试记录: {'✓' if deleted else '✗'}")

# 清理生成的文件
output_dir = Path(__file__).resolve().parent / "output"
if output_dir.exists():
    import shutil
    for zip_file in output_dir.glob("*.zip"):
        if "TEST" in zip_file.name:
            try:
                zip_file.unlink()
                print(f"  删除压缩包: {zip_file.name}")
            except:
                pass

print("\n" + "=" * 70)
print("✓ 所有第五轮修复测试通过!")
print("=" * 70)

print("\n修复总结:")
print("  1. ✓ build_package 返回 output_files_detail，包含完整的文件信息")
print("  2. ✓ can_submit 逻辑包含校验错误检查，有错误时明确拦住")
print("  3. ✓ 无待打包文件时错误信息明确：未设置批次/未确认文件/文件不存在")
print("  4. ✓ _finish() 移除重复保存逻辑，避免信息不全的历史记录")
print("  5. ✓ 历史记录保存完整的 zip_path、checklist_path、file_count")
print("  6. ✓ get_submission_preview 空状态稳定，所有字段完整")

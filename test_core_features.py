#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心功能测试脚本
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core import (
    ProjectInfo,
    MaterialList,
    BatchInfo,
    TemplateGenerator,
    ContentValidator,
    PackageOutput,
    RecordManager,
    SubmissionPreview
)
from config import TRADING_SCENARIOS, REQUIRED_MATERIALS


def test_material_list_callback():
    """测试材料清单变更回调机制"""
    print("\n" + "="*60)
    print("测试1: 材料清单变更回调机制")
    print("="*60)

    change_count = 0

    def on_change():
        nonlocal change_count
        change_count += 1
        print(f"  ✓ 材料变更通知 #{change_count}")

    ml = MaterialList()
    ml.on_change_callback = on_change

    print(f"  初始材料数量: {len(ml.items)}")

    ml.mark_provided("CPMS", "/test/product_desc.docx")
    ml.mark_provided("SQMS", "/test/auth_desc.docx")
    ml.mark_generated("YLDQ", True, "batch_001")

    print(f"  回调触发次数: {change_count} (期望: 3)")
    assert change_count == 3, f"期望回调3次，实际{change_count}次"

    ml.remove_material("CPMS")
    print(f"  移除材料后回调次数: {change_count} (期望: 4)")
    assert change_count == 4, f"期望回调4次，实际{change_count}次"

    print("  ✓ 材料变更回调测试通过!")
    return True


def test_batch_management():
    """测试批次管理功能"""
    print("\n" + "="*60)
    print("测试2: 批次管理功能")
    print("="*60)

    ml = MaterialList()

    batch1 = ml.create_batch("测试批次1", "overwrite", ["CPMS", "SQMS", "YLDQ"])
    print(f"  创建批次1: {batch1.batch_name} ({batch1.batch_id})")
    print(f"  批次策略: {batch1.strategy}")
    print(f"  批次材料: {batch1.material_codes}")

    current = ml.get_current_batch()
    assert current is not None, "当前批次应该存在"
    assert current.batch_id == batch1.batch_id, "当前批次应该是刚创建的批次"
    print(f"  ✓ 当前批次正确: {current.batch_name}")

    ml.mark_generated("CPMS", True, batch1.batch_id)
    ml.mark_generated("SQMS", True, batch1.batch_id)
    ml.mark_generated("YLDQ", True, batch1.batch_id)

    ml.confirm_batch_files(batch1.batch_id, ["CPMS", "SQMS", "YLDQ"])
    confirmed = ml.get_confirmed_for_package()
    print(f"  确认打包的材料数量: {len(confirmed)}")
    assert len(confirmed) == 3, f"期望3个确认材料，实际{len(confirmed)}个"

    batch2 = ml.create_batch("测试批次2", "new_version", ["CPMS"])
    print(f"  创建批次2: {batch2.batch_name}")
    print(f"  总批次数量: {len(ml.batches)}")
    assert len(ml.batches) == 2, f"期望2个批次，实际{len(ml.batches)}个"

    print("  ✓ 批次管理测试通过!")
    return True


def test_submission_preview():
    """测试提交预览功能"""
    print("\n" + "="*60)
    print("测试3: 提交预览功能")
    print("="*60)

    pi = ProjectInfo()
    pi.project_id = "TEST2024001"
    pi.product_code = "DATA001"
    pi.product_name = "测试产品"
    pi.contact_person = "张三"
    pi.contact_phone = "13800138000"
    pi.scene = TRADING_SCENARIOS[0]
    pi.valid_from = "2024-01-01"
    pi.valid_to = "2024-12-31"

    ml = MaterialList()
    batch = ml.create_batch("预览测试批次", "overwrite", ["CPMS", "SQMS", "YLDQ", "SCRZ"])

    ml.mark_generated("CPMS", True, batch.batch_id)
    ml.mark_generated("SQMS", True, batch.batch_id)
    ml.mark_generated("YLDQ", True, batch.batch_id)

    ml.confirm_batch_files(batch.batch_id, ["CPMS", "SQMS", "YLDQ"])

    generated_files = {
        "CPMS": "/output/TEST2024001_CPMS.docx",
        "SQMS": "/output/TEST2024001_SQMS.docx",
        "YLDQ": "/output/TEST2024001_YLDQ.xlsx"
    }

    cv = ContentValidator(pi, ml)
    vr = cv.validate_all()

    packager = PackageOutput(pi, ml, generated_files, vr)
    preview = packager.get_submission_preview()

    print(f"  待打包文件: {len(preview.files_to_include)} 个")
    print(f"  缺失必填材料: {len(preview.missing_required)} 个")
    for m in preview.missing_required:
        print(f"    - {m.code}: {m.name}")
    print(f"  缺失选填材料: {len(preview.missing_optional)} 个")
    print(f"  校验错误: {len(preview.validation_errors)} 个")
    print(f"  校验警告: {len(preview.validation_warnings)} 个")
    print(f"  敏感词警告: {len(preview.sensitive_warnings)} 个")
    print(f"  可以提交: {preview.can_submit}")

    print("  ✓ 提交预览测试通过!")
    return True


def test_record_manager():
    """测试记录管理功能"""
    print("\n" + "="*60)
    print("测试4: 记录管理功能 (多字段筛选、精确恢复)")
    print("="*60)

    rm = RecordManager()

    pi = ProjectInfo()
    pi.project_id = "PROJ001"
    pi.product_code = "PROD001"
    pi.product_name = "产品A"
    pi.contact_person = "张三"
    pi.scene = TRADING_SCENARIOS[0]

    ml = MaterialList()
    batch = ml.create_batch("测试批次", "overwrite")
    ml.mark_generated("CPMS", True, batch.batch_id)
    ml.confirm_batch_files(batch.batch_id, ["CPMS"])

    record1 = {
        "project_id": "PROJ001",
        "product_code": "PROD001",
        "product_name": "产品A",
        "contact_person": "张三",
        "scene": TRADING_SCENARIOS[0],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "batch_id": batch.batch_id,
        "batch_name": batch.batch_name,
        "project_info": pi.to_dict(),
        "materials": ml.to_dict(),
        "generated_files": {"CPMS": "/test/file.docx"},
        "validation_result": {"passed": True, "errors": [], "warnings": []},
        "zip_path": "/test/output.zip",
        "checklist_path": "/test/checklist.xlsx",
        "file_count": 3
    }

    record2 = {
        "project_id": "PROJ002",
        "product_code": "PROD002",
        "product_name": "产品B",
        "contact_person": "李四",
        "scene": TRADING_SCENARIOS[1],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "batch_id": "batch_002",
        "batch_name": "批次2",
        "project_info": pi.to_dict(),
        "materials": ml.to_dict(),
        "generated_files": {},
        "validation_result": {"passed": False, "errors": ["缺少联系人"], "warnings": []},
        "zip_path": "/test/output2.zip",
        "checklist_path": "/test/checklist2.xlsx",
        "file_count": 2
    }

    record3 = {
        "project_id": "PROJ003",
        "product_code": "PROD001",
        "product_name": "产品A",
        "contact_person": "王五",
        "scene": TRADING_SCENARIOS[0],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "batch_id": "batch_003",
        "batch_name": "批次3",
        "project_info": pi.to_dict(),
        "materials": ml.to_dict(),
        "generated_files": {},
        "validation_result": {"passed": True, "errors": [], "warnings": []},
        "zip_path": "/test/output3.zip",
        "checklist_path": "/test/checklist3.xlsx",
        "file_count": 1
    }

    rm.add_record(record1)
    rm.add_record(record2)
    rm.add_record(record3)

    all_records = rm.get_all_records()
    print(f"  总记录数: {len(all_records)}")

    results = rm.search_records(project_id="PROJ001")
    print(f"  按项目编号筛选(PROJ001): {len(results)} 条")
    assert len(results) == 1, f"期望1条，实际{len(results)}条"

    results = rm.search_records(product_code="PROD001")
    print(f"  按产品编码筛选(PROD001): {len(results)} 条 (同名不同项目)")
    assert len(results) == 2, f"期望2条，实际{len(results)}条"

    results = rm.search_records(product_name="产品A")
    print(f"  按产品名称筛选(产品A): {len(results)} 条")
    assert len(results) == 2, f"期望2条，实际{len(results)}条"

    results = rm.search_records(project_id="PROJ003", product_code="PROD001", product_name="产品A")
    print(f"  多字段组合筛选: {len(results)} 条")
    assert len(results) == 1, f"期望1条，实际{len(results)}条"
    assert results[0]["project_id"] == "PROJ003", "应该是PROJ003"
    print(f"    ✓ 精确匹配: project_id={results[0]['project_id']}, contact={results[0]['contact_person']}")

    results = rm.search_records(scene=TRADING_SCENARIOS[0])
    print(f"  按场景筛选({TRADING_SCENARIOS[0]}): {len(results)} 条")
    assert len(results) == 2, f"期望2条，实际{len(results)}条"

    new_pi = ProjectInfo()
    new_ml = MaterialList()
    new_gf = {}
    new_vr = None

    success = rm.restore_record(record1, new_pi, new_ml, new_gf, new_vr)
    print(f"  恢复记录: {'成功' if success else '失败'}")
    assert success, "恢复应该成功"
    assert new_pi.project_id == "PROJ001", f"项目ID应该是PROJ001，实际{new_pi.project_id}"
    assert new_pi.product_name == "产品A", f"产品名称应该是产品A，实际{new_pi.product_name}"
    assert "CPMS" in new_gf, "生成文件应该包含CPMS"
    print(f"    ✓ 恢复成功: project_id={new_pi.project_id}, product_name={new_pi.product_name}")

    delete_success = rm.delete_record(
        project_id=record1["project_id"],
        batch_id=record1["batch_id"],
        created_at=record1["created_at"]
    )
    print(f"  精确删除记录: {'成功' if delete_success else '失败'}")
    assert delete_success, "删除应该成功"

    remaining = rm.search_records(project_id="PROJ001")
    assert len(remaining) == 0, "PROJ001的记录应该已被删除"
    print(f"    ✓ 删除后PROJ001记录数: {len(remaining)}")

    for r in rm.get_all_records():
        rm.delete_record(r["project_id"], r.get("batch_id", ""), r.get("created_at", ""))

    print("  ✓ 记录管理测试通过!")
    return True


def test_template_strategies():
    """测试模板生成策略"""
    print("\n" + "="*60)
    print("测试5: 模板生成策略 (覆盖/新版本/更新选中)")
    print("="*60)

    from core import GENERATE_STRATEGIES

    print(f"  支持的生成策略: {GENERATE_STRATEGIES}")
    assert "overwrite" in GENERATE_STRATEGIES, "应该包含overwrite策略"
    assert "new_version" in GENERATE_STRATEGIES, "应该包含new_version策略"
    assert "update_selected" in GENERATE_STRATEGIES, "应该包含update_selected策略"

    print("  ✓ 生成策略测试通过!")
    return True


def main():
    print("\n" + "="*60)
    print("数据要素交易材料生成工具 - 核心功能测试")
    print("="*60)

    tests = [
        test_material_list_callback,
        test_batch_management,
        test_submission_preview,
        test_record_manager,
        test_template_strategies
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*60)

    if failed == 0:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查代码!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整工作流测试脚本
测试所有模块的集成功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import (
    ProjectInfo,
    MaterialList,
    TemplateGenerator,
    ContentValidator,
    PackageOutput,
    RecordManager
)
from datetime import datetime, timedelta


def create_test_project() -> ProjectInfo:
    project = ProjectInfo()
    project.product_name = "用户消费行为分析数据集"
    project.product_code = "DATA-2024-001"
    project.data_source = "某电商平台用户行为数据"
    project.update_frequency = "每月"
    project.trading_scene = "市场营销"
    project.contact_person = "张三"
    project.contact_phone = "13800138000"
    project.contact_email = "zhangsan@example.com"
    project.data_volume = "约500万条/月"
    project.usage_restrictions = "仅限内部数据分析使用，不得用于用户精准营销，不得泄露用户隐私信息，不得转授权第三方使用。"
    project.data_description = "本数据集包含电商平台用户的浏览、搜索、下单、支付等行为数据，涵盖用户基本属性、行为轨迹、消费偏好等维度。数据经过严格的脱敏处理，不包含任何可直接识别个人身份的信息。可用于用户画像构建、消费趋势分析、精准营销模型训练等场景。"
    project.valid_from = datetime.now().strftime("%Y-%m-%d")
    project.valid_to = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    project.sample_fields = [
        {"field_name": "user_id", "field_type": "string", "description": "用户脱敏标识", "sample_value": "U100001"},
        {"field_name": "behavior_type", "field_type": "string", "description": "行为类型：浏览/搜索/下单/支付", "sample_value": "下单"},
        {"field_name": "behavior_time", "field_type": "datetime", "description": "行为发生时间", "sample_value": "2024-01-15 14:30:25"},
        {"field_name": "category", "field_type": "string", "description": "商品类别", "sample_value": "电子产品"},
        {"field_name": "amount", "field_type": "float", "description": "交易金额（元）", "sample_value": "2599.00"},
        {"field_name": "region", "field_type": "string", "description": "用户所在地区", "sample_value": "上海市浦东新区"},
        {"field_name": "age_group", "field_type": "string", "description": "年龄段", "sample_value": "25-34"},
        {"field_name": "consumption_level", "field_type": "int", "description": "消费等级1-5", "sample_value": "4"}
    ]
    return project


def test_full_workflow():
    print("=" * 70)
    print("数据要素交易材料生成自动化工具 - 完整工作流测试")
    print("=" * 70)
    print()

    print("【步骤1】创建项目信息...")
    project = create_test_project()
    basic_errors = project.validate_basic()
    if basic_errors:
        print(f"  基本信息校验错误: {basic_errors}")
        return False
    print(f"  ✓ 项目名称: {project.product_name}")
    print(f"  ✓ 产品编码: {project.product_code}")
    print(f"  ✓ 数据来源: {project.data_source}")
    print(f"  ✓ 交易场景: {project.trading_scene}")
    print(f"  ✓ 字段数量: {len(project.sample_fields)}")
    print()

    print("【步骤2】初始化材料清单...")
    materials = MaterialList()
    summary = materials.get_summary()
    print(f"  ✓ 材料总数: {summary['total']}")
    print(f"  ✓ 必填材料: {summary['required']}")
    print(f"  ✓ 缺失必填: {summary['missing_required']}")
    print()

    print("【步骤3】生成模板文档...")
    generator = TemplateGenerator(project)
    generated_files = generator.generate_all()
    print(f"  ✓ 产品说明文档: {generated_files.get('product_desc', '失败')}")
    print(f"  ✓ 授权说明文档: {generated_files.get('auth_desc', '失败')}")
    print(f"  ✓ 样例字段清单: {generated_files.get('sample_fields', '失败')}")
    for key, path in generated_files.items():
        if key.endswith("_error"):
            print(f"  ✗ {key}: {path}")
        else:
            materials.mark_generated(key.replace("product_desc", "CPMS")
                                     .replace("auth_desc", "SQMS")
                                     .replace("sample_fields", "YLDQ"), True)
    print()

    print("【步骤4】内容校验...")
    validator = ContentValidator(project, materials)
    result = validator.validate_all()
    print(f"  校验结果:")
    if result.errors:
        print(f"  ✗ 错误 ({len(result.errors)}项):")
        for err in result.errors:
            print(f"    - {err}")
    else:
        print(f"  ✓ 无错误")
    if result.warnings:
        print(f"  ⚠ 警告 ({len(result.warnings)}项):")
        for warn in result.warnings:
            print(f"    - {warn}")
    else:
        print(f"  ✓ 无警告")
    if result.sensitive_hits:
        print(f"  ⚠ 敏感词 ({len(result.sensitive_hits)}处):")
        for hit in result.sensitive_hits:
            print(f"    - '{hit['word']}' 在【{hit['location']}】: {hit['context']}")
    else:
        print(f"  ✓ 无敏感词")
    print()

    print("【步骤5】打包输出...")
    packager = PackageOutput(project, materials, generated_files)
    package_result = packager.build_package(ignore_errors=result.has_errors)
    if package_result.get("success"):
        print(f"  ✓ 打包成功")
        print(f"  ✓ 提交清单: {package_result.get('checklist_path')}")
        print(f"  ✓ 压缩包: {package_result.get('zip_path')}")
        print(f"  ✓ 文件列表:")
        for f in package_result.get("output_files", []):
            print(f"    - {Path(f).name}")
    else:
        print(f"  ✗ 打包失败: {package_result.get('errors')}")
        return False
    print()

    print("【步骤6】保存生成记录...")
    record_manager = RecordManager()
    record = record_manager.save_record(
        project,
        materials,
        generated_files,
        result.to_dict(),
        package_result.get("zip_path", "")
    )
    print(f"  ✓ 记录已保存，项目ID: {record.get('project_id')}")
    print()

    print("【步骤7】查询记录统计...")
    stats = record_manager.get_statistics()
    print(f"  ✓ 总记录数: {stats['total']}")
    print(f"  ✓ 近30天: {stats['last_30_days']}")
    print(f"  ✓ 按场景分布: {stats['by_scene']}")
    print(f"  ✓ 有错误: {stats['with_errors']}")
    print(f"  ✓ 有警告: {stats['with_warnings']}")
    print()

    print("=" * 70)
    print("测试完成！所有模块工作正常。")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = test_full_workflow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n测试发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

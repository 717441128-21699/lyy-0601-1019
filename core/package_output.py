import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from docx import Document
from docx.shared import Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from core.project_info import ProjectInfo
from core.material_list import MaterialList, MaterialItem
from config import OUTPUT_DIR, PLATFORM_NAMING_RULE


class PackageOutput:
    def __init__(self, project_info: ProjectInfo, material_list: MaterialList,
                 generated_files: Dict):
        self.project = project_info
        self.materials = material_list
        self.generated_files = generated_files
        self.output_dir = OUTPUT_DIR / project_info.project_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_package(self, ignore_errors: bool = False) -> Dict:
        result = {
            "success": False,
            "output_files": [],
            "zip_path": "",
            "checklist_path": "",
            "errors": []
        }
        file_mapping = self._collect_all_files()
        if not file_mapping:
            result["errors"].append("没有可打包的文件")
            return result
        renamed_files = self._rename_files_by_platform_rule(file_mapping)
        checklist_path = self._generate_submission_checklist(renamed_files)
        result["checklist_path"] = checklist_path
        renamed_files.append(checklist_path)
        zip_path = self._create_zip_package(renamed_files)
        result["zip_path"] = zip_path
        result["output_files"] = renamed_files
        result["success"] = True
        return result

    def _collect_all_files(self) -> List[Dict]:
        collected = []
        for key, filepath in self.generated_files.items():
            if key.endswith("_error") or not filepath:
                continue
            mat_code = self._get_material_code_by_key(key)
            mat_item = self.materials.get_item(mat_code)
            collected.append({
                "original_path": filepath,
                "material_code": mat_code,
                "material_name": mat_item.name if mat_item else key,
                "is_generated": True
            })
        for item in self.materials.get_provided():
            if item.generated or not item.file_path:
                continue
            if Path(item.file_path).exists():
                collected.append({
                    "original_path": item.file_path,
                    "material_code": item.code,
                    "material_name": item.name,
                    "is_generated": False
                })
        return collected

    def _get_material_code_by_key(self, key: str) -> str:
        mapping = {
            "product_desc": "CPMS",
            "auth_desc": "SQMS",
            "sample_fields": "YLDQ"
        }
        return mapping.get(key, "QTLY")

    def _rename_files_by_platform_rule(self, files: List[Dict]) -> List[str]:
        renamed = []
        date_str = datetime.now().strftime("%Y%m%d")
        scene = self._safe_filename(self.project.trading_scene[:4] if self.project.trading_scene else "场景")
        code = self._safe_filename(self.project.product_code if self.project.product_code else self.project.project_id)
        for idx, file_info in enumerate(files):
            original_path = Path(file_info["original_path"])
            if not original_path.exists():
                continue
            mat_code = file_info["material_code"]
            new_filename = PLATFORM_NAMING_RULE.format(
                product_code=code,
                scene=scene,
                date=date_str,
                material_code=mat_code
            )
            new_filename = f"{new_filename}{original_path.suffix}"
            new_path = self.output_dir / new_filename
            counter = 1
            while new_path.exists():
                new_filename = PLATFORM_NAMING_RULE.format(
                    product_code=code,
                    scene=scene,
                    date=date_str,
                    material_code=f"{mat_code}_{counter}"
                )
                new_filename = f"{new_filename}{original_path.suffix}"
                new_path = self.output_dir / new_filename
                counter += 1
            shutil.copy2(original_path, new_path)
            file_info["platform_name"] = new_filename
            file_info["platform_path"] = str(new_path)
            renamed.append(str(new_path))
        return renamed

    def _generate_submission_checklist(self, files: List[str]) -> str:
        wb = Workbook()
        ws = wb.active
        ws.title = "提交清单"
        title = f"{self.project.product_name} - 上架材料提交清单"
        ws.cell(row=1, column=1, value=title).font = Font(size=14, bold=True)
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
        ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
        info_rows = [
            ["产品编码", self.project.product_code],
            ["交易场景", self.project.trading_scene],
            ["联系人", self.project.contact_person],
            ["联系电话", self.project.contact_phone],
            ["生成日期", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["项目编号", self.project.project_id]
        ]
        for row_idx, (key, value) in enumerate(info_rows, 3):
            ws.cell(row=row_idx, column=1, value=key).font = Font(bold=True)
            ws.cell(row=row_idx, column=2, value=value)
        start_row = len(info_rows) + 5
        headers = ["序号", "材料编码", "材料名称", "平台文件名", "来源", "状态"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        summary = self.materials.get_summary()
        provided = self.materials.get_provided()
        for idx, item in enumerate(provided, 1):
            row = start_row + idx
            is_generated = item.generated
            platform_name = ""
            for f in files:
                if item.code in Path(f).name:
                    platform_name = Path(f).name
                    break
            ws.cell(row=row, column=1, value=idx).alignment = Alignment(horizontal="center")
            ws.cell(row=row, column=2, value=item.code)
            ws.cell(row=row, column=3, value=item.name)
            ws.cell(row=row, column=4, value=platform_name)
            ws.cell(row=row, column=5, value="自动生成" if is_generated else "用户上传")
            status_cell = ws.cell(row=row, column=6, value="已准备")
            status_cell.font = Font(color="00B050")
            for col in range(1, 7):
                ws.cell(row=row, column=col).border = thin_border
        summary_start = start_row + len(provided) + 2
        ws.cell(row=summary_start, column=1, value="材料汇总").font = Font(bold=True, size=12)
        summary_data = [
            ["材料总数", summary["total"]],
            ["必填材料", summary["required"]],
            ["已提供", summary["provided"]],
            ["自动生成", summary["generated"]],
            ["缺失必填", summary["missing_required"]],
            ["缺失可选", summary["missing_optional"]],
            ["完整性", "完整" if summary["complete"] else "不完整"]
        ]
        for row_idx, (key, value) in enumerate(summary_data, summary_start + 1):
            ws.cell(row=row_idx, column=1, value=key).font = Font(bold=True)
            cell = ws.cell(row=row_idx, column=2, value=str(value))
            if key == "完整性" and not summary["complete"]:
                cell.font = Font(color="FF0000")
            elif key == "完整性" and summary["complete"]:
                cell.font = Font(color="00B050")
        for col in range(1, 7):
            ws.column_dimensions[chr(64 + col)].width = 25
        filename = f"{self._get_filename_prefix()}_TJQD_提交清单.xlsx"
        filepath = self.output_dir / filename
        wb.save(filepath)
        return str(filepath)

    def _create_zip_package(self, files: List[str]) -> str:
        zip_filename = f"{self._get_filename_prefix()}_上架材料包.zip"
        zip_path = self.output_dir / zip_filename
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filepath in files:
                path_obj = Path(filepath)
                if path_obj.exists():
                    zf.write(filepath, arcname=path_obj.name)
        return str(zip_path)

    def _get_filename_prefix(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        scene = self._safe_filename(self.project.trading_scene[:4] if self.project.trading_scene else "场景")
        code = self._safe_filename(self.project.product_code if self.project.product_code else self.project.project_id)
        return f"{code}_{scene}_{date_str}"

    @staticmethod
    def _safe_filename(filename: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for ch in invalid_chars:
            filename = filename.replace(ch, '_')
        return filename.strip() or "unnamed"

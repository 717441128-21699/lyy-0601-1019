import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from core.project_info import ProjectInfo
from core.material_list import MaterialList
from config import RECORDS_FILE


class RecordManager:
    def __init__(self):
        self.records_file = RECORDS_FILE
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        if not self.records_file.exists():
            self.records_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_records([])

    def _load_records(self) -> List[Dict]:
        try:
            with open(self.records_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_records(self, records: List[Dict]) -> None:
        with open(self.records_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    def save_record(self, project_info: ProjectInfo, material_list: MaterialList,
                    generated_files: Dict, validation_result: Dict,
                    output_package: str = "", batch_id: str = "") -> Dict:
        current_batch = material_list.get_current_batch()
        record = {
            "project_id": project_info.project_id,
            "created_at": project_info.created_at,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": project_info.product_name,
            "product_code": project_info.product_code,
            "scene": getattr(project_info, 'scene', getattr(project_info, 'trading_scene', '')),
            "trading_scene": getattr(project_info, 'trading_scene', getattr(project_info, 'scene', '')),
            "contact_person": project_info.contact_person,
            "batch_id": current_batch.batch_id if current_batch else batch_id,
            "batch_name": current_batch.batch_name if current_batch else "",
            "project_info": project_info.to_dict(),
            "materials": material_list.to_dict(),
            "material_summary": material_list.get_summary() if hasattr(material_list, 'get_summary') else {},
            "generated_files": generated_files,
            "validation_result": validation_result,
            "output_package": output_package
        }
        records = self._load_records()
        records.insert(0, record)
        self._save_records(records)
        return record

    def add_record(self, record: Dict) -> Dict:
        records = self._load_records()
        records.insert(0, record)
        self._save_records(records)
        return record

    def get_all_records(self) -> List[Dict]:
        return self._load_records()

    def get_record(self, project_id: str, batch_id: str = "") -> Optional[Dict]:
        records = self._load_records()
        for record in records:
            if record.get("project_id") == project_id:
                if not batch_id or record.get("batch_id") == batch_id:
                    return record
        return None

    def search_records(self, project_id: str = "", product_code: str = "",
                       product_name: str = "", contact_person: str = "",
                       start_date: str = "", end_date: str = "",
                       scene: str = "", batch_id: str = "") -> List[Dict]:
        records = self._load_records()
        results = []
        for record in records:
            match = True

            if project_id and record.get("project_id") != project_id:
                match = False
            if product_code and product_code.lower() not in record.get("product_code", "").lower():
                match = False
            if product_name and product_name.lower() not in record.get("product_name", "").lower():
                match = False
            if contact_person and contact_person.lower() not in record.get("contact_person", "").lower():
                match = False
            if batch_id and record.get("batch_id") != batch_id:
                match = False
            if scene:
                record_scene = record.get("scene") or record.get("trading_scene", "")
                if record_scene != scene:
                    match = False
            if start_date:
                record_date = record.get("created_at") or record.get("generated_at", "")
                if record_date < start_date:
                    match = False
            if end_date:
                record_date = record.get("created_at") or record.get("generated_at", "")
                if record_date > end_date + " 23:59:59":
                    match = False

            if match:
                results.append(record)
        return results

    def restore_record(self, record: Dict, project_info: ProjectInfo,
                       material_list: MaterialList,
                       generated_files: Dict = None,
                       validation_result: 'ValidationResult' = None) -> bool:
        try:
            if "project_info" in record:
                project_info.from_dict(record["project_info"])

            if "materials" in record:
                material_list.from_dict(record["materials"])

            if generated_files is not None:
                generated_files.clear()
                generated_files.update(record.get("generated_files", {}))

            if validation_result is not None and "validation_result" in record:
                vr = record["validation_result"]
                from core.content_validator import ValidationResult
                validation_result.__dict__.update(vr)

            return True
        except Exception as e:
            print(f"恢复记录失败: {e}")
            return False

    def get_record_detail(self, record: Dict) -> Dict:
        detail = {
            "basic": {
                "project_id": record.get("project_id"),
                "product_name": record.get("product_name"),
                "product_code": record.get("product_code"),
                "trading_scene": record.get("trading_scene"),
                "contact_person": record.get("contact_person"),
                "created_at": record.get("created_at"),
                "generated_at": record.get("generated_at"),
                "batch_id": record.get("batch_id"),
                "batch_name": record.get("batch_name"),
                "output_package": record.get("output_package")
            },
            "summary": record.get("material_summary", {}),
            "validation": record.get("validation_result", {}),
            "generated_files": record.get("generated_files", {}),
            "materials": record.get("materials", [])
        }
        return detail

    def delete_record(self, project_id: str, batch_id: str = "",
                      created_at: str = "") -> bool:
        records = self._load_records()
        original_len = len(records)

        def should_delete(r):
            if r.get("project_id") != project_id:
                return False
            if batch_id and r.get("batch_id") != batch_id:
                return False
            if created_at and r.get("created_at") != created_at:
                return False
            return True

        records = [r for r in records if not should_delete(r)]

        if len(records) < original_len:
            self._save_records(records)
            return True
        return False

    def get_record_versions(self, project_id: str) -> List[Dict]:
        records = self._load_records()
        return [r for r in records if r.get("project_id") == project_id]

    def get_statistics(self) -> Dict:
        records = self._load_records()
        total = len(records)
        if total == 0:
            return {
                "total": 0,
                "unique_products": 0,
                "by_scene": {},
                "last_30_days": 0,
                "with_errors": 0,
                "with_warnings": 0
            }
        unique_products = len(set(r.get("product_code") or r.get("project_id") for r in records))
        by_scene = {}
        last_30_days = 0
        with_errors = 0
        with_warnings = 0
        now = datetime.now()
        for record in records:
            scene = record.get("trading_scene", "未分类")
            by_scene[scene] = by_scene.get(scene, 0) + 1
            try:
                gen_date = datetime.strptime(record.get("generated_at", ""), "%Y-%m-%d %H:%M:%S")
                if (now - gen_date).days <= 30:
                    last_30_days += 1
            except ValueError:
                pass
            val_result = record.get("validation_result", {})
            if val_result.get("has_errors", False):
                with_errors += 1
            if val_result.get("has_warnings", False):
                with_warnings += 1
        return {
            "total": total,
            "unique_products": unique_products,
            "by_scene": by_scene,
            "last_30_days": last_30_days,
            "with_errors": with_errors,
            "with_warnings": with_warnings
        }

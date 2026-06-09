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
                    output_package: str = "") -> Dict:
        record = {
            "project_id": project_info.project_id,
            "created_at": project_info.created_at,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "product_name": project_info.product_name,
            "product_code": project_info.product_code,
            "trading_scene": project_info.trading_scene,
            "contact_person": project_info.contact_person,
            "project_info": project_info.to_dict(),
            "materials": material_list.to_dict(),
            "material_summary": material_list.get_summary(),
            "generated_files": generated_files,
            "validation_result": validation_result,
            "output_package": output_package
        }
        records = self._load_records()
        records.insert(0, record)
        self._save_records(records)
        return record

    def get_all_records(self) -> List[Dict]:
        return self._load_records()

    def get_record(self, project_id: str) -> Optional[Dict]:
        records = self._load_records()
        for record in records:
            if record.get("project_id") == project_id:
                return record
        return None

    def search_records(self, keyword: str = "", start_date: str = "",
                       end_date: str = "", scene: str = "") -> List[Dict]:
        records = self._load_records()
        results = []
        for record in records:
            match = True
            if keyword:
                keyword_lower = keyword.lower()
                text = " ".join([
                    record.get("product_name", ""),
                    record.get("product_code", ""),
                    record.get("contact_person", "")
                ]).lower()
                if keyword_lower not in text:
                    match = False
            if start_date and record.get("generated_at", "") < start_date:
                match = False
            if end_date and record.get("generated_at", "") > end_date + " 23:59:59":
                match = False
            if scene and record.get("trading_scene") != scene:
                match = False
            if match:
                results.append(record)
        return results

    def delete_record(self, project_id: str) -> bool:
        records = self._load_records()
        original_len = len(records)
        records = [r for r in records if r.get("project_id") != project_id]
        if len(records) < original_len:
            self._save_records(records)
            return True
        return False

    def get_statistics(self) -> Dict:
        records = self._load_records()
        total = len(records)
        if total == 0:
            return {
                "total": 0,
                "by_scene": {},
                "last_30_days": 0,
                "with_errors": 0,
                "with_warnings": 0
            }
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
            "by_scene": by_scene,
            "last_30_days": last_30_days,
            "with_errors": with_errors,
            "with_warnings": with_warnings
        }

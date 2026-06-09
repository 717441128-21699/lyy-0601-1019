from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from config import REQUIRED_MATERIALS


@dataclass
class BatchInfo:
    batch_id: str
    batch_name: str
    created_at: str
    strategy: str = "overwrite"
    confirmed_files: List[str] = field(default_factory=list)
    material_codes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "batch_name": self.batch_name,
            "created_at": self.created_at,
            "strategy": self.strategy,
            "confirmed_files": self.confirmed_files,
            "material_codes": self.material_codes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BatchInfo":
        return cls(
            batch_id=data.get("batch_id", ""),
            batch_name=data.get("batch_name", ""),
            created_at=data.get("created_at", ""),
            strategy=data.get("strategy", "overwrite"),
            confirmed_files=data.get("confirmed_files", []),
            material_codes=data.get("material_codes", [])
        )


@dataclass
class MaterialItem:
    code: str
    name: str
    required: bool = False
    provided: bool = False
    file_path: str = ""
    generated: bool = False
    batch_id: str = ""
    generated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "required": self.required,
            "provided": self.provided,
            "file_path": self.file_path,
            "generated": self.generated,
            "batch_id": self.batch_id,
            "generated_at": self.generated_at
        }


@dataclass
class MaterialList:
    items: List[MaterialItem] = field(default_factory=list)
    batches: List[BatchInfo] = field(default_factory=list)
    current_batch_id: Optional[str] = None
    on_change_callback = None

    def __post_init__(self):
        if not self.items:
            for mat in REQUIRED_MATERIALS:
                self.items.append(MaterialItem(
                    code=mat["code"],
                    name=mat["name"],
                    required=mat["required"]
                ))

    def _notify_change(self):
        if self.on_change_callback:
            self.on_change_callback()

    def get_item(self, code: str) -> MaterialItem:
        for item in self.items:
            if item.code == code:
                return item
        return None

    def mark_provided(self, code: str, file_path: str) -> None:
        item = self.get_item(code)
        if item:
            item.provided = True
            item.file_path = file_path
            self._notify_change()

    def mark_generated(self, code: str, generated: bool = True, batch_id: str = "") -> None:
        item = self.get_item(code)
        if item:
            item.generated = generated
            item.batch_id = batch_id
            item.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if generated:
                item.provided = True
            self._notify_change()

    def remove_material(self, code: str) -> bool:
        item = self.get_item(code)
        if item and not item.generated:
            item.provided = False
            item.file_path = ""
            item.batch_id = ""
            item.generated_at = ""
            self._notify_change()
            return True
        return False

    def create_batch(self, name: str = "", strategy: str = "overwrite",
                     material_codes: List[str] = None) -> BatchInfo:
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not name:
            name = f"批次_{batch_id}"
        batch = BatchInfo(
            batch_id=batch_id,
            batch_name=name,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            strategy=strategy,
            material_codes=material_codes or []
        )
        self.batches.append(batch)
        self.current_batch_id = batch_id
        self._notify_change()
        return batch

    def get_current_batch(self) -> Optional[BatchInfo]:
        if not self.current_batch_id:
            return None
        for batch in self.batches:
            if batch.batch_id == self.current_batch_id:
                return batch
        return None

    def get_batch(self, batch_id: str) -> Optional[BatchInfo]:
        for batch in self.batches:
            if batch.batch_id == batch_id:
                return batch
        return None

    def confirm_batch_files(self, batch_id: str, files: List[str]) -> None:
        batch = self.get_batch(batch_id)
        if batch:
            batch.confirmed_files = files
            self._notify_change()

    def set_current_batch(self, batch_id: str) -> None:
        if self.get_batch(batch_id):
            self.current_batch_id = batch_id
            self._notify_change()

    def get_batch_files(self, batch_id: str) -> List[MaterialItem]:
        return [item for item in self.items if item.batch_id == batch_id]

    def get_current_batch_files(self) -> List[MaterialItem]:
        if not self.current_batch_id:
            return []
        return self.get_batch_files(self.current_batch_id)

    def get_missing_required(self) -> List[MaterialItem]:
        return [item for item in self.items if item.required and not item.provided and not item.generated]

    def get_all_missing(self) -> List[MaterialItem]:
        return [item for item in self.items if not item.provided and not item.generated]

    def get_provided(self) -> List[MaterialItem]:
        return [item for item in self.items if item.provided or item.generated]

    def get_confirmed_for_package(self) -> List[MaterialItem]:
        current_batch = self.get_current_batch()
        if current_batch and current_batch.confirmed_files:
            confirmed_codes = set()
            for f in current_batch.confirmed_files:
                for item in self.items:
                    if item.file_path and item.file_path in f:
                        confirmed_codes.add(item.code)
                        break
                    elif item.code in f:
                        confirmed_codes.add(item.code)
                        break
            result = []
            for item in self.items:
                if item.code in confirmed_codes or (item.file_path and item.file_path in current_batch.confirmed_files):
                    result.append(item)
            return result
        return self.get_provided()

    def to_dict(self) -> dict:
        materials = [item.to_dict() for item in self.items]
        return {
            "items": materials,
            "materials": materials,
            "batches": [batch.to_dict() for batch in self.batches],
            "current_batch_id": self.current_batch_id
        }

    def from_dict(self, data: dict) -> None:
        items_data = data.get("items", data.get("materials", [])) if isinstance(data, dict) else data
        if isinstance(data, dict):
            self.items = []
            for item_data in items_data:
                self.items.append(MaterialItem(
                    code=item_data.get("code", ""),
                    name=item_data.get("name", ""),
                    required=item_data.get("required", False),
                    provided=item_data.get("provided", False),
                    file_path=item_data.get("file_path", ""),
                    generated=item_data.get("generated", False),
                    batch_id=item_data.get("batch_id", ""),
                    generated_at=item_data.get("generated_at", "")
                ))
            self.batches = [BatchInfo.from_dict(b) for b in data.get("batches", [])]
            self.current_batch_id = data.get("current_batch_id")
        else:
            self.items = []
            for item_data in items_data:
                self.items.append(MaterialItem(
                    code=item_data.get("code", ""),
                    name=item_data.get("name", ""),
                    required=item_data.get("required", False),
                    provided=item_data.get("provided", False),
                    file_path=item_data.get("file_path", ""),
                    generated=item_data.get("generated", False)
                ))
        self._notify_change()

    def get_summary(self) -> Dict:
        total = len(self.items)
        required = len([i for i in self.items if i.required])
        provided = len([i for i in self.items if i.provided or i.generated])
        required_provided = len([i for i in self.items if i.required and (i.provided or i.generated)])
        generated = len([i for i in self.items if i.generated])
        missing_required = required - required_provided
        missing_optional = total - provided - missing_required
        batch_count = len(self.batches)
        current_batch_files = len(self.get_current_batch_files())

        return {
            "total": total,
            "required": required,
            "provided": provided,
            "required_provided": required_provided,
            "generated": generated,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "complete": missing_required == 0,
            "batch_count": batch_count,
            "current_batch_files": current_batch_files
        }

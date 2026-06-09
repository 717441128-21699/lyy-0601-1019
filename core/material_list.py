from dataclasses import dataclass, field
from typing import List, Dict
from config import REQUIRED_MATERIALS


@dataclass
class MaterialItem:
    code: str
    name: str
    required: bool = False
    provided: bool = False
    file_path: str = ""
    generated: bool = False

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "required": self.required,
            "provided": self.provided,
            "file_path": self.file_path,
            "generated": self.generated
        }


@dataclass
class MaterialList:
    items: List[MaterialItem] = field(default_factory=list)

    def __post_init__(self):
        if not self.items:
            for mat in REQUIRED_MATERIALS:
                self.items.append(MaterialItem(
                    code=mat["code"],
                    name=mat["name"],
                    required=mat["required"]
                ))

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

    def mark_generated(self, code: str, generated: bool = True) -> None:
        item = self.get_item(code)
        if item:
            item.generated = generated
            if generated:
                item.provided = True

    def get_missing_required(self) -> List[MaterialItem]:
        return [item for item in self.items if item.required and not item.provided and not item.generated]

    def get_all_missing(self) -> List[MaterialItem]:
        return [item for item in self.items if not item.provided and not item.generated]

    def get_provided(self) -> List[MaterialItem]:
        return [item for item in self.items if item.provided or item.generated]

    def to_dict(self) -> List[dict]:
        return [item.to_dict() for item in self.items]

    def from_dict(self, data: List[dict]) -> None:
        self.items = []
        for item_data in data:
            self.items.append(MaterialItem(
                code=item_data.get("code", ""),
                name=item_data.get("name", ""),
                required=item_data.get("required", False),
                provided=item_data.get("provided", False),
                file_path=item_data.get("file_path", ""),
                generated=item_data.get("generated", False)
            ))

    def get_summary(self) -> Dict:
        total = len(self.items)
        required = len([i for i in self.items if i.required])
        provided = len([i for i in self.items if i.provided or i.generated])
        required_provided = len([i for i in self.items if i.required and (i.provided or i.generated)])
        generated = len([i for i in self.items if i.generated])
        missing_required = required - required_provided
        missing_optional = total - provided - missing_required

        return {
            "total": total,
            "required": required,
            "provided": provided,
            "required_provided": required_provided,
            "generated": generated,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "complete": missing_required == 0
        }

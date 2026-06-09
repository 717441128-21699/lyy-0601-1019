from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import uuid


@dataclass
class ProjectInfo:
    product_name: str = ""
    product_code: str = ""
    data_source: str = ""
    update_frequency: str = ""
    usage_restrictions: str = ""
    trading_scene: str = ""
    contact_person: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    valid_from: str = ""
    valid_to: str = ""
    data_volume: str = ""
    data_description: str = ""
    sample_fields: List[dict] = field(default_factory=list)
    attachments: List[dict] = field(default_factory=list)
    project_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "product_name": self.product_name,
            "product_code": self.product_code,
            "data_source": self.data_source,
            "update_frequency": self.update_frequency,
            "usage_restrictions": self.usage_restrictions,
            "trading_scene": self.trading_scene,
            "contact_person": self.contact_person,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "data_volume": self.data_volume,
            "data_description": self.data_description,
            "sample_fields": self.sample_fields,
            "attachments": self.attachments,
            "created_at": self.created_at
        }

    def from_dict(self, data: dict) -> None:
        self.project_id = data.get("project_id", self.project_id)
        self.product_name = data.get("product_name", "")
        self.product_code = data.get("product_code", "")
        self.data_source = data.get("data_source", "")
        self.update_frequency = data.get("update_frequency", "")
        self.usage_restrictions = data.get("usage_restrictions", "")
        self.trading_scene = data.get("trading_scene", "")
        self.contact_person = data.get("contact_person", "")
        self.contact_phone = data.get("contact_phone", "")
        self.contact_email = data.get("contact_email", "")
        self.valid_from = data.get("valid_from", "")
        self.valid_to = data.get("valid_to", "")
        self.data_volume = data.get("data_volume", "")
        self.data_description = data.get("data_description", "")
        self.sample_fields = data.get("sample_fields", [])
        self.attachments = data.get("attachments", [])
        self.created_at = data.get("created_at", self.created_at)

    def add_sample_field(self, field_name: str, field_type: str, description: str, sample_value: str = "") -> None:
        self.sample_fields.append({
            "field_name": field_name,
            "field_type": field_type,
            "description": description,
            "sample_value": sample_value
        })

    def add_attachment(self, file_path: str, material_code: str, material_name: str) -> None:
        self.attachments.append({
            "file_path": file_path,
            "material_code": material_code,
            "material_name": material_name
        })

    def validate_basic(self) -> List[str]:
        errors = []
        if not self.product_name:
            errors.append("数据产品名称不能为空")
        if not self.data_source:
            errors.append("数据来源不能为空")
        if not self.update_frequency:
            errors.append("更新频率不能为空")
        if not self.trading_scene:
            errors.append("交易场景不能为空")
        return errors

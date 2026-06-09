from pathlib import Path
from typing import List, Dict, Tuple
import re
from datetime import datetime
from core.project_info import ProjectInfo
from core.material_list import MaterialList
from config import SENSITIVE_WORDS_FILE


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.sensitive_hits: List[Dict] = []
        self.passed: bool = True
        self.timestamp: str = ""

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    @property
    def has_sensitive(self) -> bool:
        return len(self.sensitive_hits) > 0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.passed = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_sensitive(self, word: str, location: str, context: str = "", line: int = 0) -> None:
        self.sensitive_hits.append({
            "word": word,
            "location": location,
            "context": context,
            "line": line,
            "words": [word],
            "file": location
        })

    @property
    def sensitive_warnings(self) -> List[Dict]:
        return self.sensitive_hits

    def to_dict(self) -> Dict:
        return {
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "has_sensitive": self.has_sensitive,
            "errors": self.errors,
            "warnings": self.warnings,
            "sensitive_hits": self.sensitive_hits,
            "sensitive_warnings": self.sensitive_hits,
            "passed": self.passed,
            "timestamp": self.timestamp
        }


class ContentValidator:
    def __init__(self, project_info: ProjectInfo, material_list: MaterialList):
        self.project = project_info
        self.materials = material_list
        self.sensitive_words = self._load_sensitive_words()

    def validate_all(self) -> ValidationResult:
        result = ValidationResult()
        result.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._validate_contact_info(result)
        self._validate_validity_period(result)
        self._validate_materials(result)
        self._check_sensitive_content(result)
        self._validate_basic_info(result)
        return result

    def validate(self, project_info=None, material_list=None, generated_files=None) -> ValidationResult:
        if project_info:
            self.project = project_info
        if material_list:
            self.materials = material_list
        return self.validate_all()

    def _validate_basic_info(self, result: ValidationResult) -> None:
        errors = self.project.validate_basic()
        for err in errors:
            result.add_error(err)

    def _validate_contact_info(self, result: ValidationResult) -> None:
        if not self.project.contact_person:
            result.add_error("缺少联系人信息")
        if not self.project.contact_phone:
            result.add_error("缺少联系电话")
        else:
            phone_pattern = r'^1[3-9]\d{9}$'
            if not re.match(phone_pattern, self.project.contact_phone):
                result.add_warning("联系电话格式可能不正确，请检查")
        if not self.project.contact_email:
            result.add_warning("缺少电子邮箱")
        else:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.project.contact_email):
                result.add_warning("电子邮箱格式可能不正确，请检查")

    def _validate_validity_period(self, result: ValidationResult) -> None:
        if not self.project.valid_from:
            result.add_error("缺少授权有效期开始日期")
        if not self.project.valid_to:
            result.add_error("缺少授权有效期截止日期")
        if self.project.valid_from and self.project.valid_to:
            try:
                date_from = datetime.strptime(self.project.valid_from, "%Y-%m-%d")
                date_to = datetime.strptime(self.project.valid_to, "%Y-%m-%d")
                if date_to < date_from:
                    result.add_error("授权有效期截止日期不能早于开始日期")
                elif date_to < datetime.now():
                    result.add_warning("授权有效期已过期")
            except ValueError:
                result.add_warning("日期格式不正确，请使用YYYY-MM-DD格式")

    def _validate_materials(self, result: ValidationResult) -> None:
        missing = self.materials.get_missing_required()
        for item in missing:
            result.add_error(f"缺少必填材料：{item.name}（{item.code}）")
        missing_optional = self.materials.get_all_missing()
        for item in missing_optional:
            if not item.required:
                result.add_warning(f"缺少可选材料：{item.name}（{item.code}）")

    def _check_sensitive_content(self, result: ValidationResult) -> None:
        if not self.sensitive_words:
            return
        fields_to_check = [
            ("产品名称", self.project.product_name),
            ("数据来源", self.project.data_source),
            ("使用限制", self.project.usage_restrictions),
            ("数据描述", self.project.data_description),
            ("交易场景", self.project.trading_scene)
        ]
        for field_name, field_value in fields_to_check:
            if not field_value:
                continue
            for word in self.sensitive_words:
                if word.lower() in str(field_value).lower():
                    context = self._get_context(str(field_value), word)
                    result.add_sensitive(word, field_name, context)
                    result.add_warning(f"在【{field_name}】中检测到敏感描述：'{word}'")

    def _get_context(self, text: str, word: str, context_len: int = 20) -> str:
        idx = text.lower().find(word.lower())
        if idx == -1:
            return text
        start = max(0, idx - context_len)
        end = min(len(text), idx + len(word) + context_len)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{text[start:end]}{suffix}"

    def _load_sensitive_words(self) -> List[str]:
        if not SENSITIVE_WORDS_FILE.exists():
            self._create_default_sensitive_words()
        try:
            with open(SENSITIVE_WORDS_FILE, "r", encoding="utf-8") as f:
                words = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            return words
        except Exception:
            return []

    def _create_default_sensitive_words(self) -> None:
        default_words = [
            "# 敏感词库 - 可根据实际需要添加或修改",
            "# 每行一个词，#开头为注释",
            "绝密",
            "机密",
            "秘密",
            "个人隐私",
            "身份证号",
            "银行卡号",
            "密码",
            "核心数据",
            "内部资料",
            "不得公开",
            "仅限内部",
            "涉密",
            "敏感",
            "最高人民法院",
            "政府内部",
            "国家安全"
        ]
        SENSITIVE_WORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SENSITIVE_WORDS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(default_words))

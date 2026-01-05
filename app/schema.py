import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class SpecDraft:
    app_type: str = ""
    components: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    day2_actions: List[str] = field(default_factory=list)
    target_environment: str = ""

    def to_dict(self) -> dict:
        return {
            "app_type": self.app_type,
            "components": self.components,
            "dependencies": self.dependencies,
            "inputs": self.inputs,
            "day2_actions": self.day2_actions,
            "target_environment": self.target_environment,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Spec Draft",
            "",
            f"- App type: {self.app_type or 'TBD'}",
            f"- Components: {', '.join(self.components) or 'TBD'}",
            f"- Dependencies: {', '.join(self.dependencies) or 'TBD'}",
            f"- Inputs: {', '.join(self.inputs) or 'TBD'}",
            f"- Day-2 actions: {', '.join(self.day2_actions) or 'TBD'}",
            f"- Target environment: {self.target_environment or 'TBD'}",
        ]
        return "\n".join(lines)


def export_spec(spec: SpecDraft, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"spec_{timestamp}.json"
    md_path = output_dir / f"spec_{timestamp}.md"

    json_path.write_text(json.dumps(spec.to_dict(), indent=2), encoding="utf-8")
    md_path.write_text(spec.to_markdown(), encoding="utf-8")
    return json_path, md_path

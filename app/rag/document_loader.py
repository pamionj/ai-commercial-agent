from pathlib import Path


class DocumentLoader:

    def __init__(self, filepath: str):
        self.filepath = filepath

    def load(self):
        text = Path(self.filepath).read_text(encoding="utf-8")

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        return lines
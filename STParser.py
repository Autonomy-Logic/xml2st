import re

BASE_TYPES = [
    "BOOL",
    "SINT",
    "INT",
    "DINT",
    "LINT",
    "USINT",
    "UINT",
    "UDINT",
    "ULINT",
    "REAL",
    "LREAL",
    "TIME",
    "DATE",
    "TOD",
    "DT",
    "STRING",
    "BYTE",
    "WORD",
    "DWORD",
    "LWORD"
]


class _Block:
    def __init__(self, name):
        self.name = name.upper()
        self.start = re.compile(rf"^\s*{re.escape(self.name)}\s*$")
        self.end = re.compile(rf"^\s*END_{re.escape(self.name)}\s*$")

    def GetInfo(self, line):
        match = self.start.match(line)
        if match:
            return {
                "type": self.name,
            }
        return None


class _NamedBlock(_Block):
    def __init__(self, name):
        super().__init__(name)
        self.start = re.compile(
            rf"^\s*{re.escape(self.name)}\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*$"
        )

    def GetInfo(self, line):
        match = self.start.match(line)
        if match:
            return {
                "name": match.group("name"),
                "type": self.name,
            }
        return None


class _StructBlock(_NamedBlock):
    def __init__(self, name):
        super().__init__(name)
        self.start = re.compile(
            rf"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*{self.name}\s*$"
        )
        self.end = re.compile(rf"^\s*END_{re.escape(self.name)}\s*;\s*$")


class _DataType:
    def __init__(self, name):
        self.name = name.upper()
        self.definition = re.compile(
            r"^\s*"
            r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)"  # var_name
            r"\s*:\s*"
            r"(?P<type>[A-Za-z_][A-Za-z0-9_]*)"  # var_type
            r"(?:\s*:=\s*(?P<value>[^;]+))?"  # optional := value
            r"\s*;"
            r"\s*$"
        )

    def GetInfo(self, line):
        match = self.definition.match(line)
        if match:
            return {
                "name": match.group("name"),
                "type": self.name,
                "data_type": match.group("type"),
                "value": match.group("value"),
            }
        return None


class _ArrayType(_DataType):
    def __init__(self):
        super().__init__("array")
        self.definition = re.compile(
            rf"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*{self.name}\s*\["
            r"(?P<start>-?\d+)\s*\.\.\s*(?P<end>-?\d+)"
            r"\]\s*OF\s*"
            r"(?P<type>[A-Za-z_][A-Za-z0-9_]*)"
            r"(?:\s*:=\s*(?P<value>[^;]+))?"  # optional := value
            r"\s*;\s*$"
        )

    def GetInfo(self, line):
        match = self.definition.match(line)
        if match:
            return {
                "name": match.group("name"),
                "type": self.name,
                "data_type": match.group("type"),
                "start": int(match.group("start")),
                "end": int(match.group("end")),
            }
        return None


class _ProgramDefinition(_NamedBlock):
    def __init__(self):
        super().__init__("program_definition")
        self.definition = re.compile(
            r"^\s*PROGRAM\s+"
            r"(?P<instance>[a-zA-Z_][a-zA-Z0-9_]*)\s+WITH\s+"
            r"(?P<task>[a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*"
            r"(?P<program>[a-zA-Z_][a-zA-Z0-9_]*)\s*;"
        )

    def GetInfo(self, line):
        match = self.definition.match(line)
        if match:
            return {
                "instance": match.group("instance"),
                "task": match.group("task"),
                "program": match.group("program"),
                "type": self.name,
            }
        return None


TYPE = _Block("type")
FUNCTION_BLOCK = _NamedBlock("function_block")
PROGRAM = _NamedBlock("program")
CONFIGURATION = _NamedBlock("configuration")
RESOURCE = _NamedBlock("resource")
RESOURCE.start = re.compile(
    rf"^\s*{RESOURCE.name}\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+ON\s+PLC\s*$"
)
STRUCT = _StructBlock("struct")
VARIABLE = _DataType("variable")
ARRAY = _ArrayType()
PROGRAM_DEFINITION = _ProgramDefinition()

ALL_BLOCKS = [
    TYPE,
    FUNCTION_BLOCK,
    PROGRAM,
    CONFIGURATION,
    RESOURCE,
    STRUCT,
    ARRAY,
    VARIABLE,
]

CLOSABLE_BLOCKS = [
    TYPE,
    FUNCTION_BLOCK,
    PROGRAM,
    CONFIGURATION,
    RESOURCE,
    STRUCT,
]

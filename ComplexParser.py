import os, re
from jinja2 import Environment, FileSystemLoader
from util import paths
from STParser import (
    TYPE,
    FUNCTION_BLOCK,
    PROGRAM,
    CONFIGURATION,
    RESOURCE,
    STRUCT,
    ARRAY,
    VARIABLE,
    PROGRAM_DEFINITION,
    ALL_BLOCKS,
    CLOSABLE_BLOCKS,
    BASE_TYPES,
)

## GLOABL VARIABLES

EMPTY_LINE = re.compile(r"^\s*$")
FUNCTION_BLOCK_ST_TEMPLATE = "function_block.st.j2"

## CUSTOM CLASSES FOR BLOCK INSTANCES


class _InsertLine:
    def __init__(self, index):
        self.index = index


class _BlockInstance:

    def __init__(self, type):
        self.inner_blocks = []
        self.lines = []
        self.opened = True
        self.type = type

    def close(self, line):
        if self.inner_blocks and self.inner_blocks[-1].opened:
            self.inner_blocks[-1].close(line)
        else:
            self.opened = False
            self.AppendLine(line)

    def AddBlock(self, block):
        """
        Add a block to the inner blocks.
        """
        if self.inner_blocks == [] or not self.inner_blocks[-1].opened:
            self.inner_blocks.append(block)
            self.lines.append(_InsertLine(len(self.inner_blocks) - 1))
        else:
            self.inner_blocks[-1].AddBlock(block)

    def AppendLine(self, line):
        """
        Add a block to the inner blocks.
        """
        if self.inner_blocks == [] or not self.inner_blocks[-1].opened:
            self.lines.append(line)
        else:
            self.inner_blocks[-1].AppendLine(line)

    def __str__(self):
        line_break = "\n "
        return f"{self.type} : \n {line_break.join([str(b) for b in self.inner_blocks])} \nEND_{self.type};\n"


class _NamedBlockInstance(_BlockInstance):
    def __init__(self, type, name):
        super().__init__(type)
        self.name = name


class _VariableInstance(_NamedBlockInstance):
    def __init__(self, name, data_type, value=None):
        super().__init__(VARIABLE.name, name)
        self.data_type = data_type
        self.value = value
        self.opened = False
        self.simple = data_type in BASE_TYPES

    def VerifyCustomTypes(self, custom_types):
        """
        Verify if the data type is a custom type.
        """
        if not self.simple:
            self.simple = next(
                (t.simple for t in custom_types if t.name == self.data_type), False
            )

    def __str__(self):
        if self.value:
            return f"{self.data_type} {self.name} := {self.value};"
        else:
            return f"{self.data_type} {self.name};"


class _ArrayInstance(_VariableInstance):
    def __init__(self, name, start, end, data_type):
        super().__init__(name, data_type)
        self.type = ARRAY.name
        self.start = start
        self.end = end
        self.opened = False


class _StructInstance(_NamedBlockInstance):

    def __init__(self, name):
        self.simple = True
        super().__init__(STRUCT.name, name)

    def AddBlock(self, block):
        """
        Add a block to the inner blocks.
        """
        super().AddBlock(block)
        if self.simple and hasattr(block, "simple"):
            self.simple = block.simple


## MAIN COMPLEX PARSER CLASS


class ComplexParser:

    ## PRIVATE METHODS AND CONSTRUCTORS

    def __init__(self):
        self.blocks = []
        self.arrays = []
        self.structs = []
        self.programs = []
        self.simple_types = []
        self.simple_types_names = []
        self.complex_types = []
        self.complex_structs = []
        self.function_blocks = []
        self.__loader = FileSystemLoader(
            os.path.join(paths.AbsDir(__file__), "templates")
        )

    def __clear(self):
        """
        Clear the current state of the parser.
        """
        self.blocks = []
        self.arrays = []
        self.structs = []
        self.programs = []
        self.simple_types = []
        self.simple_types_names = []
        self.complex_types = []
        self.complex_structs = []
        self.function_blocks = []

    def __close(self, line):
        """
        Close the last opened block.
        """
        if self.blocks == []:
            raise Exception("No block opened to close.")
        self.blocks[-1].close(line)

    def __appendBlock(self, block):
        """
        Append a block to the blocks list.
        """
        if self.blocks == [] or not self.blocks[-1].opened:
            self.blocks.append(block)
        else:
            self.blocks[-1].AddBlock(block)

    def __appendLine(self, line):
        """
        Append a line to the current block's lines.
        """
        if self.blocks == []:
            if EMPTY_LINE.match(line):
                pass
            else:
                raise Exception("No block opened to append line.")
        else:
            self.blocks[-1].AppendLine(line)

    def __classifyBlock(self, info):
        """
        Classify the block based on its type.
        """
        if info["type"] == ARRAY.name:
            instance = _ArrayInstance(
                info["name"], info["start"], info["end"], info["data_type"]
            )
            self.arrays.append(instance)
            return instance
        elif info["type"] == STRUCT.name:
            instance = _StructInstance(info["name"])
            self.structs.append(instance)
            return instance
        elif info["type"] == VARIABLE.name:
            instance = _VariableInstance(
                info["name"], info["data_type"], info.get("value")
            )
            return instance
        elif "name" in info.keys():
            return _NamedBlockInstance(info["type"], info["name"])
        else:
            return _BlockInstance(info["type"])

    def __getBlockLines(self, block, ignoreComplexStructs=True):
        """
        Get the lines of the block.
        """

        lines = []
        if ignoreComplexStructs and isinstance(block, _StructInstance):
            return []
        for line in block.lines:
            if isinstance(line, _InsertLine):
                lines.extend(self.__getBlockLines(block.inner_blocks[line.index]))
            else:
                lines.append(line)

        return lines

    def __analyseTypes(self, block):
        """
        Separate custom defined types into simple and complex types.
        All structs are now marked as complex and will be transformed to function blocks.
        """
        simple_blocks = [
            b for b in block.inner_blocks if not isinstance(b, _StructInstance)
        ]
        self.simple_types.extend(simple_blocks)
        self.simple_types_names = [s.name for s in self.simple_types]

        struct_blocks = [
            b for b in block.inner_blocks if isinstance(b, _StructInstance)
        ]
        self.complex_types.extend([b.name for b in struct_blocks])
        self.complex_structs.extend(struct_blocks)

    def __separateOuterBlocks(self):
        """
        Get the custom types from the blocks.
        """
        self.custom_types = []
        for block in self.blocks:
            if block.type == TYPE.name:
                self.__analyseTypes(block)
            elif block.type == FUNCTION_BLOCK.name:
                self.function_blocks.append(block)
            elif block.type == PROGRAM.name:
                self.programs.append(block)

    def _parseStTree(self):
        """
        Parse the ST file to extract complex variables.
        """

        with open(self.__stFile, "r") as f:
            lines = f.readlines()

        for line in lines:
            info = next((t.GetInfo(line) for t in ALL_BLOCKS if t.GetInfo(line)), None)
            if info:
                block = self.__classifyBlock(info)
                self.__appendBlock(block)
            elif next((True for t in CLOSABLE_BLOCKS if t.end.match(line)), False):
                self.__close(line)
                continue
            self.__appendLine(line)

        self.__separateOuterBlocks()

    def __getSTLines(self):
        """
        Get the ST file content as a string.
        """
        lines = []
        for block in [b for b in self.blocks]:
            if block.type == TYPE.name:
                lines.extend(self.__getBlockLines(block))
                lines.append(self.__rewriteStructsAsFunctionBlocks())
            else:
                lines.extend(self.__getBlockLines(block))
        return lines

    def __rewriteStructsAsFunctionBlocks(self):
        template = Environment(loader=self.__loader).get_template(
            FUNCTION_BLOCK_ST_TEMPLATE
        )
        program_text = ""
        for struct in self.complex_structs:
            lines = [l.strip() for l in self.__getBlockLines(struct, False)[1:-1]]
            program_text += f"{template.render(name=struct.name, vars=lines)}\n\n"

        return program_text

    def __rewriteSTWithComplexStructs(self):
        """
        Rewrite the ST file with complex variables.
        """
        program_text = "".join(self.__getSTLines())
        with open(self.__stFile, "w") as f:
            f.write(program_text)

        return program_text

    ## PUBLIC METHODS

    def RewriteST(self, st_file):
        """
        Rewrite the ST file with complex variables.
        """
        if not st_file or not os.path.isfile(st_file):
            raise Exception("ST file not valid. Please provide a valid ST file path.")

        self.__clear()

        self.__stFile = st_file
        self._parseStTree()

        return self.__rewriteSTWithComplexStructs()

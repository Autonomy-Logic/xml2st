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
CSV_VARS_TEMPLATE = "variable_declaration.csv.j2"

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
        self.csv_vars = []
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
        self.csv_vars = []
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
        if (
            ignoreComplexStructs
            and isinstance(block, _StructInstance)
            and block.name in self.complex_types
        ):
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
        """
        changes = [b for b in block.inner_blocks if b.simple]
        self.simple_types.extend(changes)

        self.simple_types_names = [s.name for s in self.simple_types]

        complex_blocks = [b for b in block.inner_blocks if not b.simple]

        while changes:
            changes = False
            complex_blocks_copy = complex_blocks.copy()
            complex_blocks = []
            for complex_block in complex_blocks_copy:
                if isinstance(complex_block, _VariableInstance):
                    complex_block.simple = (
                        complex_block.data_type in self.simple_types_names
                    )
                    if complex_block.simple:
                        changes = True
                        self.simple_types.append(complex_block)
                        self.simple_types_names.append(complex_block.name)
                    else:
                        complex_blocks.append(complex_block)
                elif isinstance(complex_block, _StructInstance):
                    for inner_block in [
                        i for i in complex_block.inner_blocks if not i.simple
                    ]:
                        if inner_block.data_type not in self.simple_types_names:
                            complex_blocks.append(complex_block)
                            break
                    else:
                        complex_block.simple = True
                        self.simple_types.append(complex_block)
                        self.simple_types_names.append(complex_block.name)
                        changes = True

        self.complex_types.extend([b.name for b in complex_blocks])
        self.complex_structs.extend(
            [b for b in complex_blocks if isinstance(b, _StructInstance)]
        )

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
                for inner_block in block.inner_blocks:
                    if (
                        not isinstance(inner_block, _StructInstance)
                        or inner_block.name in self.simple_types_names
                    ):
                        break
                else:
                    if (
                        len(
                            list(
                                filter(
                                    lambda x: not isinstance(x, _InsertLine)
                                    and not EMPTY_LINE.match(x),
                                    block.lines,
                                )
                            )
                        )
                        > 2
                    ):
                        lines.extend(self.__getBlockLines(block))
                    lines.append(self.__rewriteStructsAsFunctionBlocks())
                    continue
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

    def __getCustomType(self, type_name):
        """
        Get the complex type by its name.
        """
        for custom_type in self.simple_types:
            if custom_type.name == type_name:
                return custom_type
        return None

    def __getFunctionBlock(self, name):
        """
        Get the function block by its name.
        """
        for block in self.function_blocks:
            if block.name == name:
                return block
        return None

    def __spreadDeclarations(
        self, block, prefix="", write_base_types=True, raw_type=False, value_added=False
    ):
        """
        Spread the declarations of the block.
        """
        if block.type == ARRAY.name:
            array_prefix = prefix
            if not raw_type:
                array_prefix = f"{array_prefix}.{block.name.upper()}"
            if not value_added:
                array_prefix = f"{array_prefix}.value"
            for i in range(0, block.end + 1 - block.start):
                indexed_prefix = f"{array_prefix}.table[{i}]"
                if block.data_type in BASE_TYPES:
                    self.csv_vars.append(
                        {"name": indexed_prefix, "type": block.data_type}
                    )
                else:
                    type = self.__getCustomType(block.data_type)
                    if type:
                        self.__spreadDeclarations(
                            type, prefix=indexed_prefix, value_added=True
                        )
        elif block.type == VARIABLE.name:
            prefix = f"{prefix}.{block.name.upper()}"
            if block.data_type in BASE_TYPES and write_base_types:
                self.csv_vars.append({"name": prefix, "type": block.data_type})
            elif block.data_type in self.simple_types_names:
                type = self.__getCustomType(block.data_type)
                if type:
                    self.__spreadDeclarations(
                        type, prefix=prefix, raw_type=True, value_added=value_added
                    )
            elif block.data_type in [b.name for b in self.function_blocks]:
                function_block = self.__getFunctionBlock(block.data_type)
                if function_block:
                    for inner_block in function_block.inner_blocks:
                        self.__spreadDeclarations(
                            inner_block,
                            prefix=prefix,
                            write_base_types=False,
                            value_added=value_added,
                        )
        elif block.type == STRUCT.name:
            if not value_added:
                prefix = f"{prefix}.value"
            for inner_block in block.inner_blocks:
                if isinstance(inner_block, _VariableInstance):
                    self.__spreadDeclarations(
                        inner_block, prefix=prefix, value_added=True
                    )

    def __addVarDeclarations(self, program, prefix=""):
        program_block = next((p for p in self.programs if p.name == program), None)
        if program_block:
            for block in program_block.inner_blocks:
                if isinstance(block, _VariableInstance):
                    self.__spreadDeclarations(block, prefix, write_base_types=False)

    def __findProgramInstances(self):
        """
        Find program instances in the ST file.
        """
        for block in self.blocks:
            if block.type == CONFIGURATION.name:
                for resource in filter(
                    lambda x: x.type == RESOURCE.name, block.inner_blocks
                ):
                    program_instances = [
                        PROGRAM_DEFINITION.GetInfo(line)
                        for line in resource.lines
                        if PROGRAM_DEFINITION.GetInfo(line)
                    ]
                    for program_instance in program_instances:
                        prefix = f"{block.name.upper()}.{resource.name.upper()}.{program_instance['instance'].upper()}"
                        self.__addVarDeclarations(program_instance["program"], prefix)

    def __appendVarsToCSV(self, csv_file):
        """
        Append new variable lines before the Ticktime section using regex matching.
        """

        content = []
        with open(csv_file, "r") as f:
            content = f.readlines()

        ticktime_idx = None
        var_number_pattern = re.compile(r"^\s*(\d+);")  # captures first number in line
        ticktime_pattern = re.compile(r"\s*//\s*Ticktime\s*$")

        # Find Ticktime section using regex
        for i, line in enumerate(content):
            if ticktime_pattern.match(line):
                ticktime_idx = i
                break

        if ticktime_idx is None:
            raise ValueError("Ticktime section not found in lines.")

        while ticktime_idx >= 1 and EMPTY_LINE.match(content[ticktime_idx - 1]):
            ticktime_idx -= 1

        last_var_number = -1

        if ticktime_idx > 0:
            extracted_var_number = var_number_pattern.match(
                content[ticktime_idx - 1]
            ).group(1)
            if extracted_var_number:
                last_var_number = int(extracted_var_number)

        template = Environment(loader=self.__loader).get_template(CSV_VARS_TEMPLATE)

        formatted_vars = []
        for var in self.csv_vars:
            last_var_number += 1
            formatted_vars.append(f"{template.render(i=last_var_number, var=var)}\n")

        with open(csv_file, "w") as f:
            f.writelines(
                content[:ticktime_idx] + formatted_vars + [""] + content[ticktime_idx:]
            )

        return content[:ticktime_idx] + formatted_vars + [""] + content[ticktime_idx:]

    def __rewriteCSVWithComplexVars(self, csv_file):

        self.__findProgramInstances()
        self.__appendVarsToCSV(csv_file)

    ## PUBLIC METHODS

    def AddComplexVars(self, st_file, csv_file):

        if not st_file or not os.path.isfile(st_file):
            raise Exception("ST file not valid. Please provide a valid ST file path.")

        if not csv_file or not os.path.isfile(csv_file):
            raise Exception("ST file not valid. Please provide a valid CSV file path.")

        self.__clear()

        self.__stFile = st_file
        self._parseStTree()

        self.__rewriteCSVWithComplexVars(csv_file)

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

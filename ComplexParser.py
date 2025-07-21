import os
from jinja2 import Environment, FileSystemLoader
from util import paths

STRUCT_TOKEN = "STRUCT"
TYPE_TOKEN = "TYPE"


class ComplexParser:

    def __init__(self):
        self.__loader = FileSystemLoader(
            os.path.join(paths.AbsDir(__file__), "templates")
        )

    def __rewriteSTFile(self, lines, complex_vars):
        """
        Rewrite the ST file with complex variables.
        """
        template = Environment(loader=self.__loader).get_template(
            "function_block.st.j2"
        )
        program_text = ""
        for var in complex_vars:
            program_text += f"{template.render(name=var[0], vars=var[1])}\n\n"
        program_text += "".join(lines)
        file_name = f"processed_{os.path.basename(self.__stFile)}"
        with open(os.path.join(paths.AbsDir(self.__stFile), file_name), "w") as f:
            f.write(program_text)

        return program_text

    def ParseSTFile(self, file):
        """
        Parse ST file to extract complex variables.
        """

        if not file:
            raise Exception("ST file not valid. Please ")

        self.__stFile = file

        lines = []

        with open(self.__stFile, "r") as f:
            lines = f.readlines()

        complex_vars = []
        new_lines = []
        parsing = False
        type_declaration = False

        for l in lines:
            line = l.strip()

            if line == TYPE_TOKEN:
                type_declaration = True
            if f": {STRUCT_TOKEN}" in line:
                if parsing:
                    raise Exception(
                        f"Error: Nested {STRUCT_TOKEN} declaration found in ST file."
                    )

                if not type_declaration:
                    raise Exception(
                        f"Error: {STRUCT_TOKEN} found out of {TYPE_TOKEN} block declaration."
                    )
                name = f"{line.split(':')[0].strip()}"
                complex_vars.append((name, {}))
                parsing = True
                continue
            elif f"END_{STRUCT_TOKEN}" in line:
                parsing = False
                continue
            elif parsing:
                splitted_line = line.replace(":=", ":").split(":")
                if len(splitted_line) == 3:
                    # Handle complex variable with type and initial value
                    name, type, value = (
                        splitted_line[0].strip(),
                        splitted_line[1].strip(),
                        splitted_line[2].replace(";", "").strip(),
                    )
                    complex_vars[-1][1][name] = {"type": type, "value": value}
                    continue
                name, type = (
                    splitted_line[0].strip(),
                    splitted_line[1].replace(";", "").strip(),
                )
                complex_vars[-1][1][name] = {"type": type, "value": None}
                continue
            # Remove type block if empty
            elif f"END_{TYPE_TOKEN}" in line:
                type_declaration = False
                if TYPE_TOKEN in new_lines[-1]:
                    new_lines.pop()
                    continue
            # Skip consecutive empty lines
            elif not l.strip() and not (new_lines and new_lines[-1].strip()):
                continue

            new_lines.append(l)

        return self.__rewriteSTFile(new_lines, complex_vars)

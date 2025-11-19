import os
import re
from jinja2 import Environment, FileSystemLoader
from util import paths

# LOCATED_VARIABLES.h example:
# __LOCATED_VAR(BOOL,__QX0_0,Q,X,0,0)
# __LOCATED_VAR(INT,__QW0,Q,W,0)
# __LOCATED_VAR(BOOL,__QX0_1,Q,X,0,1)


class GlueGenerator:

    def __init__(self):
        self.__loader = FileSystemLoader(
            os.path.join(paths.AbsDir(__file__), "templates")
        )

    def __glue_logic(self, varName):
        """
        Generate glue logic based on variable type.
        """

        # Extract indices
        print(f"Linking variable {varName}")
        try:
            parts = varName.split("_")
            pos1 = int(parts[2][2:])  # number after QX0 or QW0
            pos2 = int(parts[3]) if len(parts) > 3 else 0
        except Exception as e:
            raise Exception(f"Error parsing variable name '{varName}': {e}")

        kind = varName[2]  # I, Q, M
        sub = varName[3]  # X, B, W, D, L

        if kind == "I":
            if sub == "X":
                return f"bool_input_ptr[{pos1}][{pos2}] = (IEC_BOOL *){varName};"
            elif sub == "B":
                return f"byte_input_ptr[{pos1}] = (IEC_BYTE *){varName};"
            elif sub == "W":
                return f"int_input_ptr[{pos1}] = (IEC_UINT *){varName};"
            elif sub == "D":
                return f"dint_input_ptr[{pos1}] = (IEC_UDINT *){varName};"
            elif sub == "L":
                return f"lint_input_ptr[{pos1}] = (IEC_ULINT *){varName};"

        elif kind == "Q":
            if sub == "X":
                return f"bool_output_ptr[{pos1}][{pos2}] = (IEC_BOOL *){varName};"
            elif sub == "B":
                return f"byte_output_ptr[{pos1}] = (IEC_BYTE *){varName};"
            elif sub == "W":
                return f"int_output_ptr[{pos1}] = (IEC_UINT *){varName};"
            elif sub == "D":
                return f"dint_output_ptr[{pos1}] = (IEC_UDINT *){varName};"
            elif sub == "L":
                return f"lint_output_ptr[{pos1}] = (IEC_ULINT *){varName};"

        elif kind == "M":
            if sub == "W":
                return f"int_memory_ptr[{pos1}] = (IEC_UINT *){varName};"
            elif sub == "D":
                return f"dint_memory_ptr[{pos1}] = (IEC_UDINT *){varName};"
            elif sub == "L":
                return f"lint_memory_ptr[{pos1}] = (IEC_ULINT *){varName};"

        raise Exception(f"Unhandled variable type: {varName}")

    def __parse_line(self, line):
        """
        Parse a line from LOCATED_VARIABLES.h to extract variable information.
        Example: __LOCATED_VAR(BOOL,__QX0_0,Q,X,0,0)
        """
        m = re.match(r"__LOCATED_VAR\(([^,]+),([^,]+),.*\)", line.strip())
        if not m:
            print(f"Warning: Line '{line.strip()}' does not match expected format.")
            return None
        varType, varName = m.group(1), m.group(2)
        return {
            "type": varType,
            "name": varName,
            "glue_code": self.__glue_logic(varName),
        }

    def generate_glue_variables(self, located_vars_lines, template_file):
        """
        Generate glue variables from the LOCATED_VARIABLES content.
        """
        parsed = []
        for line in located_vars_lines:
            entry = self.__parse_line(line)
            if entry is not None:
                parsed.append(entry)

        if template_file:
            abs_template_file = os.path.abspath(template_file)
            env = Environment(loader=FileSystemLoader(os.path.dirname(abs_template_file)))
            template = env.get_template(os.path.basename(template_file))
        else:
            env = Environment(loader=self.__loader)
            template = env.get_template("glueVars.c.j2")
        return template.render(vars=parsed)

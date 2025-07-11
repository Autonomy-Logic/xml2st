import argparse
import os
import sys
import plcopen.plcopen as plcopen
import PLCGenerator
from PLCControler import PLCControler
from ProjectController import ProjectController

def compile_xml_to_st(xml_file_path):
    if not os.path.isfile(xml_file_path) or not xml_file_path.lower().endswith('.xml'):
        print(f"Error: Invalid file '{xml_file_path}'. A path to a xml file is expected.")
        return
    print(f"Compiling file {xml_file_path}")

    # Extract the file name
    file_name = os.path.abspath(xml_file_path)

    # Create a PLCControler instance and open the XML file
    # This will parse the XML and check for syntax errors
    controler = PLCControler()
    result = controler.OpenXMLFile(file_name)
    if result is not None:
        if isinstance(result, (tuple, list)) and len(result) == 2:
            (num, line) = result
            print(f"PLC syntax error at line {num}:\n{line}")
            return
        elif isinstance(result, str):
            print(result)
            return
        else:
            print("Unknown error! Exiting...")
            return

    project_tree = plcopen.LoadProject(file_name)

    if project_tree is None or len(project_tree) < 2:
        print(f"Error: Failed to load XML project file.")
        return

    project = project_tree[0]
    errors = []
    warnings = []
    try:
        ProgramChunks = PLCGenerator.GenerateCurrentProgram(controler, project, errors, warnings)
        program_text = "".join([item[0] for item in ProgramChunks])
        print("Stage 1 compilation finished successfully")
        return program_text

    except Exception as e:
        print(f"Error compiling project: {e}", file=sys.stderr)
        sys.exit(1)

def generate_debugger_file(csv_file):
    if not os.path.isfile(csv_file) or not csv_file.lower().endswith('.csv'):
        print(f"Error: Invalid file '{csv_file}'. A path to a csv file is expected.")
        return None, None

    controler = ProjectController()
    controler.SetCSVFile(csv_file)
    return controler.Generate_embedded_plc_debugger()[1]

def append_debugger_to_st(program_text, debug_text):
    # Wrap debugger code around (* comments *)
    c_debug_lines = debug_text.split('\n')
    c_debug = [f'(*DBG:{line}*)' for line in c_debug_lines]
    c_debug = '\n'.join(c_debug)

    # Concatenate debugger code with st program
    return f"{program_text}\n{c_debug}"

def main():
    parser = argparse.ArgumentParser(description='Process a PLCopen XML file and transpiles it into a Structured Text (ST) program.')
    parser.add_argument('--generate-st', type=str, help='The path to the XML file')
    parser.add_argument('--generate-debug', nargs=2, metavar=('XML_FILE', 'CSV_FILE'), type=str, help='Paths to the XML file and the variables CSV file')

    args = parser.parse_args()

    if args.generate_st:
        try:
            program_text = compile_xml_to_st(args.generate_st)

            if program_text is None:
                # This exception will always be caught
                raise Exception("Compilation failed, no program text generated.")

            print("Saving ST file...")


        except Exception as e:
            print(f"Error generating ST file: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.generate_debug and len(args.generate_debug) == 2:
        try:
            program_text = compile_xml_to_st(args.generate_debug[0])

            if program_text is None:
                # This exception will always be caught
                raise Exception("Compilation failed, no program text generated.")
            
            debug_text = generate_debugger_file(args.generate_debug[1])

            program_text = append_debugger_to_st(program_text, debug_text)

            print("Saving files...")

        except Exception as e:
            print(f"Error generating debug: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        print("Error: No valid arguments provided. Use --help for usage information.")
        return


    st_file = os.path.abspath(args.generate_st or args.generate_debug[0]).replace("plc.xml", "program.st")
    with open(st_file, "w") as file:
        file.write(program_text)

if __name__ == '__main__':
    main()

import argparse
import os
import sys
import plcopen.plcopen as plcopen
import PLCGenerator
from PLCControler import PLCControler
from ProjectController import ProjectController

def main():
    parser = argparse.ArgumentParser(description='Process a PLCopen XML file and transpiles it into a Structured Text (ST) program.')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable generate debug C variables from CSV file')
    parser.add_argument('file', type=str, help='The path to the XML file OR to the CSV file')

    args = parser.parse_args()

    if not os.path.isfile(args.file):
            print(f"Error: The file '{args.file}' does not exist.")
            return

    if not args.debug:
        if not args.file.lower().endswith('.xml'):
            print(f"Error: The file '{args.file}' is not an XML file.")
            return

        print(f"Compiling file {args.file}")

        # Extract and print the file name
        file_name = os.path.abspath(args.file)

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

        if project_tree == None or len(project_tree) < 2:
            print(f"Error: Failed to load XML project file.")
            return
        
        project = project_tree[0]
        errors = []
        warnings = []
        try:
            ProgramChunks = PLCGenerator.GenerateCurrentProgram(controler, project, errors, warnings)
            program_text = "".join([item[0] for item in ProgramChunks])

            # Construct a path to the ST program file, it is the same as the XML file, but with a .st extension
            program_file_path = file_name.replace("plc.xml", "program.st")
            with open (program_file_path, "w") as program_file:
                program_file.write(program_text)
            print("Stage 1 compilation finished successfully")
        except Exception as e:
            print(f"Error compiling project: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        if not args.file.lower().endswith('.csv'):
            print(f"Error: The file '{args.file}' is not an CSV file.")
            return
        
        # Generate the embedded PLC debugger file from the CSV file
        try:
            controler = ProjectController()
            controler.SetCSVFile(args.file)
            controler.Generate_embedded_plc_debugger()

        except Exception as e:
            print(f"Error generating debugger file: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()

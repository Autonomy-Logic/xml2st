import argparse
import os
import plcopen.plcopen as plcopen
import PLCGenerator
from PLCControler import PLCControler

def main():
    parser = argparse.ArgumentParser(description='Process a PLCopen XML file and transpiles it into a Structured Text (ST) program.')
    parser.add_argument('xml_file', type=str, help='The path to the XML file')

    args = parser.parse_args()

    if not os.path.isfile(args.xml_file):
        print(f"Error: The file '{args.xml_file}' does not exist.")
        return

    if not args.xml_file.lower().endswith('.xml'):
        print(f"Error: The file '{args.xml_file}' is not an XML file.")
        return
    
    print("Compiling file {a1}".format(a1=args.xml_file))

    # Extract and print the file name
    file_name = os.path.basename(args.xml_file)

    controler = PLCControler()
    result = controler.OpenXMLFile(file_name)
    if result is not None:
        if isinstance(result, (tuple, list)) and len(result) == 2:
            (num, line) = result
            print("PLC syntax error at line {a1}:\n{a2}".format(a1=num, a2=line))
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
    ProgramChunks = PLCGenerator.GenerateCurrentProgram(controler, project, errors, warnings)
    program_text = "".join([item[0] for item in ProgramChunks])
    with open ("program.st", "w") as program_file:
        program_file.write(program_text)
    print("Stage 1 compilation finished successfully")
        

if __name__ == '__main__':
    main()

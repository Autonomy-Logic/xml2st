# xml2st.py

import argparse
import os
import sys
# Make sure to import the necessary modules
from PLCControler import PLCControler
import PLCGenerator

def main():
    # 1. Updated Argument Parser to accept XML and CSV files
    parser = argparse.ArgumentParser(
        description='Process a PLCopen XML file and a debug CSV to generate Structured Text (ST) programs.')
    parser.add_argument('xml_file', type=str, help='The path to the PLCopen XML file')
    parser.add_argument('csv_file', type=str, help='The path to the debug variables CSV file')
    args = parser.parse_args()

    # --- File Validation ---
    if not os.path.isfile(args.xml_file):
        print(f"Error: The file '{args.xml_file}' does not exist.")
        return
    if not args.xml_file.lower().endswith('.xml'):
        print(f"Error: The file '{args.xml_file}' is not an XML file.")
        return
    if not os.path.isfile(args.csv_file):
        print(f"Error: The file '{args.csv_file}' does not exist.")
        return

    print(f"Processing file: {args.xml_file}")
    print(f"Using debug variables from: {args.csv_file}")
    
    file_name = os.path.abspath(args.xml_file)

    # --- Controller Initialization and Data Loading ---
    controler = PLCControler()
    
    # Load XML Project
    result = controler.OpenXMLFile(file_name)
    if result is not None and isinstance(result, str) and "error" in result.lower():
        print(result)
        return
    
    # 2. Load the new CSV data into the controller
    controler.LoadDebugCSV(args.csv_file)
    
    project = controler.GetProject()
    if project is None:
        print("Error: Failed to load project from XML.")
        return

    errors = []
    warnings = []

    # 4. --- Generate the DEBUG version of the program ---
    try:
        print("\nGenerating program with debug...")
        # Call GenerateCurrentProgram with debug=True
        debug_chunks = PLCGenerator.GenerateCurrentProgram(controler, project, errors, warnings, debug=True)
        debug_program_text = "".join([item[0] for item in debug_chunks])

        debug_file_path = file_name.replace(".xml", "_debug.st")
        with open(debug_file_path, "w", encoding='utf-8') as program_file:
            program_file.write(debug_program_text)
        print(f"Successfully generated debug program: {debug_file_path}")
        for warning in warnings:
            print(f"Warning: {warning}")

    except Exception as e:
        print(f"Error generating debug project: {e}", file=sys.stderr)
        for error in errors:
            print(f"Details: {error}", file=sys.stderr)

    # --- Generate the NORMAL (production) version of the program ---
    # Reset errors and warnings for the second run
    errors.clear()
    warnings.clear()
    
    try:
        print("\nGenerating production program...")
        # Call GenerateCurrentProgram with debug=False
        normal_chunks = PLCGenerator.GenerateCurrentProgram(controler, project, errors, warnings, debug=False)
        normal_program_text = "".join([item[0] for item in normal_chunks])

        normal_file_path = file_name.replace(".xml", ".st")
        with open(normal_file_path, "w", encoding='utf-8') as program_file:
            program_file.write(normal_program_text)
        print(f"Successfully generated production program: {normal_file_path}")
        for warning in warnings:
            print(f"Warning: {warning}")

    except Exception as e:
        print(f"Error generating production project: {e}", file=sys.stderr)
        for error in errors:
            print(f"Details: {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
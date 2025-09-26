import subprocess
import os
import glob
import xml.etree.ElementTree as ET
import time
import google.generativeai as genai

GEMINI_API_KEY = ""  # Replace with your Gemini API key

def run_maven_tests(project_path):
    mvn_cmd = r"C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.11\bin\mvn.cmd"
    process = subprocess.run(
        [mvn_cmd, "test"],
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    print(process.stdout)

def parse_surefire_reports(project_path):
    report_dir = os.path.join(project_path, "target", "surefire-reports")
    if not os.path.isdir(report_dir):
        print("No surefire-reports directory found. Did the tests run?")
        return [], []

    all_tests = []
    failing_tests = []

    for xml_file in glob.glob(os.path.join(report_dir, "TEST-*.xml")):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        class_name = root.attrib.get("name", "")
        for testcase in root.iter("testcase"):
            method = testcase.attrib.get("name", "")
            full_name = f"{class_name}.{method}"
            all_tests.append(full_name)
            if testcase.find("failure") is not None or testcase.find("error") is not None:
                failing_tests.append((class_name, method))

    print("\nTest cases run:")
    if all_tests:
        for test in sorted(all_tests):
            print(f"• {test}")
    else:
        print("No test cases detected.")

    print("\nFailing test cases:")
    if failing_tests:
        for class_name, method in failing_tests:
            print(f"❌ {class_name}.{method}")
    else:
        print("✅ No failing tests found")
    return failing_tests, all_tests

def find_java_file(class_name, src_dir):
    class_file = class_name.replace('.', os.sep) + ".java"
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file == class_file.split(os.sep)[-1]:
                return os.path.join(root, file)
    return None

def get_class_under_test(test_class_name, src_main_dir):
    if test_class_name.endswith("Test"):
        main_class = test_class_name[:-4]
    elif test_class_name.endswith("Tests"):
        main_class = test_class_name[:-5]
    else:
        main_class = test_class_name
    main_file = find_java_file(main_class, src_main_dir)
    return main_file

def read_file_content(file_path):
    if not file_path or not os.path.isfile(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def call_gemini_sdk(test_code, main_code, error_message):
    prompt = (
        "You are an expert Java developer. "
        "Given the following failing test case and its corresponding main class, "
        "fix the test case so that it passes, without removing the assertion or test logic. "
        "Explain your fix as comments in the code. "
        "Provide only the code content without any markdown formatting or language tags like  ```python. Just raw code. "
        "If you need to change the main class, do so only if necessary.\n\n"
        "Failing test case code:\n"
        "```\n" + test_code + "\n```\n\n"
        "Main class code:\n"
        "```\n" + main_code + "\n```\n\n"
        "Error message:\n"
        + error_message + "\n\n"
        "Return only the fixed test case code."
    )
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini SDK error: {e}")
        return None

def fix_failing_tests(project_path, failing_tests):
    src_test_dir = os.path.join(project_path, "src", "test", "java")
    src_main_dir = os.path.join(project_path, "src", "main", "java")
    report_dir = os.path.join(project_path, "target", "surefire-reports")

    for class_name, method in failing_tests:
        print(f"\n--- Attempting to fix: {class_name}.{method} ---")
        test_file = find_java_file(class_name, src_test_dir)
        if not test_file:
            print(f"Test file for {class_name} not found.")
            continue
        test_code = read_file_content(test_file)
        main_file = get_class_under_test(class_name.split('.')[-1], src_main_dir)
        main_code = read_file_content(main_file) if main_file else ""
        error_message = ""
        xml_report = os.path.join(report_dir, f"TEST-{class_name}.xml")
        if os.path.isfile(xml_report):
            tree = ET.parse(xml_report)
            root = tree.getroot()
            for testcase in root.iter("testcase"):
                if testcase.attrib.get("name", "") == method:
                    failure = testcase.find("failure")
                    error = testcase.find("error")
                    if failure is not None:
                        error_message = failure.text or ""
                    elif error is not None:
                        error_message = error.text or ""
        for attempt in range(3):
            print(f"Gemini attempt {attempt+1} for {class_name}.{method} ...")
            fixed_code = call_gemini_sdk(test_code, main_code, error_message)
            if fixed_code and "class" in fixed_code:
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(fixed_code)
                print(f"✅ Fixed and updated {test_file}")
                break
            else:
                print("Gemini did not return valid code, retrying...")
                time.sleep(2)
        else:
            print(f"❌ Failed to fix {class_name}.{method} after 3 attempts.")

"""
Run tests on submissions by python file submission for an assignment
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict

__author__ = "Duncan Mazza"


def acquire_and_rename_student_python_submissions(submissions_dir: str) -> \
        Dict[str, List[str]]:
    all_python_files = glob.glob(os.path.join(submissions_dir, "*.py"))
    student_files_dict: Dict[str, List[str]] = {}

    for python_file in all_python_files:
        # Canvas will append "-[digit]" to the filename sometimes; get rid of
        # this
        fixed_python_file = re.sub(r"-\d+(?=.py$)", "", python_file)
        if fixed_python_file != python_file:
            os.rename(python_file, fixed_python_file)
            python_file = fixed_python_file

        file_basename = os.path.basename(python_file)
        split_file_basename = file_basename.split("_")
        student_identifier: str = split_file_basename[0]

        is_test_file: bool
        if file_basename.__contains__("test"):
            is_test_file = True
        else:
            is_test_file = False

        renamed_file: str = os.path.join(submissions_dir,
                                         "_".join(split_file_basename[3:]))
        os.rename(python_file, renamed_file)

        if student_files_dict.get(student_identifier) is None:
            student_files_dict[student_identifier] = [""] * 2

        if is_test_file:
            student_files_dict[student_identifier][1] = str(renamed_file)
        else:
            student_files_dict[student_identifier][0] = str(renamed_file)

    return student_files_dict


def make_parser() -> argparse.ArgumentParser:
    """Makes an argument parser object for this program

    Returns:
        Argument parser
    """
    parser = argparse.ArgumentParser(description="Auto-grade an assignment")
    parser.add_argument(
        "submissions_dir",
        type=str,
        help="path to the submission directory to be graded",
    )
    parser.add_argument(
        "hw_dir_name",
        type=str,
        help="name of the homework folder you want graded (i.e., 'hw_1')",
    )
    return parser


def refactor_test_input(dest_module: str, file_lines: List[str],
                        orig_file_path: str):
    idx: int = 0
    for line in file_lines:
        if line.__contains__("from") and line.__contains__("import") and \
                line.__contains__("find_max_val_unimodal_arr"):
            file_lines[idx] = \
                "from {} import find_max_val_unimodal_arr\n".format(dest_module)
            break
        idx += 1

    with open(orig_file_path, 'w') as new_test_file:
        new_test_file.write("".join(file_lines))


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()

    if not os.path.isdir(args.submissions_dir):
        print(
            "Specified submissions folder {} is not a directory/does not "
            "exist".format(args.submissions_dir))
        exit()

    student_python_file_paths: Dict[str, List[str]] = \
        acquire_and_rename_student_python_submissions(args.submissions_dir)

    autograding_dir: str = os.path.dirname(os.path.realpath(__file__))
    test_results_dir: str = os.path.join(autograding_dir,
                                         "{}_test_results".format(
                                             args.hw_dir_name))

    if os.path.isdir(test_results_dir):
        print("There already exists a folder at {} that presumably "
              "already contains test results; deleting folder contents "
              "to replace with new".format(
            test_results_dir))
        shutil.rmtree(test_results_dir)

    os.mkdir(test_results_dir)

    # The python file containing the appropriate tests will need to be copied
    # into the students' directories. Get the contents of the file from the
    # teaching team repository for writing into a new file in the students'
    # repositories.
    local_hw_folder_path: str = os.path.join(Path(os.getcwd()).parent, "hw",
                                             args.hw_dir_name)
    matching_test_file_list = glob.glob(
        os.path.join(local_hw_folder_path, "test_hw*.py"))

    if len(matching_test_file_list) != 1:
        print("It appears that more than one or no file matches 'test_*.py' "
              "in {}. Make sure that there is only one file that matches to "
              "proceed."
              .format(local_hw_folder_path))
        exit()

    # Copy over the official tests to the submission folder and set up for
    # the test running
    official_test_text: str
    teacher_test_lines: List[str]
    with open(matching_test_file_list[0], 'r') as official_test_file:
        teacher_test_lines = official_test_file.readlines()
        official_test_text = "".join(teacher_test_lines)
    teacher_test_filepath = os.path.join(args.submissions_dir,
                                         "teacher_tests.py")
    teacher_test_lines: List[str]
    with open(teacher_test_filepath, 'w') as teacher_test_file:
        teacher_test_file.write(official_test_text)

    # Run tests
    for student in student_python_file_paths:
        full_student_test_path = os.path.join(args.submissions_dir, student_python_file_paths[
                                   student][1])
        student_test_lines: List[str]
        with open(full_student_test_path, 'r') as student_tests_file:
            student_test_lines = student_tests_file.readlines()

        refactor_test_input(os.path.basename(student_python_file_paths[student][
                                0])[:-3], student_test_lines,
                            full_student_test_path)
        try:
            student_test_results_text = subprocess.run(["python3", "-m", "pytest",
                                                        "-v",
                                                        "{}".format(
                student_python_file_paths[student][1])],
                cwd=args.submissions_dir,
                stdout=subprocess.PIPE,
                text=True,
                timeout=2
            )
            with open(os.path.join(test_results_dir,
                                   "{}_student_tests.txt".format(student)),
                      'w') as student_tests_file:
                student_tests_file.write(student_test_results_text.stdout)
            print("Student test output acquisition succeeded for {}".format(
                student))
        except:
            print("Student test output acquisition failed for {}".format(
                student))

        # Run teacher test
        refactor_test_input(os.path.basename(student_python_file_paths[student][
                                                 0])[:-3],
                            teacher_test_lines,
                            teacher_test_filepath)
        try:
            teacher_test_results_text = subprocess.run(["python3", "-m",
                "pytest", "-v", "{}".format(teacher_test_filepath)],
                cwd=args.submissions_dir,
                stdout=subprocess.PIPE,
                text=True,
                timeout=2
            )
            with open(os.path.join(test_results_dir,
                                   "{}_teacher_tests.txt".format(student)),
                      'w') as student_tests_file:
                student_tests_file.write(teacher_test_results_text.stdout)
            print("Teacher test output acquisition succeeded for {}".format(
                student))
        except:
            print("Teacher test output acquisition failed for {}".format(
                student))




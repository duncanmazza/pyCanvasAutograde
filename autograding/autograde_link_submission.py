"""
Run tests on submissions by github links for an assignment
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Union

from bs4 import BeautifulSoup

__author__ = "Duncan Mazza"


class GHLink:
    rx: str = r"(?<=^https:\/\/github.com\/)[\w\d./-]+$|(?<=^https:\/\/github" \
              r".com\/)[\w\d./-]+(?=\.git$)|(?<=http:\/\/github.com\/)[\w\d./" \
              r"-]+$|(?<=http:\/\/github.com\/)[\w\d./-]+(?=\.git$)|(?<=git@g" \
              r"ithub\.com:).+(?=\.git$)"
    ssh_link_prefix: str = "git@github.com:"
    ssh_link_suffix: str = ".git"
    https_link_prefix: str = "https://github.com/"

    err_regex_match_msg = "Regex did not find exactly 1 match"
    err_link_split_length_msg = "Link path when split at '/' must be =2 or >= 4"
    err_invalid_commit_hash_msg = "Specified commit, but commit hash was not " \
                                  "the required 40 characters long"
    err_third_pos_wrong = "Link path when split at '/' and of length 4 must " \
                          "contain 'tree', 'commit', or 'blob' in the 3rd " \
                          "position"

    def __init__(self, link):
        self._orig_link = str(link)
        self._is_valid: bool = False
        self._diagnosis: str = ""
        self._bare_link: str = ""
        self._ssh_link: str = ""
        self._https_link: str = ""
        self._branch: str = ""
        self._commit: str = ""
        self._username: str = ""
        self._repo_name: str = ""

        match_obj = re.findall(GHLink.rx, link.strip("/"))
        if not isinstance(match_obj, list):
            self._diagnosis = GHLink.err_regex_match_msg
            return

        if len(match_obj) != 1:
            self._diagnosis = GHLink.err_regex_match_msg
            return
        split_path = match_obj[0].split("/")
        if len(split_path) != 2 and len(split_path) < 4:
            self._diagnosis = GHLink.err_link_split_length_msg
            return
        if len(split_path) >= 4:
            if split_path[2] == "commit":
                if  len(split_path[3]) == 40:
                    self._commit = split_path[3]
                else:
                    self._diagnosis = GHLink.err_invalid_commit_hash_msg
                    return
            elif split_path[2] == "tree" or split_path[2] == "blob":
                self._branch = split_path[3]
            else:
                self._diagnosis = GHLink.err_third_pos_wrong
                return

        self._is_valid = True
        self._username = split_path[0]
        self._repo_name = split_path[1]
        self._bare_link = self._username + "/" + self._repo_name
        self._ssh_link = GHLink.ssh_link_prefix + self._bare_link \
                         + GHLink.ssh_link_suffix
        self._https_link = GHLink.https_link_prefix + self._bare_link

    def is_valid(self) -> bool:
        return bool(self._is_valid)

    def ssh_link(self) -> str:
        return str(self._ssh_link)

    def https_link(self) -> str:
        return str(self._https_link)

    def orig_link(self) -> str:
        return str(self._orig_link)

    def branch(self) -> str:
        return str(self._branch)

    def commit(self) -> str:
        return str(self._commit)

    def username(self) -> str:
        return str(self._username)

    def repo_name(self) -> str:
        return str(self._repo_name)

    def diagnosis(self) -> str:
        return str(self._diagnosis)

    def __eq__(self, other) -> bool:
        if not isinstance(other, GHLink):
            return False
        if self._orig_link == other._orig_link:
            return True

    def __hash__(self):
        return self._orig_link.__hash__()

    def __repr__(self):
        return self._orig_link


class Student:
    def __init__(self, gh_link: GHLink, student_repos_dir: str):
        self.gh_link = gh_link
        if not self.gh_link.is_valid():
            raise Exception("Assigned an invalid gh link")

        self._repo_folder_name: str = self.gh_link.username() + "_" + \
                                      self.gh_link.repo_name()
        self._repo_folder_path = os.path.join(student_repos_dir,
                                              self._repo_folder_name)
        self._repo_folder_exists: bool = False
        self._local_repo_existence_resolved: bool = False
        self._tested_without_failure: bool = False
        self._pushed_successfully: bool = True
        self._detached_head: bool = False

    def __repr__(self):
        return self.gh_link.username()

    def _resolve_local_repo_existence(self, delete_if_exists: bool = False):
        self._local_repo_existence_resolved = False

        self._repo_folder_exists = os.path.isdir(self._repo_folder_path)
        delete_if_exists &= self._repo_folder_exists

        if delete_if_exists:
            print("Deleting repository at folder path: {}".format(
                self._repo_folder_path))
            shutil.rmtree(self._repo_folder_path)
            self._repo_folder_exists = False

        if not self._repo_folder_exists:
            print("Cloning repo for {}".format(self.gh_link.username()))
            try:
                subprocess.run(["git", "clone", self.gh_link.ssh_link(),
                                self._repo_folder_path], check=True)
            except subprocess.CalledProcessError:
                raise Exception("Could not successfully clone the repo {}"
                                .format(self._repo_folder_name))

        self._local_repo_existence_resolved = True

    def _run_cmd_for_student(
            self,
            command: List[str],
            cwd: Union[str, None] = None,
            check: bool = True
    ) -> str:
        subprocess_cwd_arg: str
        if cwd is None:
            subprocess_cwd_arg = self._repo_folder_path
        else:
            subprocess_cwd_arg = os.path.join(self._repo_folder_path, cwd)
        output = subprocess.run(
            command,
            cwd=subprocess_cwd_arg,
            check=check,
            stdout=subprocess.PIPE,
            text=True,
            timeout=20,
        )
        return output.stdout

    def _update_to_gh_link_specified(self):
        try:
            self._run_cmd_for_student(["git", "reset", "--hard"])
            self._run_cmd_for_student(["git", "pull", "--ff-only"])
        except subprocess.CalledProcessError:
            print("An error occurred when running when hard-resetting and "
                  "pulling from the repo {}, so the repo will attempt to be "
                  "deleted and re-cloned".format(self.gh_link.https_link()))
            self._resolve_local_repo_existence(True)
        finally:
            self._run_cmd_for_student(["git", "fetch", "--all"])

        if len(self.gh_link.commit()) == 0 and len(self.gh_link.branch()) == 0:
            self._run_cmd_for_student(["git", "checkout", "main"])
        elif len(self.gh_link.commit()) == 0 and \
                len(self.gh_link.branch()) > 0:
            self._run_cmd_for_student(
                ["git", "checkout", self.gh_link.branch()])
        else:
            self._run_cmd_for_student(
                ["git", "checkout", self.gh_link.commit()])
            self._detached_head = True

    def _run_tests_for_file(self, test_file_name: str,
                            hw_folder_abs_path: str,
                            output_file_name: str) -> None:
        test_results = self._run_cmd_for_student(
            ["python3", "-m", "pytest", "-v", "--timeout=5",
             test_file_name], hw_folder_abs_path, False
        )
        with open(os.path.join(hw_folder_abs_path, output_file_name),
                  'w') as test_results_file:
            test_results_file.write(test_results)

    def _push_results(self, hw_folder_abs_path: str):
        self._run_cmd_for_student(["git", "add", os.path.join(
            hw_folder_abs_path, ".")])
        self._run_cmd_for_student(
            ["git", "commit", "-m", "Add testing results for {}".format(
                hw_folder_abs_path.split(os.path.sep)[-1])]
        )

        if self._detached_head:
            # Create temporary branch with the commits, switch out of
            # detached-head state into  the branch associated with the commit
            # hash, merge in the the temporary branch, and then delete the
            # temporary branch.
            commit_and_branch = self._run_cmd_for_student(
                ["git", "name-rev", self.gh_link.commit()])
            match_obj = re.findall(r"(?<=[\d\w]{40}\s)[\w\d/-]+",
                                   commit_and_branch)
            branch_of_commit: str
            if isinstance(match_obj, list):
                if len(match_obj) == 1:
                    branch_of_commit = (match_obj[0].split("/"))[-1]
                else:
                    raise Exception("Could not find the branch associated "
                                    "with the specified commit")
            else:
                raise Exception("Could not find the branch associated with "
                                "the specified commit")
            tmp_branch: str = "tmp_for_{}".format(self.gh_link.commit())
            self._run_cmd_for_student(["git", "branch", tmp_branch])
            self._run_cmd_for_student(["git", "checkout", branch_of_commit])
            self._detached_head = False
            self._run_cmd_for_student(
                ["git", "merge", "-s", "recursive", "-X", "theirs", tmp_branch]
            )
            self._run_cmd_for_student(["git", "branch", "-D", tmp_branch])

        self._run_cmd_for_student(["git", "push", "--force"])

    def test(self, hw_folder: str, teacher_tests_text: str,
             student_test_file_name: Union[str, None], push_results: bool =
             False) -> str:
        self._tested_without_failure = False
        self._pushed_successfully = False

        if not self._local_repo_existence_resolved:
            self._resolve_local_repo_existence()
        self._update_to_gh_link_specified()

        hw_folder_subdir = os.path.join("hw", hw_folder)
        hw_folder_abs_path = os.path.join(
            self._repo_folder_path,
            hw_folder_subdir
        )

        # Import errors may occur if there is no __init__.py in the homework
        # directory, so add one just to be safe
        hw_init_py_path = os.path.join(hw_folder_abs_path, "__init__.py")
        if not os.path.isfile(hw_init_py_path):
            with open(hw_init_py_path, 'w') as hw_init_py_file:
                hw_init_py_file.write("")

        teacher_tests_path: str = os.path.join(hw_folder_abs_path,
                                               "teacher_tests.py")

        with open(teacher_tests_path, 'w') as teacher_tests_file:
            teacher_tests_file.write(teacher_tests_text)

        full_report: str = "Testing for " + self.__repr__() + ": "
        self._tested_without_failure = True
        if student_test_file_name is not None:
            try:
                self._run_tests_for_file(
                    student_test_file_name,
                    hw_folder_abs_path,
                    "student_test_results.txt"
                )
                print("Completed student tests successfully for {}".format(
                    self.__repr__())
                )
            except Exception as ex:
                failed_diagnosis1: str = "Could not complete student tests " \
                                         "for {} due to error: {}".format(
                    self.gh_link.username(),
                    ex)
                print(failed_diagnosis1)
                full_report += failed_diagnosis1 + " | "
                self._tested_without_failure = False

        try:
            self._run_tests_for_file(
                "teacher_tests.py",
                hw_folder_abs_path,
                "teacher_test_results.txt"
            )
            print("Completed teacher tests successfully for {}".format(
                self.__repr__())
            )
        except Exception as ex:
            failed_diagnosis2: str = "Could not complete teacher tests for {}" \
                " due to error: {}".format(self.gh_link.username(), ex)
            print(failed_diagnosis2)
            full_report += failed_diagnosis2 + (" | " if push_results else "")
            self._tested_without_failure = False

        os.remove(teacher_tests_path)

        if self._tested_without_failure:
            full_report += "SUCCESS (tests gave exit code 0)"

        if push_results:
            try:
                self._push_results(hw_folder_abs_path)
                self._pushed_successfully = True
                full_report += " | Pushed successfully"
            except Exception as ex:
                full_report += " | Did NOT push successfully due to " \
                               "error: {}".format(ex)

        return full_report

    def do_push_only(self, hw_folder: str) -> str:
        self._pushed_successfully = False

        if not self._local_repo_existence_resolved:
            self._resolve_local_repo_existence()
        self._update_to_gh_link_specified()

        hw_folder_subdir = os.path.join("hw", hw_folder)
        hw_folder_abs_path = os.path.join(
            self._repo_folder_path,
            hw_folder_subdir
        )

        full_report: str = "For " + self.__repr__() + ": "
        try:
            self._push_results(hw_folder_abs_path)
            self._pushed_successfully = True
            full_report += "Pushed successfully"
        except Exception as ex:
            full_report += "Not pushed successfully due to " \
                           "error: {}".format(ex)
        return full_report

    def tested_without_failure(self) -> bool:
        return self._tested_without_failure

    def pushed_successfully(self) -> bool:
        return self._pushed_successfully


def make_parser() -> argparse.ArgumentParser:
    """Makes an argument parser object for this program

    Returns:
        Argument parser
    """
    parser = argparse.ArgumentParser(description="Unit test an assignment")
    parser.add_argument(
        "submissions_dir",
        type=str,
        help="path to the submission directory to be graded",
    )
    parser.add_argument(
        "hw_dir_name",
        type=str,
        help="name of the homework folder you want graded (e.g., 'hw_2')",
    )
    parser.add_argument(
        "teacher_test_file",
        type=str,
        help="file in the specified homework directory that contains the "
             "teacher-written tests (e.g., 'test_hw2.py'). It is expected "
             "that the teacher-written tests import the solution from a file "
             "that is named the same as the file the student has submitted "
             "except with the suffix '_solution'. For example, if the "
             "student's code is in hw2.py, then the solution should be "
             "imported from 'hw2_solution.py'."
    )
    parser.add_argument(
        "-s",
        type=str,
        help="file in the specified homework directory of the student's fork "
             "that contains the student-written tests (e.g., 'test_hw2.py')"
    )
    parser.add_argument(
        "-P",
        action="store_true",
        help="push results to student repos (without this flag, "
             "no results are committed or pushed)"
    )
    return parser


def acquire_gh_links(submission_dir: str) -> Tuple[GHLink]:
    """Acquires the github links from a folder of canvas link submissions
    formatted as html files.

    Args:
        submission_dir: Absolute path to the submissions folder that contains
         the html files that represent the students' link submissions

    Returns:
        Tuple of student-submitted github links
    """
    matched_files = glob.glob(os.path.join(submission_dir, "*.html"))
    gh_links: List[GHLink] = []

    for i, submission in enumerate(matched_files):
        with open(submission, 'r') as submission_file:
            submission_text = submission_file.read()
            soup = BeautifulSoup(submission_text, "html.parser")
            hw_link_before_process: str = soup.body.a["href"]
            gh_link = GHLink(hw_link_before_process)
            gh_links.append(gh_link)

    gh_links.sort(key=lambda x: x.__repr__())
    return tuple(gh_links)


if __name__ == "__main__":
    parser = make_parser()
    args = parser.parse_args()

    if not os.path.isdir(args.submissions_dir):
        print(
            "Specified submissions folder {} is not a directory/does not "
            "exist".format(args.submissions_dir)
        )
        exit()

    autograding_dir: str = os.path.dirname(os.path.realpath(__file__))
    student_repos_dir: str = os.path.join(autograding_dir, "student_repos")

    # The python file containing the appropriate tests will need to be copied
    # into the students' directories. Get the contents of the file from the
    # teaching team repository for writing into a new file in the students'
    # repositories.
    local_hw_folder_path: str = os.path.join(Path(os.getcwd()).parent, "hw",
                                             args.hw_dir_name)
    matching_test_file_list = glob.glob(
        os.path.join(local_hw_folder_path, args.teacher_test_file))

    if len(matching_test_file_list) != 1:
        print(
            "It appears that more than one or no file matches '{}' in {}. Make "
            "sure that there is only one file that matches to proceed.".format(
                args.teacher_test_file, local_hw_folder_path
            )
        )
        exit()

    teacher_tests_lines: List[str]

    with open(matching_test_file_list[0], 'r') as teacher_test_file:
        teacher_tests_lines = teacher_test_file.readlines()

    # Search for the import statement that imports the solution file in the
    # teacher test suite and change it such that it imports the students'
    # code. This is achieved by deleting the '_solution' suffix from the
    # imported file/package (assumes solution file is the same as the
    # student's submission except with a '_solution' suffix).
    refactored_teacher_tests: bool = False
    for i in range(len(teacher_tests_lines)):
        if re.findall(
                r"((?<=from\s)([\s\w\d.]*_solution)(?=\simport[\s\w*]))|((?<=im"
                r"port\s)([\s\w\d.]*_solution))", teacher_tests_lines[i]):
            teacher_tests_lines[i] = re.sub(r"_solution(?=\s)", "",
                                            teacher_tests_lines[i])
            refactored_teacher_tests = True
            break

    if not refactored_teacher_tests:
        print("Failed to update the import statement in teacher tests file")
        exit(1)

    teacher_tests_text: str = "".join(teacher_tests_lines)

    if not os.path.isdir(student_repos_dir):
        os.mkdir(student_repos_dir)

    gh_links = acquire_gh_links(args.submissions_dir)

    students: List[Student] = []
    failed_for: List[str] = []
    for gh_link in gh_links:
        try:
            students.append(Student(gh_link, student_repos_dir))
        except Exception as ex:
            print("Could not proceed with repository cloning or testing for "
                  "link: {}".format(gh_link.__repr__()))
            failed_for.append(gh_link.__repr__() + " (reason: {})".format(
                gh_link.diagnosis()))

    report: List[str] = []
    for student in students:
        report.append(student.test(args.hw_dir_name, teacher_tests_text,
                                   args.s, args.P))
        print("")

    print("\n--------\nSummary:")
    if len(report) > 0:
        print("\n".join(report))
    if len(failed_for) > 0:
        print("\nCould not proceed with repository cloning for any of the "
              "following submitted links:\n{}".format("\n".join(failed_for)))

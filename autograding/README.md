# Autograding

Scripts to run unit tests on student Canvas submissions.

> Note: While the code was written to be operating system-independent, it has only been validated on Ubuntu and errors have been encountered when run on Windows.
 
> Note: Double-check that the unit tests ran correctly **BEFORE** pushing the unit test results to student repositories. 

## Link submission testing

```text
usage: autograde_link_submission.py [-h] [-s S] [-P] submissions_dir hw_dir_name 
       teacher_test_file

Unit test an assignment

positional arguments:
  submissions_dir    path to the submission directory to be graded
  hw_dir_name        name of the homework folder you want graded (e.g., 'hw_2')
  teacher_test_file  file in the specified homework directory that contains the 
                     teacher-written tests (e.g., 'test_hw2.py'). It is 
                     expected that the teacher-written tests import the solution
                     from a file that is named the same as the file the 
                     student has submitted except with the suffix '_solution'. 
                     For example, if the student's code is in hw2.py, then the 
                     solution should be imported from 'hw2_solution.py'.

optional arguments:
  -h, --help         show this help message and exit
  -s S               file in the specified homework directory of the student's 
                     fork that contains the student-written tests (e.g., 
                     'test_hw2.py')
  -P                 push results to student repos (without this flag, no 
                     results are committed or pushed)
```

Both the student-written tests and the teacher-written tests will be run and output to `.txt` files in the `dsa/autograding/student_repos/<student_repo>/hw/<hw_dir_name>` path. If the `-P` option is specified, then those test results will be pushed to the students repositoryies.

Valid link examples:

| Link | Test behavior | Push behavior (`-P` flag given) |
| ---- | ------------- | ----------------------------- |
| `https://github.com/duncanmazza/dsa-2021-01` | Will grade whatever is in `hw/<hw_dir_name>` directory of the latest commit in the `main` branch | Will push to the `main` branch
| `https://github.com/duncanmazza/dsa-2021-01/tree/test_branch` | Will grade whatever is in `hw/<hw_dir_name>` directory of the latest commit in the `test_branch` branch | Will push to the `test_branch`
| `https://github.com/duncanmazza/dsa-2021-01/commit/60596b55ad9b1ee1bc0ca2fce3ee43e1db7e4136` or `https://github.com/duncanmazza/dsa-2021-01/tree/60596b55ad9b1ee1bc0ca2fce3ee43e1db7e4136` | Will grade whatever is in `hw/<hw_dir_name>` directory of the commit specified by the commit hash `60596b55ad9b1ee1bc0ca2fce3ee43e1db7e4136`) | Will push to the branch associated with the commit (specifically, the branch named by the command `git name-rev <commit hash>`) |

### Example

```shell
python3 autograde_link_submissions.py "/home/duncan/Downloads/submissions" hw_2 -s test_hw2.py test_hw2.py
```
The above command will inspect each of the github links in the submission files in `"/home/duncan/Downloads/submissions"` and, for any repositories not locally cloned into `dsa/autograding/student_repos`, clone them. Then, for each student, it will:

- Run the student's tests by calling `python3 -m pytest <local_student_repo>/hw/hw_2/test_hw2.py` and save the results into `student_test_results.txt`.
- Run the teacher's tests by first copying `dsa/hw/hw_2/test_hw2.py` into the student's repository (named as `teacher_tests.py`) and then calling `python3 -m pytest <local_student_repo>/hw/hw_2/teacher_tests.py`; the results are saved into `teacher_test_results.txt`.

To push the results to the students' repositories, simply add the `-P` flag to the above command.

Notes:

- The `submissions_dir` path should point to the unzipped folder of submissions from Canvas. With link submissions, all of the submissions should be `.html` files (this is what the script will look for).

## File submission testing

Documentation TBD

# pyCanvasAutograde

Scripts to run Pytest unit tests on student Canvas submissions that are either GitHub links or raw Python files.

## Overview 

These scripts were developed for use in the student-run Data Structures and Algorithms Course I (Duncan) co-taught as a student teacher at Olin College of Engineering in 2021. Students were typically to submit their solutions to Python coding assignments as GitHub links to their repositories, which were forks of a student-facing repository. Downloading submissions for an assignment gives a folder full of files (`.html` files in the case of link submissions) that can be used as the target for these auto-grading script so long as specific file naming conventions are followed. 

> Note: While the code was written to be operating system-independent, it has only been validated on Ubuntu and errors have been encountered when run on Windows.
 
> Note: Double-check that the unit tests ran correctly **BEFORE** pushing the unit test results to student repositories. 

See [autograding/README.md](autograding/README.md) for usage instructions.

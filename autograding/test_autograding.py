import pytest
from .autograde_link_submission import GHLink
from typing import Tuple, Union, Dict

# Dictionary keys must match the GHLink attribute names
links = [
    # Test invalid link (invalid domain)
    ("https:/github.com/dm/repo_name", {
        "_is_valid": False,
        "_diagnosis": GHLink.err_regex_match_msg,
        "_bare_link": "",
        "_ssh_link": "",
        "_https_link": "",
        "_branch": "",
        "_commit": "",
        "_username": "",
        "_repo_name": "",
    }),

    # Test invalid link (no repository name)
    ("https:/github.com/dm", {
        "_is_valid": False,
        "_diagnosis": GHLink.err_regex_match_msg,
        "_bare_link": "",
        "_ssh_link": "",
        "_https_link": "",
        "_branch": "",
        "_commit": "",
        "_username": "",
        "_repo_name": "",
    }),

    # Nominal case (with trailing slash)
    ("https://github.com/dm/repo_name/", {
        "_is_valid": True,
        "_diagnosis": "",
        "_bare_link": "dm/repo_name",
        "_ssh_link": "git@github.com:dm/repo_name.git",
        "_https_link": "https://github.com/dm/repo_name",
        "_branch": "",
        "_commit": "",
        "_username": "dm",
        "_repo_name": "repo_name",
    }),

    # Nominal case (without trailing slash)
    ("https://github.com/dm/repo_name", {
        "_is_valid": True,
        "_diagnosis": "",
        "_bare_link": "dm/repo_name",
        "_ssh_link": "git@github.com:dm/repo_name.git",
        "_https_link": "https://github.com/dm/repo_name",
        "_branch": "",
        "_commit": "",
        "_username": "dm",
        "_repo_name": "repo_name",
    }),

    # Nominal case (ssh link)
    ("git@github.com:dm/repo_name.git", {
        "_is_valid": True,
        "_diagnosis": "",
        "_bare_link": "dm/repo_name",
        "_ssh_link": "git@github.com:dm/repo_name.git",
        "_https_link": "https://github.com/dm/repo_name",
        "_branch": "",
        "_commit": "",
        "_username": "dm",
        "_repo_name": "repo_name",
    }),

    # Invalid case (ssh link)
    ("git@github.com:dm/repo_name", {
        "_is_valid": False,
        "_diagnosis": GHLink.err_regex_match_msg,
        "_bare_link": "",
        "_ssh_link": "",
        "_https_link": "",
        "_branch": "",
        "_commit": "",
        "_username": "",
        "_repo_name": "",
    }),

    # Test link to folder (should ignore folder but pick up on branch)
    ("https://github.com/dm/repo_name/tree/main/folder_name", {
        "_is_valid": True,
        "_diagnosis": "",
        "_bare_link": "dm/repo_name",
        "_ssh_link": "git@github.com:dm/repo_name.git",
        "_https_link": "https://github.com/dm/repo_name",
        "_branch": "main",
        "_commit": "",
        "_username": "dm",
        "_repo_name": "repo_name",
    }),

    # Test link to file (should ignore folder but pick up on branch)
    ("https://github.com/dm/repo_name/blob/main/folder_name/file.py", {
        "_is_valid": True,
        "_diagnosis": "",
        "_bare_link": "dm/repo_name",
        "_ssh_link": "git@github.com:dm/repo_name.git",
        "_https_link": "https://github.com/dm/repo_name",
        "_branch": "main",
        "_commit": "",
        "_username": "dm",
        "_repo_name": "repo_name",
    }),

    # Test link to a commit hash
    ("https://github.com/dm/repo_name/commit/d0d7a24ff0e6cd6009a75728f67cde39a5"
     "2ed7b6", {
        "_is_valid": True,
        "_diagnosis": "",
        "_bare_link": "dm/repo_name",
        "_ssh_link": "git@github.com:dm/repo_name.git",
        "_https_link": "https://github.com/dm/repo_name",
        "_branch": "",
        "_commit": "d0d7a24ff0e6cd6009a75728f67cde39a52ed7b6",
        "_username": "dm",
        "_repo_name": "repo_name",
    }),

    # Test link to an invalid commit hash
    ("https://github.com/dm/repo_name/commit/d0d7a24ff0e6cd6009a75728f67cde39a"
     "2ed7b6", {
        "_is_valid": False,
        "_diagnosis": GHLink.err_invalid_commit_hash_msg,
        "_bare_link": "",
        "_ssh_link": "",
        "_https_link": "",
        "_branch": "",
        "_commit": "",
        "_username": "",
        "_repo_name": "",
    }),

    # Test invalid link (does not contain 'commit' or tree
    ("https://github.com/dm/repo_name/no_commit"
     "/d0d7a24ff0e6cd6009a75728f67cde39a"
     "2ed7b6", {
        "_is_valid": False,
        "_diagnosis": GHLink.err_third_pos_wrong,
        "_bare_link": "",
        "_ssh_link": "",
        "_https_link": "",
        "_branch": "",
        "_commit": "",
        "_username": "",
        "_repo_name": "",
    }),

    # Test link to a branch
    ("https://github.com/dm/repo_name/tree/branch", {
        "_is_valid": True,
        "_diagnosis": "",
        "_bare_link": "dm/repo_name",
        "_ssh_link": "git@github.com:dm/repo_name.git",
        "_https_link": "https://github.com/dm/repo_name",
        "_branch": "branch",
        "_commit": "",
        "_username": "dm",
        "_repo_name": "repo_name",
    }),
]

@pytest.mark.parametrize("link_dict_pair", links)
def test_GHLink_valid(link_dict_pair: Tuple[str, Dict[str, Union[str, bool]]]):
    g = GHLink(link_dict_pair[0])
    for key in link_dict_pair[1]:
        assert(link_dict_pair[1][key] == g.__getattribute__(key))

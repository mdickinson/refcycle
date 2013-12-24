Making a release
================

Making a new release should be fairly simple.  For a patchlevel release:

- Make a branch for the release.

- Bump the version number in refcycle/version.py.

- Update the CHANGES file.

- Verify that everything's working as expected:  run tests; build docs.

- Push the release branch to GitHub.

- Wait for Travis CI run to complete.

- Build docs on Read The Docs for the release branch.

- If all looks okay, tag the release on GitHub.

- Do a post-release version bump.

- Upload to PyPI:  'python setup.py sdist upload'.  (Make sure to checkout the correct tag first.)

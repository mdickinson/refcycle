# Copyright 2013 Mark Dickinson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os.path

from setuptools import setup, find_packages


PROJECT_URL = "https://github.com/mdickinson/refcycle"


def get_version_info():
    """Extract version information as a dictionary from version.py."""
    version_info = {}
    with open(os.path.join("refcycle", "version.py"), 'r') as f:
        version_code = compile(f.read(), "version.py", 'exec')
        exec(version_code, version_info)
    return version_info


def long_description(version):
    with open('README.rst') as f:
        contents = f.read()
    # For a released version, we want the description to link to the
    # corresponding docs rather than the docs for master.
    contents = contents.replace(
        'refcycle.readthedocs.org/en/latest',
        'refcycle.readthedocs.org/en/maintenance-v{}'.format(version),
    )
    return contents


version_info = get_version_info()

setup(
    name="refcycle",
    version=version_info['release'],
    author="Mark Dickinson",
    author_email="dickinsm@gmail.com",
    url=PROJECT_URL,
    license="Apache license",
    description="Find and visualise reference cycles between Python objects.",
    long_description=long_description(version_info['version']),
    install_requires=["six"],
    packages=find_packages(),
    platforms=["Windows", "Linux", "Mac OS-X", "Unix", "Solaris"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    data_files=[
        ("", ["README.rst"]),
    ],
)

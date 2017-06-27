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


def long_description(release):
    with open('README.rst') as f:
        contents = f.read()
    # For a released version, we want the description to link to the
    # corresponding docs rather than the docs for master.
    tag = 'v{}'.format(release)
    contents = contents.replace(
        'refcycle.readthedocs.org/en/latest',
        'refcycle.readthedocs.io/en/{}'.format(tag),
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
    long_description=long_description(version_info['release']),
    install_requires=["six"],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Software Development :: Debuggers",
    ],
    data_files=[
        ("", ["README.rst"]),
    ],
)

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


def get_version():
    """Extract version from version.py."""
    version_globals = {}
    with open(os.path.join("refcycle", "version.py"), 'r') as f:
        version_code = compile(f.read(), "version.py", 'exec')
        exec(version_code, version_globals)
    return version_globals['__version__']


def long_description():
    with open('README.rst') as f:
        return f.read()


version = get_version()

setup(
    name="refcycle",
    version=version,
    author="Mark Dickinson",
    author_email="dickinsm@gmail.com",
    url=PROJECT_URL,
    license="Apache license",
    description="Find and visualise reference cycles between Python objects.",
    long_description=long_description(),
    install_requires=["six"],
    packages=find_packages(),
    platforms=["Windows", "Linux", "Mac OS-X", "Unix", "Solaris"],
    download_url="{}/archive/v{}.tar.gz".format(PROJECT_URL, version),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    data_files = [
        ("", ["README.rst"]),
    ],
)

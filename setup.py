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


DESCRIPTION = (
    "Tools for creating and analysing graphs of "
    "Python objects and their references.")
URL = "https://github.com/mdickinson/refcycle"


def get_version():
    """Extract version from version.py."""
    version_globals = {}
    with open(os.path.join("refcycle", "version.py"), 'r') as f:
        version_code = compile(f.read(), "version.py", 'exec')
        exec(version_code, version_globals)
    return version_globals['__version__']


version = get_version()

setup(
    name="refcycle",
    version=version,
    url=URL,
    author="Mark Dickinson",
    author_email="dickinsm@gmail.com",
    description=DESCRIPTION,
    install_requires=["six"],
    packages=find_packages(),
    license="License :: OSI Approved :: Apache Software License",
    platforms=["Windows", "Linux", "Mac OS-X", "Unix", "Solaris"],
    download_url="{}/releases/tag/{}".format(URL, version),
)

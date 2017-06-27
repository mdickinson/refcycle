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
"""
Version information.

"""
major = 0
minor = 2
patch = 0
prerelease = ''  # '', 'alpha', 'beta', etc.

if prerelease:
    __version__ = "{}.{}.{}-{}".format(major, minor, patch, prerelease)
else:
    __version__ = "{}.{}.{}".format(major, minor, patch)

# Release and version for Sphinx purposes.

# The short X.Y version.
version = "{}.{}".format(major, minor)

# The full version, including patchlevel and alpha/beta/rc tags.
release = __version__

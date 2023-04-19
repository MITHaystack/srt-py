import setuptools
from pathlib import Path
import versioneer


scripts = ["bin/srt_controller.py", "bin/srt_runner.py"]

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="srt-py",
    version='v1.1.1',
    include_package_data=True,
    cmdclass=versioneer.get_cmdclass(),
    author="MIT Haystack",
    author_email="srt@mit.edu",
    description="Python implementation of the Small Radio Telescope.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.mit.edu/SmallRadioTelescope/srt-py",
    packages=setuptools.find_packages(),
    scripts=scripts,
    package_data={"": ["*.js", "*.css", "*.ico", "*.png"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

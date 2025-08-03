"""
Setup configuration for Task Reminder CLI Tool.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="task-reminder-cli",
    version="1.0.0",
    author="Sarisha Jaitly",
    author_email="sarisha10jaitly@gmail.com",
    description="A command-line interface tool for managing tasks with cloud synchronization",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/sjaitly13/task-reminder-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "task-cli=task_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="cli, tasks, todo, cloud-sync, mongodb, productivity",
    project_urls={
        "Bug Reports": "https://github.com/sjaitly13/task-reminder-cli/issues",
        "Source": "https://github.com/sjaitly13/task-reminder-cli",
        "Documentation": "https://github.com/sjaitly13/task-reminder-cli#readme",
    },
) 
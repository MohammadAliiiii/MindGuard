#!/usr/bin/env python3
"""Setup script for Idle Security Reminder."""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="idle-security-reminder",
    version="1.0.0",
    author="Enterprise Security Team",
    author_email="security@company.com",
    description="Lightweight desktop app for idle time security reminders",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/company/idle-security-reminder",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "idle-reminder=idle_reminder.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "idle_reminder": ["data/*.yaml", "data/*.txt"],
    },
)

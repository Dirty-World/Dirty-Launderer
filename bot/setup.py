from setuptools import setup, find_packages
import os
from pathlib import Path

# Get the project root directory (parent of bot directory)
PROJECT_ROOT = Path(__file__).parent

# Read README.md from the project root
readme_path = PROJECT_ROOT / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()

# Read requirements from requirements.txt if it exists
install_requires = [
    "python-telegram-bot>=20.0",
    "google-cloud-secret-manager>=2.0.0",
]

# Development dependencies
extras_require = {
    "dev": [
        "pytest>=8.0.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "pytest-asyncio>=0.21.1",
        "pytest-timeout>=2.2.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "mypy>=1.0.0",
        "flake8>=6.0.0",
        "build",
        "twine",
    ],
    "test": [
        "pytest>=8.0.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0",
        "pytest-asyncio>=0.21.1",
        "pytest-timeout>=2.2.0",
    ],
}

setup(
    name="dirty_launderer_bot",
    version="0.1.0",
    author="Your Name",
    author_email="your@email.com",
    description="A Telegram bot for cleaning and sanitizing URLs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Dirty-World/Dirty-Launderer",
    packages=find_packages(where=".", exclude=["tests"]),
    package_data={
        "": ["*.json", "*.yaml", "*.yml"],  # Include all JSON and YAML files
    },
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    python_requires=">=3.11",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "dirty-launderer=main:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/gregmiller/Dirty-Launderer/issues",
        "Source": "https://github.com/gregmiller/Dirty-Launderer",
    },
) 
from setuptools import setup, find_packages

setup(
    name="dirty-launderer-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.0",
        "google-cloud-secret-manager>=2.0.0",
        "pytest>=8.0.0",
        "pytest-cov>=4.1.0",
        "pytest-mock>=3.12.0"
    ],
    python_requires=">=3.11",
) 
from setuptools import setup, find_packages

setup(
    name="data_anon_pipeline",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "spacy",
        "PyYAML==6.0.3",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "data-anon-scan=src.cli:main",
        ],
    },
)

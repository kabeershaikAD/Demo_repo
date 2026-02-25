"""
Setup script for the Agentic Legal RAG system.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentic-legal-rag",
    version="1.0.0",
    author="M.Tech Research Team",
    author_email="research@example.com",
    description="A comprehensive Retrieval-Augmented Generation system for legal question answering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/agentic-legal-rag",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "legal-rag=orchestrator:main",
            "legal-rag-api=api.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.md", "*.yml", "*.yaml"],
    },
    keywords="legal, rag, retrieval-augmented-generation, nlp, ai, law, question-answering",
    project_urls={
        "Bug Reports": "https://github.com/your-username/agentic-legal-rag/issues",
        "Source": "https://github.com/your-username/agentic-legal-rag",
        "Documentation": "https://github.com/your-username/agentic-legal-rag/docs",
    },
)

"""
Setup configuration for Midscene Playwright
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="midscene-playwright",
    version="0.1.0",
    author="Midscene Team",
    author_email="contact@midscene.ai",
    description="AI-powered Playwright extension for intelligent web automation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/midscene-ai/midscene-playwright",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
        ],
        "test": [
            "pytest>=7.0.0", 
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "midscene-playwright=midscene_playwright.cli:main",
        ],
    },
    keywords=[
        "playwright", "automation", "testing", "ai", "vision-language-model",
        "web-automation", "ui-testing", "qwen", "artificial-intelligence"
    ],
    project_urls={
        "Documentation": "https://midscene-playwright.readthedocs.io/",
        "Source": "https://github.com/midscene-ai/midscene-playwright",
        "Tracker": "https://github.com/midscene-ai/midscene-playwright/issues",
    },
)
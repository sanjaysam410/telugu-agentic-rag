from setuptools import setup, find_packages

setup(
    name="telugu-agents",
    version="0.1.0",
    description="Multi-agent architecture for Telugu story processing",
    author="Chandamama Studio Team",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.30.0",
        "google-generativeai>=0.3.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

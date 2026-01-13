from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chat2txt",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A GUI application to convert CHAT format files to TXT format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/chat2txt",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "customtkinter>=5.0.0",
    ],
    entry_points={
        "console_scripts": [
            "chat2txt=chat2txt.gui:main",
        ],
    },
)

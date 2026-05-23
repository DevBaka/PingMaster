from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pingmaster",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="PingMaster - A powerful cross-platform network monitoring tool with ping monitoring, host discovery, and live dashboard",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/pingmaster",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
    ],
    python_requires='>=3.6',
    install_requires=[
        'python-nmap>=0.7.1',
        'psutil>=5.9.0',
        'rich>=10.0.0',
        'python-dotenv>=0.19.0',
    ],
    entry_points={
        'console_scripts': [
            'pingmaster=network_monitor:main',
        ],
    },
    include_package_data=True,
    keywords="network monitoring ping scanner host discovery network visualization latency monitoring packet loss network troubleshooting",
)

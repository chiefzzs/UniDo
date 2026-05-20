from setuptools import setup, find_packages

setup(
    name="trae-assistant",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "pytest",
        "anyio",
        "aiofiles",
        "python-dotenv"
    ],
    extras_require={
        "dev": [
            "pytest-cov",
            "pytest-asyncio"
        ]
    }
)

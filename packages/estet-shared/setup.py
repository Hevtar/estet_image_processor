from setuptools import setup, find_packages

setup(
    name="estet-shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "sqlalchemy[asyncio]>=2.0.23",
        "asyncpg>=0.29.0",
    ],
)

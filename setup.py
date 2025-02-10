from setuptools import setup, find_packages

setup(
    name="ecommerce_calculator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai",
        "pydantic",
        "psycopg2-binary",
    ],
) 
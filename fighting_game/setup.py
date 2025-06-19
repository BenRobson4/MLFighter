from setuptools import setup, find_packages

setup(
    name="fighting-game-ml",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "torch>=1.9.0",
        "numpy>=1.19.0",
        "pygame>=2.0.0",
    ],
    python_requires=">=3.7",
    author="Your Name",
    description="A fighting game framework for ML agent training",
    entry_points={
        'console_scripts': [
            'fighting-game=main:main',
        ],
    },
)
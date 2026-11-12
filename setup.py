"""BeatOven - Modular Generative Music Engine"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="beatoven",
    version="1.0.0",
    description="Modular generative music engine with ABX-Core and SEED protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Applied Alchemy Labs",
    author_email="contact@appliedalchemy.io",
    url="https://github.com/appliedalchemy/beatoven",
    license="Apache-2.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.21.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        "feedparser>=6.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "gpu": [
            "torch>=2.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.24.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
        "audio": [
            "scipy>=1.10.0",
            "soundfile>=0.12.0",
        ],
        "hardware-midi": [
            "python-rtmidi>=1.5.8",
            "cbor2>=5.4.0",
        ],
        "hardware": [
            "pyserial>=3.5",
            "cbor2>=5.4.0",
        ],
        "media": [
            "opencv-python>=4.8.0",
        ],
        "media-full": [
            "opencv-python>=4.8.0",
            "transformers>=4.30.0",
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "timm>=0.9.0",
            "pillow>=10.0.0",
            "librosa>=0.10.0",
        ],
        "all": [
            "torch>=2.0.0",
            "torchvision>=0.15.0",
            "scipy>=1.10.0",
            "soundfile>=0.12.0",
            "pytest>=7.0.0",
            "httpx>=0.24.0",
            "pyserial>=3.5",
            "cbor2>=5.4.0",
            "opencv-python>=4.8.0",
            "transformers>=4.30.0",
            "timm>=0.9.0",
            "pillow>=10.0.0",
            "librosa>=0.10.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "beatoven=beatoven.api.main:main",
            "beatoven-patch=scripts.patch_inspect:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Sound Synthesis",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords=[
        "generative-music",
        "audio-synthesis",
        "modular-synthesis",
        "eurorack",
        "deterministic",
        "machine-learning",
    ],
    include_package_data=True,
    zip_safe=False,
)

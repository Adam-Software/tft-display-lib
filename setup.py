from setuptools import setup

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setup(
    name='robot-eye-display',
    version='0.0.1',
    packages=['robot_eye_display'],
    url='https://github.com/Adam-Software/tft-display-lib',
    license='MIT',
    author='vertigra',
    author_email='a@nesterof.com',
    description='Robot eye display use for TFT-display 1.28 inch',
    long_description_content_type="text/markdown",
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved ::Unknown',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ]
)

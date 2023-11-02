from setuptools import setup

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setup(
    name='serial-motor-control',
    version='0.1.1',
    packages=['serial_motor_control'],
    url='https://github.com/Adam-Software/Serial-motor-control',
    license='MIT',
    author='vertigra',
    author_email='a@nesterof.com',
    description='Motion control used old Api for STM32 firmware',
    long_description_content_type="text/markdown",
    long_description=long_description,
    install_requires=['Adam-Serial-for-controller'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ]
)

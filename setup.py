import os
from setuptools import setup, find_packages
import versioneer
classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: MacOS',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Operating System :: Microsoft',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Topic :: Software Development :: Testing',
]

if os.path.exists('README.md'):
    with open('README.md', 'r') as fp:
        long_description = fp.read().strip()
else:
    long_description = ""

setup(
    name='turing-chatroom-bus',
    version=versioneer.get_version(),
    description='Turing Chatroom Bus',
    long_description=long_description,
    author='Swind Ou',
    author_email='swind@code-life.info',
    license='MIT',
    packages=find_packages(),
    package_data={
        '': ["README.md"]
    },
    install_requires=[
        "python-socketio",
        "aiohttp",
        "socketIO-client",
        "retrying",
        "logzero",
        "zeroconf"
    ],
    classifiers=classifiers,
    cmdclass=versioneer.get_cmdclass(),
)

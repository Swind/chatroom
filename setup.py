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

long_description = ""

if os.path.exists('README.rst'):
    with open('README.rst', 'r') as fp:
        long_description = fp.read().strip()

setup(
    name='turing-chatroom-bus',
    version=versioneer.get_version(),
    description='Chatroom by Socket.IO',
    long_description=long_description,
    author='Swind Ou',
    author_email='swind@code-life.info',
    license='MIT',
    packages=['chatroom'],
    install_requires=[
        "python-socketio",
        "aiohttp",
        "socketIO-client",
        "retrying",
        "logzero",
        "zeroconf"
    ],
    include_package_data=True,
    classifiers=classifiers,
    cmdclass=versioneer.get_cmdclass(),
)

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

setup(
    name='turing-chatroom-bus',
    version=versioneer.get_version(),
    description='Turing Chatroom Bus',
    long_description=open('README.md').read().strip(),
    author='Swind Ou',
    author_email='swind@code-life.info',
    license='MIT',
    packages=find_packages(),
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

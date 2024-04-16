from setuptools import setup


setup(
    name='cldfbench_ditransitive',
    py_modules=['cldfbench_ditransitive'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'ditransitive=cldfbench_ditransitive:Dataset',
        ]
    },
    install_requires=[
        'ditrans2cldf',
        'cldfbench[glottolog]',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)

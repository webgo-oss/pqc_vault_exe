from setuptools import setup
setup(
    name='vault',
    version='1.0',
    py_modules=['main'],
    install_requires=['click', 'rich', 'supabase', 'cryptography'],
    entry_points='''
        [console_scripts]
        vault=main:cli
    ''',
)
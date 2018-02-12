import os
import subprocess

__all__ = ['compile_bibtex']


def compile_bibtex(tex_file):
    """
    Compile the BibTeX into .bbl file.

    Args:
        tex_file (str): Path of the latex file.
    """
    tex_file = os.path.abspath(tex_file)
    bib_file = os.path.splitext(tex_file)[0] + '.bbl'
    work_dir, file_name = os.path.split(tex_file)
    subprocess.check_call(['latexmk', '-pdf', file_name], cwd=work_dir)
    subprocess.check_call(['latexmk', '-C', '-pdf', file_name], cwd=work_dir)
    if not os.path.exists(bib_file):
        raise IOError('{} is not generated.'.format(bib_file))

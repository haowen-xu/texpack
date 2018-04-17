import os
import subprocess

__all__ = ['compile_latex', 'cleanup_compile']


def compile_latex(tex_file, flavour='pdflatex'):
    """
    Compile the LaTeX source file.

    Args:
        tex_file (str): Path of the latex file.
        flavour (str): Flavour of the LaTeX compiler. (default "pdflatex")
    """
    tex_file = os.path.abspath(tex_file)
    pdf_file = os.path.splitext(tex_file)[0] + '.pdf'
    flavour_opt = '-' + {'pdflatex': 'pdf'}.get(flavour, flavour)
    work_dir, file_name = os.path.split(tex_file)
    subprocess.check_call(['latexmk', flavour_opt, file_name], cwd=work_dir)
    if not os.path.exists(pdf_file):
        raise IOError('{} is not generated.'.format(pdf_file))


PRESERVE_FILE_EXT = '.texpack-preserve'

def cleanup_compile(tex_file, preserve=('.bbl', '.pdf')):
    """
    Cleanup the LaTeX build files.

    Args:
        tex_file (str): Path of the latex file.
        preserve (tuple[str]): File extensions to preserve after cleanup.
    """
    tex_file = os.path.abspath(tex_file)
    work_dir, file_name = os.path.split(tex_file)

    # backup preserved files
    preserved_files = []
    for ext in preserve:
        p_name = os.path.splitext(file_name)[0] + ext
        p_path = os.path.join(work_dir, p_name)
        if os.path.exists(p_path):
            pd_path = p_path + PRESERVE_FILE_EXT
            os.rename(p_path, pd_path)
            preserved_files.append((p_path, pd_path))

    # do cleanup
    subprocess.check_call(['latexmk', '-C', file_name], cwd=work_dir)

    # recover preserved files
    for p_path, pd_path in preserved_files:
        os.rename(pd_path, p_path)

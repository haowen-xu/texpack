import os

import click

from texpack.compilation import compile_latex, cleanup_compile
from texpack.imgoptim import optimize_image
from texpack.texparser import TexParser


@click.command()
@click.option('--figure-dpi', help='Figure DPI, for converting PDF into PNG.',
              type=int, default=192, required=False)
@click.option('--to-png', type=click.Choice(['auto', 'always', 'never']),
              default='auto', required=False,
              help='Strategy of converting PDF into PNG, one of '
                   '{"auto", "always", "never"}.')
@click.option('--figure-dir', help='Name of the destination figure directory.',
              default='figures', required=False)
@click.option('-c', '--compile', 'should_compile', help='Compile the LaTeX source.',
              default=False, required=False, is_flag=True)
@click.option('--flavour', help='LaTeX compiler flavour', default='pdflatex', required=False)
@click.argument('source')
@click.argument('destination')
def main(figure_dpi, to_png, figure_dir, should_compile, flavour, source, destination):
    """Pack LaTeX project into a single source file, and optimize figures."""
    if not figure_dir.endswith('/'):
        figure_dir += '/'

    tp = TexParser()
    tp.process(source, destination, figdir_name=figure_dir)

    figure_dir = os.path.join(
        os.path.split(os.path.abspath(destination))[0], figure_dir)

    for image_file in os.listdir(figure_dir):
        optimize_image(os.path.join(figure_dir, image_file),
                       figure_dpi=figure_dpi, to_png=to_png)

    if should_compile:
        compile_latex(destination, flavour=flavour)
        cleanup_compile(destination)

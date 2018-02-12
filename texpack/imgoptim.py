import os
import subprocess
from tempfile import TemporaryDirectory

import shutil

__all__ = ['ImageOptimizer', 'PDFOptimizer', 'optimize_image']


class ImageOptimizer(object):
    """Base class for all image optimizers."""

    def process(self, image_file):
        """
        Process the specified image file.

        Args:
            image_file (str): Path of the image file.

        Returns:
            str: New path of the file, if changed.
        """
        raise NotImplementedError()


class PDFOptimizer(ImageOptimizer):
    """PDF optimizer."""

    def __init__(self, figure_dpi=192, to_png='auto', **kwargs):
        """
        Create a new :class:`PDFOptimizer`.

        Args:
            figure_dpi (int): The DPI for converting the PDF figures into PNG.
            to_png (str): One of {"auto", "always", "never"}.
                If "auto", will convert PDF to PNG only if size is reduced.
                If "always", will always convert PDF to PNG.
                If "never", will not convert PDF to PNG.
            \**kwargs: Consumes the extra options.
        """
        self._figure_dpi = figure_dpi
        self._to_png = to_png

    def _compile_to_png(self, from_file, to_file):
        subprocess.check_call([
            'convert',
            '-verbose',
            '-density',
            str(self._figure_dpi),
            '-strip',
            '-trim',
            from_file + '[0]',
            '-quality',
            '100',
            to_file
        ])

    def process(self, image_file):
        to_file = os.path.splitext(image_file)[0] + '.png'

        if self._to_png == 'always':
            self._compile_to_png(image_file, to_file)
            image_file = to_file

        elif self._to_png == 'auto':
            with TemporaryDirectory() as temp_dir:
                temp_to_file = os.path.join(temp_dir, 'temp.png')
                self._compile_to_png(image_file, temp_to_file)

                if os.stat(image_file).st_size > os.stat(temp_to_file).st_size:
                    shutil.copyfile(temp_to_file, to_file)
                    image_file = to_file

        return image_file


extensions_to_optimizer = {
    '.pdf': PDFOptimizer,
}


def optimize_image(image_file, **kwargs):
    """
    Optimize the specified image file.

    Args:
        image_file (str): Path of the image file.
        \**kwargs: Extra options for the optimizers.

    Returns:
        str: New path of the image file, if changed.
            Old files are ensured to be deleted.
    """
    while True:
        ext = os.path.splitext(image_file)[1]
        if ext not in extensions_to_optimizer:
            break
        optimizer = extensions_to_optimizer[ext](**kwargs)
        image_file2 = optimizer.process(image_file)
        if os.path.samefile(image_file, image_file2):
            break
        os.remove(image_file)
        image_file = image_file2

    return image_file

import codecs
import os
import re

import shutil

from .uniquify import Uniquify

__all__ = ['TexParser']


class FigureResolver(object):
    """
    A :class:`FigureResolver` resolves ``includegraphics`` in latex source,
    locating the very file from the search paths.
    """

    def __init__(self, figure_dirs, extensions=('.png', '.pdf', '.jpg')):
        """
        Create a new :class:`FigureResolver`.

        Args:
            figure_dirs (list[str]): The directories to be searched.
            extensions (list[str]): The extensions to be automatically added.
        """
        self._figure_dirs = tuple(figure_dirs)
        self._extensions = tuple(extensions)

    def resolve(self, figure):
        """
        Resolve the path of `figure`.
        Args:
            figure (str): The figure included by ``includegraphics``.

        Returns:
            The resolved figure path.

        Raises:
            IOError: If the figure cannot be resolved.
        """
        if '.' in os.path.split(figure)[1]:
            extensions = ('',)
        else:
            extensions = self._extensions

        for figure_dir in self._figure_dirs:
            base_path = os.path.join(figure_dir, figure)
            for ext in extensions:
                path = base_path + ext
                if os.path.exists(path):
                    return path

        raise IOError('Figure `{}` cannot be resolved.'.format(figure))


class TexParser(object):
    """
    A :class:`TexParser` merges tex files in a project into one single file,
    and copies all figures into destination directory.
    It may do other transformations such as interpreting the macros,
    according to configurations.
    """

    INCLUDE_INPUT_PATTERN = re.compile(
        r'(?<!%)\\(include|input){([^{}]+)}')
    FIGURE_DIRS_PATTERN = re.compile(
        r'\\graphicspath{([^{}]+|(?:{[^{}]+})(?:,{[^{}]+})*)}')
    INCLUDE_FIGURE_PATTERN = re.compile(
        r'\\includegraphics(\[[^\[\]]*\])?{([^{}]+)}')
    DOC_CLASS_PATTERN = re.compile(
        r'\\documentclass(?:\[[^\[\]]*\])?{([^{}]+)}')
    BIB_STYLE_PATTERN = re.compile(
        r'\\bibliographystyle{([^{}]+)}')
    BIB_PATTERN = re.compile(
        r'\\bibliography{([^{}]+)}')

    def _gather_sources(self, from_dir, from_file):
        def repl_func(m):
            mode = m.group(1)
            path = m.group(2)
            if '.' not in os.path.split(path)[1]:
                path += '.tex'
            cnt = self._gather_sources(from_dir, path)
            delim = '%' * 79
            fmt = (
                '{delim}\n% begin {mode} file: {path}\n{delim}\n'
                '{cnt}\n{delim}\n% end {mode} file: {path}\n{delim}\n'
            )
            if mode == 'include':
                fmt += '\\newpage\n'
            return fmt.format(delim=delim, mode=mode, path=path, cnt=cnt)

        with codecs.open(os.path.join(from_dir, from_file), 'rb',
                         'utf-8') as f:
            return self.INCLUDE_INPUT_PATTERN.sub(repl_func, f.read())

    def _parse_figure_dirs(self, cnt):
        figure_dirs = self.FIGURE_DIRS_PATTERN.search(cnt)
        if figure_dirs:
            figure_dirs = figure_dirs.group(1)
        if figure_dirs and figure_dirs.startswith('{'):
            figure_dirs = figure_dirs[1:-1].split('},{')
        else:
            figure_dirs = [figure_dirs or '']
        return figure_dirs

    def _collect_figures(self, cnt, resolver, to_dir, figdir_name):
        def repl_func(m):
            # parse the latex source
            options = m.group(1) or ''
            figure = m.group(2)
            resolved = resolver.resolve(figure)
            name = os.path.split(resolved)[1]
            base_name, ext = os.path.splitext(name)

            # locate the figure
            if figure not in unique_names:
                unique_names[figure] = uniquify.get(base_name)
            unique_name = unique_names[figure]
            dst_path = os.path.join(to_dir, unique_name + ext)
            dst_dir = os.path.split(dst_path)[0]

            # copy the figure
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
            shutil.copyfile(resolved, dst_path)

            # compose the translated latex source
            return '\\includegraphics{options}{{{figure}}}'.format(
                options=options, figure=unique_name
            )

        # collect figures
        uniquify = Uniquify()
        unique_names = {}
        cnt = self.INCLUDE_FIGURE_PATTERN.sub(repl_func, cnt)

        # rewrite figure path
        graphics_path = '\\graphicspath{{' + figdir_name + '}}'
        m = self.FIGURE_DIRS_PATTERN.search(cnt)
        if m:
            cnt = cnt[:m.start()] + graphics_path + cnt[m.end():]
        else:
            begin_doc = '\\begin{document}'
            cnt = cnt.replace(begin_doc, graphics_path + '\n' + begin_doc)

        return cnt

    def _collect_files(self, cnt, pattern, from_dir, to_dir, extensions):
        m = pattern.search(cnt)
        if m:
            name = m.group(1)
            base_name = os.path.split(name)[1]
            for ext in extensions:
                from_path = os.path.join(from_dir, name + ext)
                to_path = os.path.join(to_dir, base_name + ext)
                if os.path.isfile(from_path):
                    shutil.copy(from_path, to_path)
            cnt = cnt[:m.start(1)] + base_name + cnt[m.end(1):]

        return cnt

    def _collect_doc_class_files(self, cnt, from_dir, to_dir,
                                 extensions=('.sty', '.ins', '.dtx', '.cls')):
        return self._collect_files(
            cnt, self.DOC_CLASS_PATTERN, from_dir, to_dir, extensions)

    def _collect_bib_style_files(self, cnt, from_dir, to_dir,
                                 extensions=('.bbx', '.bst', '.cbx', '.dbx')):
        return self._collect_files(
            cnt, self.BIB_STYLE_PATTERN, from_dir, to_dir, extensions)

    def _collect_bib_files(self, cnt, from_dir, to_dir,
                           extensions=('', '.bib')):
        return self._collect_files(
            cnt, self.BIB_PATTERN, from_dir, to_dir, extensions)

    def process(self, from_path, to_path, figdir_name='./figures/'):
        """
        Process the tex file.

        Args:
            from_path (str): Path of the main source file.
            to_path (str): Destination of the target source file.
            figdir_name (str): Name of the figures directory, alongside
                with `to_path`.

        Returns:
            str: The processed latex source, for further analysis.
        """
        # check the paths
        from_path = os.path.abspath(from_path)
        to_path = os.path.abspath(to_path)
        from_dir = os.path.dirname(from_path)
        to_dir = os.path.dirname(to_path)
        fig_dir = os.path.join(to_dir, figdir_name)

        # gather the source files
        cnt = self._gather_sources(from_dir, os.path.relpath(from_path, from_dir))

        # parse the figure include dirs, and create the figure resolver
        figure_dirs = self._parse_figure_dirs(cnt)
        figure_resolver = FigureResolver(
            [os.path.join(from_dir, figure_dir) for figure_dir in figure_dirs])

        # collect all figures
        cnt = self._collect_figures(cnt, figure_resolver, fig_dir, figdir_name)

        # collect document class files
        cnt = self._collect_doc_class_files(cnt, from_dir, to_dir)

        # collect bibliography style files
        cnt = self._collect_bib_style_files(cnt, from_dir, to_dir)

        # collect bibliography files
        cnt = self._collect_bib_files(cnt, from_dir, to_dir)

        # generate the target latex file
        if not os.path.isdir(to_dir):
            os.makedirs(to_dir)
        with codecs.open(os.path.join(to_path), 'wb', 'utf-8') as f:
            f.write(cnt)

        return cnt

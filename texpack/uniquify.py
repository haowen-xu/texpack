__all__ = ['Uniquify']


class Uniquify(object):
    """Class to assign unique names."""

    def __init__(self):
        self._assigned_names = set()

    def get(self, name):
        """
        Get a unique name according to suggested `name`.

        Args:
            name (str): The suggested name.

        Returns:
            str: The uniquified name.  "." in the name is ensured to be
                replaced by "_".
        """
        name = str(name).replace('.', '_')
        candidate = name
        index = 1
        while candidate in self._assigned_names:
            candidate = name + '_' + str(index)
            index += 1
        self._assigned_names.add(candidate)
        return candidate

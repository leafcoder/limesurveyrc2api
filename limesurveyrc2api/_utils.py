import random

class IDGenerator(object):

    '''https://stackoverrun.com/cn/q/287179'''

    ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"

    def __init__(self, length=8):
     self._alphabet_length = len(self.ALPHABET)
     self._id_length = length

    def _encode_int(self, n):
        # Adapted from:
        # Source: https://stackoverflow.com/a/561809/1497596
        # Author: https://stackoverflow.com/users/50902/kmkaplan

        encoded = ''
        while n > 0:
            n, r = divmod(n, self._alphabet_length)
            encoded = self.ALPHABET[r] + encoded
        return encoded

    def generate_id(self):
        """Generate an ID without leading zeros.

        For example, for an ID that is eight characters in length, the
        returned values will range from '10000000' to 'zzzzzzzz'.
        """ 

        start = self._alphabet_length ** (self._id_length - 1)
        end = self._alphabet_length ** self._id_length - 1
        return self._encode_int(random.randint(start, end))
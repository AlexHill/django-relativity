import math
from collections import namedtuple


def regular(i):
    digits = [int(c) for c in str(i)]
    diffs = [b - a for a, b in zip(digits[:-1], digits[1:])]
    return len(diffs) > 1 and all(diff == diffs[0] for diff in diffs)


def georegular(i):
    digits = [int(c) for c in str(i)]
    diffs = [b - a for a, b in zip(digits[:-1], digits[1:])]
    diff_diffs = [b - a for a, b in zip(diffs[:-1], diffs[1:])]
    return len(diff_diffs) > 1 and all(diff == diff_diffs[0] for diff in diff_diffs)


def even(i):
    return i % 2 == 0


def odd(i):
    return i % 2 == 1


def same_digits(i):
    txt = str(i)
    return txt.count(txt[0]) == len(txt)


def multiple_of_17(i):
    return i % 17 == 0


def digits_add_to_10(i):
    digits = [int(c) for c in str(i)]
    return sum(digits) == 10


def gen_primes():
    """ Generate an infinite sequence of prime numbers.
    """
    # Maps composites to primes witnessing their compositeness.
    # This is memory efficient, as the sieve is not "run forward"
    # indefinitely, but only as long as required by the current
    # number being tested.
    #
    D = {}

    # The running integer that's checked for primeness
    q = 2

    while True:
        if q not in D:
            # q is a new prime.
            # Yield it and mark its first multiple that isn't
            # already marked in previous iterations
            #
            yield q
            D[q * q] = [q]
        else:
            # q is composite. D[q] is the list of primes that
            # divide it. Since we've reached q, we no longer
            # need it in the map, but we'll mark the next
            # multiples of its witnesses to prepare for larger
            # numbers
            #
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]

        q += 1


def prime(i):
    while i > prime._max:
        prime._max = next(prime._gen)
        prime._cache.add(prime._max)
    return i in prime._cache
prime._max = 0
prime._cache = set()
prime._gen = gen_primes()


def power_of_two(i):
    try:
        return math.log(i, 2).is_integer()
    except ValueError:
        return False


def palindromic(i):
    digits = str(i)
    return digits == digits[::-1]


def descending(i):
    digits = [int(c) for c in str(i)]
    pairs = list(zip(digits[:-1], digits[1:]))
    return all(a >= b for a, b in pairs) and any(a > b for a, b in pairs)


def ascending(i):
    digits = [int(c) for c in str(i)]
    pairs = list(zip(digits[:-1], digits[1:]))
    return all(a <= b for a, b in pairs) and any(a < b for a, b in pairs)


Predicate = namedtuple('Predicate', ['id', 'name', 'fn'])

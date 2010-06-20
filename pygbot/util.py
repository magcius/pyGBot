
def pretty_print_list(List, use_both=False):
    List = [i for i in List if i is not None]
    Len = len(List)

    if not List:
        return ""
    
    if Len == 1:
        return List[0]
    elif use_both and Len == 2:
        return "both %s and %s" % tuple(List)

    return ("%s, " * (Len-1)) % tuple(List[:-1]) + (', and %s' % List[-1])

def pp_index(List, start=1, use_both=False):
    return pretty_print_list(["%d: %s" % (i, v) for i, v in
                              zip(itertools.count(start), List)], use_both)

def plural(L, plural="s", singular=""):
    """
    Use like this:
    >>> 'You have %d card%s' % (len(L), plural(L))
    'You have 1 card'
    >>> 'I have %d dictionar%s' (len(L), plural(L, 'ies', 'y'))
    'I have 3 dictionaries'
    >>> 'My friend has %d potato%s' % (len(L), plural(L, 'es'))
    'My friend has 0 potatoes'
    """
    return singular if len(L) == 1 else plural

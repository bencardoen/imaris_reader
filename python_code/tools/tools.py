import os

def treedir(pathname):
    '''
    Walk a path, and build a recursive dictionary of <path, content> on the way.
    :param pathname: top level directory / path
    :return: nested dictionary of <path, <contents>>, leafs are <path, filename>, nodes are <path, <dict>>
    '''
    (t, d, f)  = next(os.walk(pathname))
    return {**{dir:treedir(os.path.join(pathname, dir)) for dir in d},**{file:os.path.join(t, file) for file in f}}


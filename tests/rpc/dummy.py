def method1(name):
    return "Hello {0}".format(name)


def method2(start=1, end=100):
    from random import randint
    return randint(start, end)

def error_method():
    raise Exception('Error here')

from adrest.resources.rpc import get_request


def method1(name):
    return "Hello {0}".format(name)


def method2(start=1, end=100):
    from random import randint
    return randint(start, end)


def error_method():
    raise Exception('Error here')


@get_request
def method3(request, name):
    return request.method + name


def __private_method():
    raise Exception("I am hidden!")

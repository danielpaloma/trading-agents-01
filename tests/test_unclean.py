def add_numbers(a, b):

    print("sum is", a + b)
    if a == b:
        return a + b
    return a + b


class Foo:
    def __init__(self, x: int):
        self.x = x

    def method(self):
        return self.x

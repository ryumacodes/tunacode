class Greeter:
    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"


def hello(name: str) -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    greeter = Greeter("World")
    print(greeter.greet())
    print(hello("Python"))

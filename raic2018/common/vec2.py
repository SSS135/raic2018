import math


class Vec2:
    def __init__(self, x=0.0, y=0.0):
        if isinstance(x, list) or isinstance(x, tuple):
            x, y = x
        self.x = x
        self.y = y

    @property
    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def clamp(self, a, b):
        ax, ay = (a.x, a.y) if isinstance(a, Vec2) else (a, a)
        bx, by = (b.x, b.y) if isinstance(b, Vec2) else (b, b)
        return Vec2(max(ax, min(bx, self.x)), max(ay, min(by, self.y)))

    def __add__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x + other.x, self.y + other.y)
        else:
            return Vec2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x - other.x, self.y - other.y)
        else:
            return Vec2(self.x - other, self.y - other)

    def __rsub__(self, other):
        return Vec2(other - self.x, other - self.y)

    def __mul__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x * other.x, self.y * other.y)
        else:
            return Vec2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x / other.x, self.y / other.y)
        else:
            return Vec2(self.x / other, self.y / other)

    def __floordiv__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x // other.x, self.y // other.y)
        else:
            return Vec2(self.x // other, self.y // other)

    def __rtruediv__(self, other):
        return Vec2(other / self.x, other / self.y)

    def __rfloordiv__(self, other):
        return Vec2(other // self.x, other // self.y)

    def __eq__(self, other):
        if isinstance(other, Vec2):
            return self.x == other.x and self.y == other.y
        else:
            return False

    def __pow__(self, power, modulo=None):
        if isinstance(power, Vec2):
            return Vec2(self.x ** power.x, self.y ** power.y)
        else:
            return Vec2(self.x ** power, self.y ** power)

    def __iter__(self):
        return iter((self.x, self.y))

    def __repr__(self):
        return str.format('{{ x: {}, y: {} }}', self.x, self.y)

    __rmul__ = __mul__
    __radd__ = __add__
    __str__ = __repr__


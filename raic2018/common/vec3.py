import math


class Vec3():
    def __init__(self, x=0.0, y=0.0, z=0.0):
        if isinstance(x, list) or isinstance(x, tuple):
            x, y, z = x
        self.x = x
        self.y = y
        self.z = z

    @property
    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    @property
    def normalized(self):
        mag = self.magnitude
        if mag < 1e-10:
            return Vec3()
        return self / mag

    def clamp_pointwise(self, a, b):
        ax, ay, az = (a.x, a.y, a.z) if isinstance(a, Vec3) else (a, a, a)
        bx, by, bz = (b.x, b.y, b.z) if isinstance(b, Vec3) else (b, b, b)
        return Vec3(max(ax, min(bx, self.x)), max(ay, min(by, self.y)), max(az, min(bz, self.z)))

    def clamp_length(self, max_len):
        mag = self.magnitude
        return self.clone() if mag <= max_len else self / mag * max_len

    def __matmul__(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    @staticmethod
    def dot(a, b):
        return a.x * b.x + a.y * b.y + a.z * b.z

    def clone(self):
        return Vec3(self.x, self.y, self.z)

    def __add__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
        else:
            return Vec3(self.x + other, self.y + other, self.z + other)

    def __sub__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
        else:
            return Vec3(self.x - other, self.y - other, self.z - other)

    def __rsub__(self, other):
        return Vec3(other - self.x, other - self.y, other - self.z)

    def __mul__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)
        else:
            return Vec3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x / other.x, self.y / other.y, self.z / other.z)
        else:
            return Vec3(self.x / other, self.y / other, self.z / other)

    def __floordiv__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x // other.x, self.y // other.y, self.z // other.z)
        else:
            return Vec3(self.x // other, self.y // other, self.z // other)

    def __rtruediv__(self, other):
        return Vec3(other / self.x, other / self.y, other / self.z)

    def __rfloordiv__(self, other):
        return Vec3(other // self.x, other // self.y, other // self.z)

    def __eq__(self, other):
        if isinstance(other, Vec3):
            return self.x == other.x and self.y == other.y and self.z == other.z
        else:
            return False

    def __pow__(self, power, modulo=None):
        if isinstance(power, Vec3):
            return Vec3(self.x ** power.x, self.y ** power.y, self.z ** power.z)
        else:
            return Vec3(self.x ** power, self.y ** power, self.z ** power)

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __repr__(self):
        return str.format('{{ x: {}, y: {}, z: {} }}', self.x, self.y, self.z)

    __rmul__ = __mul__
    __radd__ = __add__
    __str__ = __repr__


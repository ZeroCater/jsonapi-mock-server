import random

from faker import Faker

from fake_provider import CatererProvider


class BaseFaker(object):
    def __init__(self):
        pass

    def generate_value(self):
        raise NotImplementedError


class NullableBaseFaker(BaseFaker):
    def generate_value(self):
        if random.choice([True, False]):
            return None
        return super(NullableBaseFaker, self).generate_value()


class IntFaker(BaseFaker):
    def __init__(self, start, end):
        super(IntFaker, self).__init__()
        self.start = start
        self.end = end

    def generate_value(self):
        return random.randint(self.start, self.end)


class ChoiceFaker(BaseFaker):
    def __init__(self, options):
        super(ChoiceFaker, self).__init__()
        self.options = options

    def generate_value(self):
        return random.choice(self.options)


class BooleanFaker(BaseFaker):
    def __init__(self):
        super(BooleanFaker, self).__init__()

    def generate_value(self):
        return random.choice((True, False))


class StringFaker(BaseFaker):
    fake = Faker()
    fake.add_provider(CatererProvider)

    def __init__(self, faker_provider):
        super(StringFaker, self).__init__()
        self.faker_provider = faker_provider

    def generate_value(self):
        return getattr(self.fake, self.faker_provider)()


class NullableIntFaker(NullableBaseFaker, IntFaker):
    pass


class NullableBooleanFaker(NullableBaseFaker, BooleanFaker):
    pass

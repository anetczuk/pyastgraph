class Base:
    pass


class Worker(Base):
    PARAM = 44

    def __init__(self):
        self.field_data = 333

    def do_work(self):
        pass

    @staticmethod
    def initialize():
        pass

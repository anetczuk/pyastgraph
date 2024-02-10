#
#
#


class Invalid:
    def __init__(self):
        self.data_field = None
        self.execute()
        self.invalid_call()  # non existing method  # pylint: disable=E1101

    def execute(self):
        self.data_field = "xxx"

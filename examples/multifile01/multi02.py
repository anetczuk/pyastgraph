#
#
#


class Runner:

    STATIC_FIELD = "initial_value"

    def __init__(self):
        self.instance_field = []
        self.execute()

    def execute(self):
        print("executing", self.instance_field)
        self.STATIC_FIELD = "new_value"

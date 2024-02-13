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


def main():
    runner = Runner()
    runner.instance_field = ["aaa"]
    runner.execute()
    Runner.STATIC_FIELD = "main_value"


if __name__ == "__main__":
    main()

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


def main():
    runner = Runner()
    runner.instance_field = ["aaa"]
    runner.execute()


if __name__ == "__main__":
    main()

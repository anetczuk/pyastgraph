#
#
#


class Worker:
    def __init__(self):
        self.data_dict = {}

    def work(self):
        return self.data_dict.get("abc")


class Runner:
    def __init__(self):
        self.worker = Worker()

    def execute(self):
        print("executing")
        return self.worker.work()


def main():
    runner = Runner()
    runner.execute()
    runner.worker.data_dict.get("qwe")


if __name__ == "__main__":
    main()

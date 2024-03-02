#
#
#

from threading import Thread

from thread01.worker01 import Worker


class Runner:
    def __init__(self):
        self.worker = Worker()
        self.thread = Thread(target=self.worker.work, args=[])

    def execute(self):
        self.thread.start()
        self.thread.join()
        self.result()

    def result(self):
        print("result")


def main():
    runner = Runner()
    runner.execute()


if __name__ == "__main__":
    main()

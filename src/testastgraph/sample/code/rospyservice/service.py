import rospy  # pylint: disable=E0401

from rospyservice.worker import Worker


class ServiceOwner:
    def __init__(self):
        self.worker = Worker()
        self.service = rospy.Service("~service", bool, self.service_callback)

    def listen(self):
        pass

    def service_callback(self, enabled):
        if enabled:
            self.worker.do_work()
        if not enabled:
            print("not enabled")


def main():
    service = ServiceOwner()
    service.listen()


if __name__ == "__main__":
    main()

#
#
#

from multifile01.multi02 import Runner


def main():
    runner = Runner()
    runner.instance_field = ["done"]
    runner.execute()
    Runner.STATIC_FIELD = "main_value"


if __name__ == "__main__":
    main()

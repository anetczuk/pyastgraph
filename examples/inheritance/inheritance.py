class Base:
    def execute(self):
        print("calling execute")
        self._execute_priv()

    def work(self):
        print("calling base work")

    def wait(self):
        print("calling base wait")

    def _execute_priv(self):
        print("calling base _execute_priv")


class Item(Base):
    def _execute_priv(self):
        print("calling _execute_priv")

    def work(self):
        print("calling work")

    def wait(self):
        print("calling wait")
        super().wait()


item = Item()
item.execute()
item.work()
item.wait()

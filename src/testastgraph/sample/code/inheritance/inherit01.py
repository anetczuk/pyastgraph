class Base:
    def __init__(self):
        print("calling Base ctor")
        self.field = None

    def do_work(self):
        print("working")

    def execute_base(self):
        print("calling execute_base")
        self._execute_priv()

    def _execute_priv(self):
        # override if needed
        pass


class Item(Base):
    # default constructor here

    def execute(self):
        print("calling execute")
        self.do_work()
        self.execute_base()

    def _execute_priv(self):
        print("calling _execute_priv")
        self.do_work()


item = Item()
item.execute()

print("done")

#
# Example of simple method override. The method is executed through base class.
#


class Base:
    def execute(self):
        self.do_work()

    def do_work(self):
        print("Base working")


class Item(Base):
    def do_work(self):
        print("Item working")


item = Item()
item.execute()

print("done")

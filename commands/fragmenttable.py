from commands.base import Command
from commands import register
from squashfs_fs import SquashFSParser

@register()
class FtableCommand(Command):
    @staticmethod
    def get_help():
        return "Mount the SquashFS filesystem for browsing"

    def execute(self, *args) -> None:
        if not hasattr(self.explorer, 'fs_parser') or not self.explorer.fs_parser:
            print("SquashFS filesystem not mounted. Use 'mount' command first.")
            return

        table = self.explorer.fs_parser.fragment_table
        print(table)

        print("Fragment Table")
        print("--------------")
        for i in range(0, len(table)):
            print(f"Index: {i}")
            table[i].print()

from commands.base import Command
from commands import register

@register()
class StatCommand(Command):

    @staticmethod
    def get_help() -> str:
        return "Show details for a given inode number"

    def execute(self, *args) -> None:
        if not hasattr(self.explorer, 'fs_parser') or not self.explorer.fs_parser:
            print("SquashFS filesystem not mounted. Use 'mount' command first.")
            return

        try:

            inodes = self.explorer.fs_parser.inodes

            if args:
                num = int(args[0])
            else:
                raise Exception("stat requires an inode number as a parameter")

            found = False
            for inode in inodes:
                if inode.header.inode_num == num:
                    found = True
                    inode.print()
                    return

            if not found:
                print("No matching inode found.")
                return

        except Exception as e:
            print(f"Error listing directory: {e}")

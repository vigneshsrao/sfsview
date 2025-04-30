from commands.base import Command
from commands import register

@register()
class InodesCommand(Command):
    @staticmethod
    def get_help() -> str:
        return "Show valid inode id's"

    def execute(self, *args) -> None:
        if not hasattr(self.explorer, 'fs_parser') or not self.explorer.fs_parser:
            print("SquashFS filesystem not mounted. Use 'mount' command first.")
            return

        inodes = self.explorer.fs_parser.inodes
        print(f"Inodes: 1-{len(inodes)}");

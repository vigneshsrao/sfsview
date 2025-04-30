from commands.base import Command
from commands import register

@register()
class VersionCommand(Command):
    @staticmethod
    def get_help():
        return "Show SquashFS version"
    
    def execute(self, *args):
        if not self.explorer.superblock:
            print("No valid superblock found. Cannot determine version.")
            return
            
        sb = self.explorer.superblock
        print(f"\nSquashFS Version: {sb.version_major}.{sb.version_minor}")

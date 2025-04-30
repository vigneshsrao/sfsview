from commands.base import Command
from commands import register
from squashfs_fs import SquashFSParser

@register()
class MountCommand(Command):
    @staticmethod
    def get_help():
        return "Mount the SquashFS filesystem for browsing"
    
    def execute(self, *args):
        # try:
            # Initialize the filesystem parser
            self.explorer.fs_parser = SquashFSParser(self.explorer.squashfs_file)
           
            if self.explorer.fs_parser.superblock:
                print("SquashFS filesystem parsed successfully.")
            else:
                print("Failed to mount SquashFS filesystem.")
        # except Exception as e:
        #     print(f"Error mounting filesystem: {e}")

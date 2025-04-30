import sys
from commands.base import Command
from commands import register

@register('exit', 'quit')
class ExitCommand(Command):
    @staticmethod
    def get_help():
        return "Exit the explorer"
    
    def execute(self, *args):
        print("Exiting SquashFS Explorer. Goodbye!")
        sys.exit(0)

# Base class for all commands
class Command:
    
    def __init__(self, explorer):
        self.explorer = explorer
    
    @staticmethod
    def get_help():
        """Return help text for the command"""
        return "No help available for this command"
    
    def execute(self, *args) :
        """Execute the command with the given arguments"""
        raise NotImplementedError("Command subclasses must implement execute()")
    
    @staticmethod
    def _format_size(size_bytes):
        """Format byte size to human-readable format"""
        # Convert bytes to human-readable format
        for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB']:
            if size_bytes < 1024.0 or unit == 'TiB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} {unit}"

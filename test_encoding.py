import sys
import io

class LogStream(io.StringIO):
    @property
    def encoding(self):
        return 'utf-8'

sys.stdout = LogStream()
print('🚀')

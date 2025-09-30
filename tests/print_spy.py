class PrintSpy:
    def __init__(self):
        self.captured_output = []

    def __call__(self, *args, **kwargs):
        if args:
            message = ' '.join(str(arg) for arg in args)
        else:
            message = ''

        self.captured_output.append(message)

    def get_output(self):
        return '\n'.join(self.captured_output)

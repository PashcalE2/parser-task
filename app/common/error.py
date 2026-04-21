from datetime import date


class DateAlreadyPresentError(RuntimeError):
    date: "date"

    def __init__(self, date: "date", *args):
        super().__init__(*args)
        self.date = date

    def __str__(self):
        return f"Date '{self.date}' already present."

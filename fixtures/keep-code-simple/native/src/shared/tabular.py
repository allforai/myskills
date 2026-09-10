import csv
import io


def write_csv(rows):
    """Public CSV writer used by exports; includes a final CRLF."""
    stream = io.StringIO(newline="")
    csv.writer(stream).writerows(rows)
    return stream.getvalue()

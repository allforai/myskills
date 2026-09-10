def export_catalog(rows):
    lines = []
    for row in rows:
        cells = []
        for value in row:
            cell = "" if value is None else str(value)
            if any(character in cell for character in (',', '"', '\r', '\n')):
                cell = '"' + cell.replace('"', '""') + '"'
            cells.append(cell)
        lines.append(','.join(cells) + '\r\n')
    return ''.join(lines)

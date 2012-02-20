def serialize(result):
    if result is None:
        return ''
    elif type(result) == bool:
        return str(int(result))
    elif type(result) == tuple:
        return ','.join([serialize(x) for x in result])
    else:
        return str(result)

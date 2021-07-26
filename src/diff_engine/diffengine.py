def diff(new_obj, old_obj):
    spec = {}

    def _get_nested_value(obj, chain):
        if len(chain):
            if chain[0] not in obj:
                return None
            else:
                return _get_nested_value(obj[chain[0]], chain[1:])
        else:
            return obj

    def _set_nested_spec(obj, value, chain):
        if len(chain) > 0:
            if chain[0] not in obj:
                obj[chain[0]] = {}
            _set_nested_spec(obj[chain[0]], value, chain[1:])
        else:
            obj["$set"] = value

    def _merge_nested_spec(obj, value, chain):
        if len(chain) > 0:
            if chain[0] not in obj:
                obj[chain[0]] = {}
            _merge_nested_spec(obj[chain[0]], value, chain[1:])
        else:
            if "$merge" not in obj:
                obj["$merge"] = value
            else:
                obj["$merge"].update(value)

    def nested(root, chain=None):
        if chain is None:
            chain = []

        state = _get_nested_value(old_obj, chain)
        if not type(root) == dict:
            if root != state:
                _set_nested_spec(spec, root, chain)
        elif type(root) == dict and not type(state) == dict:
            _set_nested_spec(spec, root, chain)
        else:
            for k in root:
                if k not in state:
                    _merge_nested_spec(spec, {k: root[k]}, chain.copy())
                else:
                    nested(root[k], chain.copy() + [k])

    nested(new_obj)
    return spec

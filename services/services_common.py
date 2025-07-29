# common/services_common.py


def get_choice_labels(enum_class, selected_keys):
    if not selected_keys:
        return []
    return [enum_class(key).label for key in selected_keys if key in enum_class.values]

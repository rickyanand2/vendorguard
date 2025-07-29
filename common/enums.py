def get_choice_labels(enum_class, selected_keys):
    """
    Converts a list of enum keys to their human-readable labels.

    Args:
        enum_class (models.TextChoices): The TextChoices enum.
        selected_keys (list): List of selected enum keys (str).

    Returns:
        list: List of human-readable labels (str).
    """
    if not selected_keys:
        return []
    return [enum_class(key).label for key in selected_keys if key in enum_class.values]

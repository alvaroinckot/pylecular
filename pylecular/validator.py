class ValidationError(Exception):
    """Custom exception for parameter validation errors."""
    def __init__(self, message, field=None, type=None, expected=None, got=None):
        self.field = field
        self.type = type
        self.expected = expected
        self.got = got
        self.message = message
        super().__init__(message)


def validate_type(value, expected_type):
    """Validate if a value is of the expected type."""
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    elif expected_type == "null":
        return value is None
    elif expected_type == "any":
        return True
    return False


def validate_param_rule(name, value, rule):
    """Validate a parameter against its rule."""
    # Convert simple string rule to dict form
    if isinstance(rule, str):
        rule = {"type": rule}
    
    # Check if parameter is required
    if rule.get("required", False) and value is None:
        raise ValidationError(f"Parameter '{name}' is required", field=name)
    
    # If value is None and not required, skip further validation
    if value is None and not rule.get("required", False):
        return True
    
    # Type validation
    if "type" in rule:
        if not validate_type(value, rule["type"]):
            raise ValidationError(
                f"Parameter '{name}' must be of type '{rule['type']}'",
                field=name, 
                type="type_mismatch", 
                expected=rule["type"], 
                got=type(value).__name__
            )
    
    # Number validations
    if rule["type"] == "number":
        # Min value
        if "min" in rule and value < rule["min"]:
            raise ValidationError(
                f"Parameter '{name}' must be greater than or equal to {rule['min']}",
                field=name,
                type="min_value",
                expected=rule["min"],
                got=value
            )
        
        # Max value
        if "max" in rule and value > rule["max"]:
            raise ValidationError(
                f"Parameter '{name}' must be less than or equal to {rule['max']}",
                field=name,
                type="max_value",
                expected=rule["max"],
                got=value
            )
        
        # Greater than
        if "gt" in rule and value <= rule["gt"]:
            raise ValidationError(
                f"Parameter '{name}' must be greater than {rule['gt']}",
                field=name,
                type="greater_than",
                expected=rule["gt"],
                got=value
            )
        
        # Greater than or equal
        if "gte" in rule and value < rule["gte"]:
            raise ValidationError(
                f"Parameter '{name}' must be greater than or equal to {rule['gte']}",
                field=name,
                type="greater_than_equal",
                expected=rule["gte"],
                got=value
            )
        
        # Less than
        if "lt" in rule and value >= rule["lt"]:
            raise ValidationError(
                f"Parameter '{name}' must be less than {rule['lt']}",
                field=name,
                type="less_than",
                expected=rule["lt"],
                got=value
            )
        
        # Less than or equal
        if "lte" in rule and value > rule["lte"]:
            raise ValidationError(
                f"Parameter '{name}' must be less than or equal to {rule['lte']}",
                field=name,
                type="less_than_equal",
                expected=rule["lte"],
                got=value
            )
    
    # String validations
    if rule["type"] == "string":
        # Min length
        if "minLength" in rule and len(value) < int(rule["minLength"]):
            raise ValidationError(
                f"Parameter '{name}' must have a minimum length of {rule['minLength']}",
                field=name,
                type="min_length",
                expected=rule["minLength"],
                got=len(value)
            )
        
        # Max length
        if "maxLength" in rule and len(value) > int(rule["maxLength"]):
            raise ValidationError(
                f"Parameter '{name}' must have a maximum length of {rule['maxLength']}",
                field=name,
                type="max_length",
                expected=rule["maxLength"],
                got=len(value)
            )
        
        # Pattern
        if "pattern" in rule:
            import re
            if not re.match(rule["pattern"], value):
                raise ValidationError(
                    f"Parameter '{name}' must match the pattern '{rule['pattern']}'",
                    field=name,
                    type="pattern_mismatch",
                    expected=rule["pattern"],
                    got=value
                )
    
    # Array validations
    if rule["type"] == "array":
        # Min items
        if "minItems" in rule and len(value) < int(rule["minItems"]):
            raise ValidationError(
                f"Parameter '{name}' must have a minimum of {rule['minItems']} items",
                field=name,
                type="min_items",
                expected=rule["minItems"],
                got=len(value)
            )
        
        # Max items
        if "maxItems" in rule and len(value) > int(rule["maxItems"]):
            raise ValidationError(
                f"Parameter '{name}' must have a maximum of {rule['maxItems']} items",
                field=name,
                type="max_items",
                expected=rule["maxItems"],
                got=len(value)
            )
        
        # Items validation (if items have a specific type)
        if "items" in rule and isinstance(rule["items"], dict) and "type" in rule["items"]:
            for i, item in enumerate(value):
                try:
                    validate_param_rule(f"{name}[{i}]", item, rule["items"])
                except ValidationError as e:
                    # Wrap the error to include array index information
                    raise ValidationError(
                        e.message,
                        field=e.field,
                        type=e.type,
                        expected=e.expected,
                        got=e.got
                    ) from e
    
    # Enum validation (value must be one of the specified values)
    if "enum" in rule and value not in rule["enum"]:
        raise ValidationError(
            f"Parameter '{name}' must be one of: {', '.join(map(str, rule['enum']))}",
            field=name,
            type="enum_mismatch",
            expected=rule["enum"],
            got=value
        )
    
    return True


def validate_params(params, schema):
    """
    Validate parameters against a schema.
    
    Args:
        params (dict): The parameters to validate
        schema (dict or list): The validation schema
        
    Returns:
        bool: True if validation passes
        
    Raises:
        ValidationError: If validation fails
    """
    # Handle the case where schema is a list of parameter names
    if isinstance(schema, list):
        for param_name in schema:
            if param_name not in params:
                raise ValidationError(
                    f"Parameter '{param_name}' is required",
                    field=param_name
                )
        return True
    
    # Handle the case where schema is a dict
    if isinstance(schema, dict):
        # First, check required parameters
        for param_name, param_rule in schema.items():
            # Convert simple string rule to dict form
            rule = param_rule
            if isinstance(rule, str):
                rule = {"type": rule}
            
            # Check if required
            if (isinstance(param_rule, dict) and param_rule.get("required", False) 
                and param_name not in params):
                raise ValidationError(
                    f"Parameter '{param_name}' is required",
                    field=param_name
                )
        
        # Then validate all parameters that are present
        for param_name, param_value in params.items():
            if param_name in schema:
                validate_param_rule(param_name, param_value, schema[param_name])
    
    return True

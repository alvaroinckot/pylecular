import pytest
from pylecular.validator import validate_params, validate_param_rule, ValidationError, validate_type


def test_validate_type():
    
    # Test string type
    assert validate_type("test", "string") is True
    assert validate_type(123, "string") is False
    
    # Test number type
    assert validate_type(123, "number") is True
    assert validate_type(123.45, "number") is True
    assert validate_type("123", "number") is False
    assert validate_type(True, "number") is False  # Booleans are not numbers
    
    # Test boolean type
    assert validate_type(True, "boolean") is True
    assert validate_type(False, "boolean") is True
    assert validate_type(1, "boolean") is False
    
    # Test array type
    assert validate_type([], "array") is True
    assert validate_type([1, 2, 3], "array") is True
    assert validate_type({}, "array") is False
    
    # Test object type
    assert validate_type({}, "object") is True
    assert validate_type({"a": 1}, "object") is True
    assert validate_type([], "object") is False
    
    # Test null type
    assert validate_type(None, "null") is True
    assert validate_type(False, "null") is False
    
    # Test any type
    assert validate_type("anything", "any") is True
    assert validate_type(123, "any") is True
    assert validate_type(None, "any") is True


def test_validate_param_rule_required():
    # Test required validation
    validate_param_rule("name", "John", {"type": "string", "required": True})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("name", None, {"type": "string", "required": True})
    assert "required" in str(exc.value)
    
    # Not required and None should pass
    validate_param_rule("name", None, {"type": "string", "required": False})


def test_validate_param_rule_string():
    # Test string validation
    validate_param_rule("name", "John", {"type": "string"})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("name", 123, {"type": "string"})
    assert "type" in str(exc.value)
    
    # Test minLength
    validate_param_rule("name", "John", {"type": "string", "minLength": 4})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("name", "Jo", {"type": "string", "minLength": 3})
    assert "minimum length" in str(exc.value)
    
    # Test maxLength
    validate_param_rule("name", "John", {"type": "string", "maxLength": 4})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("name", "John Doe", {"type": "string", "maxLength": 6})
    assert "maximum length" in str(exc.value)
    
    # Test pattern
    validate_param_rule("email", "test@example.com", {"type": "string", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("email", "invalid-email", {"type": "string", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"})
    assert "pattern" in str(exc.value)


def test_validate_param_rule_number():
    # Test number validation
    validate_param_rule("age", 25, {"type": "number"})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("age", "25", {"type": "number"})
    assert "type" in str(exc.value)
    
    # Test min
    validate_param_rule("age", 18, {"type": "number", "min": 18})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("age", 17, {"type": "number", "min": 18})
    assert "greater than or equal to" in str(exc.value)
    
    # Test max
    validate_param_rule("age", 65, {"type": "number", "max": 65})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("age", 66, {"type": "number", "max": 65})
    assert "less than or equal to" in str(exc.value)
    
    # Test gt
    validate_param_rule("price", 10.1, {"type": "number", "gt": 10})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("price", 10, {"type": "number", "gt": 10})
    assert "greater than" in str(exc.value)
    
    # Test lt
    validate_param_rule("price", 9.9, {"type": "number", "lt": 10})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("price", 10, {"type": "number", "lt": 10})
    assert "less than" in str(exc.value)
    
    # Test gte and lte
    validate_param_rule("count", 5, {"type": "number", "gte": 5, "lte": 10})
    validate_param_rule("count", 10, {"type": "number", "gte": 5, "lte": 10})
    
    with pytest.raises(ValidationError):
        validate_param_rule("count", 4, {"type": "number", "gte": 5, "lte": 10})
    
    with pytest.raises(ValidationError):
        validate_param_rule("count", 11, {"type": "number", "gte": 5, "lte": 10})


def test_validate_param_rule_array():
    # Test array validation
    validate_param_rule("tags", ["a", "b", "c"], {"type": "array"})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("tags", "not_an_array", {"type": "array"})
    assert "type" in str(exc.value)
    
    # Test minItems
    validate_param_rule("tags", ["a", "b"], {"type": "array", "minItems": 2})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("tags", ["a"], {"type": "array", "minItems": 2})
    assert "minimum" in str(exc.value)
    
    # Test maxItems
    validate_param_rule("tags", ["a", "b"], {"type": "array", "maxItems": 2})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("tags", ["a", "b", "c"], {"type": "array", "maxItems": 2})
    assert "maximum" in str(exc.value)
    
    # Test items validation
    validate_param_rule("numbers", [1, 2, 3], {"type": "array", "items": {"type": "number"}})
    
    with pytest.raises(ValidationError):
        validate_param_rule("numbers", [1, "2", 3], {"type": "array", "items": {"type": "number"}})


def test_validate_param_rule_enum():
    # Test enum validation
    validate_param_rule("status", "active", {"type": "string", "enum": ["active", "inactive", "pending"]})
    
    with pytest.raises(ValidationError) as exc:
        validate_param_rule("status", "deleted", {"type": "string", "enum": ["active", "inactive", "pending"]})
    assert "must be one of" in str(exc.value)
    
    # Enum works with other types too
    validate_param_rule("code", 200, {"type": "number", "enum": [200, 404, 500]})
    
    with pytest.raises(ValidationError):
        validate_param_rule("code", 201, {"type": "number", "enum": [200, 404, 500]})


def test_validate_params_with_list_schema():
    # Test list schema (required params)
    validate_params({"name": "John", "email": "john@example.com"}, ["name", "email"])
    
    with pytest.raises(ValidationError) as exc:
        validate_params({"name": "John"}, ["name", "email"])
    assert "required" in str(exc.value)


def test_validate_params_with_dict_schema():
    # Test dict schema
    schema = {
        "name": {"type": "string", "required": True},
        "age": {"type": "number", "gte": 0},
        "role": {"type": "string", "enum": ["admin", "user"]}
    }
    
    validate_params({
        "name": "John",
        "age": 30,
        "role": "admin"
    }, schema)
    
    # Missing required param
    with pytest.raises(ValidationError):
        validate_params({"age": 30}, schema)
    
    # Invalid type
    with pytest.raises(ValidationError):
        validate_params({"name": "John", "age": "30"}, schema)
    
    # Invalid enum value
    with pytest.raises(ValidationError):
        validate_params({"name": "John", "role": "superadmin"}, schema)


def test_validate_params_short_syntax():
    # Test short syntax for schema
    schema = {
        "name": "string",
        "age": "number",
        "active": "boolean"
    }
    
    validate_params({
        "name": "John",
        "age": 30,
        "active": True
    }, schema)
    
    with pytest.raises(ValidationError):
        validate_params({"name": "John", "age": "30"}, schema)

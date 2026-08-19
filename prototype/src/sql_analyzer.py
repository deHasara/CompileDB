import ast
import re
from enum import Enum
from typing import List, Tuple, Union, Dict
from sql_parser import parse
from pyparsing import ParseResults
import logging

class EntityType(Enum):
    REGULAR = 'REGULAR'
    WEAK = 'WEAK'
    SUBCLASS = 'SUBCLASS'

#####################################
######## CREATE RELATIONSHIP
######################################
def analyze_attribute(attr):
    is_primary_key = 'PRIMARY KEY' in list(attr)
    is_discriminator = 'DISCRIMINATOR' in list(attr)
    is_multivalued = (len(attr) == 3 and attr[2] == '[]')
    sub_attributes = []
    if attr[1] == 'COMPOSITE':
        for i in range(3, len(attr)-1):
            sub_attributes.append({'attr_name': attr[i][0], 'attr_type': attr[i][1]})
    attr_name = attr[0]
    attr_type = attr[1]
    return {
        'attr_name': attr_name,
        'attr_type': attr_type,
        'is_primary_key': is_primary_key,
        'is_discriminator': is_discriminator,
        'is_multivalued': is_multivalued,
        'sub_attributes': sub_attributes
    }

# Function to convert ParseResults to the desired dictionary format
def convert_parse_results_relationship(parse_results):
    # Extract table name
    table_name = parse_results.table_name[0]

    # Extract and format attributes
    attributes = [analyze_attribute(attr) for attr in parse_results.attributes]

    # Helper function to process entity modifiers
    def process_entity(entity_name, modifier):
        cardinality = True if modifier.get('cardinality', 'ONE') == 'ONE' else False#True for one False for many
        participation = True if modifier.get('participation', 'TOTAL') == 'TOTAL' else False
        role_info = list(modifier.get('role', []))
        if role_info:
            role_name = role_info[0]
        else:
            role_name = None
        return {'name': entity_name, 'one': cardinality, 'total': participation, 'role': role_name}

    # Process entity1
    entity1 = process_entity(parse_results.entity1[0], parse_results.entity1_modifier)

    # Process entity2
    entity2 = process_entity(parse_results.entity2[0], parse_results.entity2_modifier)

    # Construct the final dictionary
    result = {
        'table_name': table_name,
        'entity1': entity1,
        'entity2': entity2,
        'attributes': attributes
    }

    return result

#####################################
######## CREATE ENTITY
######################################

def convert_entity_parse_results(parse_results) -> Dict[str, Union[str, EntityType, List[Tuple[str, str, bool]]]]:
    result = {}

    # Determine entity type
    if  'WEAK' in list(parse_results):
        result['entity_type'] = EntityType.WEAK
    elif 'SUBCLASS OF' in list(parse_results):
        result['entity_type'] = EntityType.SUBCLASS
        result['total'] = True if parse_results.get('participation', 'TOTAL') == 'TOTAL' else False #if all subclasses participation partial -> then parent need to exist as a table, if all total -> parent can have the option to not have a table
    else:
        result['entity_type'] = EntityType.REGULAR

    # Extract table name
    result['table_name'] = parse_results.table_name[0]

    # Extract parent entity for weak and subclass entities
    if result['entity_type'] in [EntityType.WEAK, EntityType.SUBCLASS]:
        result['parent_entity'] = parse_results.parent_entity[0]

    # Process attributes
    result['attributes'] = [analyze_attribute(attr) for attr in parse_results.attributes]


    return result

#####################################
######## INSERT STATEMENT
######################################
def analyze_value(value):
    if isinstance(value, str):
        return value
    elif isinstance(value, (int, float)):
        return value
    elif isinstance(value, ParseResults):
        if value[0] == '(' and value[-1] == ')':
            return tuple(analyze_values(value[1:-1]))
        elif value[0] == '[' and value[-1] == ']':
            return analyze_values(value[1:-1])
    assert False

def analyze_values(values):
    return [analyze_value(v) for v in values]

def analyze_insert(parsed_insert):
    table_name = list(parsed_insert['table_name'])[0]
    values = parsed_insert['values'][1:-1]  # Remove outer parentheses
    analyzed_values = analyze_values(values)
    return {
        'table_name': table_name,
        'values': analyzed_values
    }

#####################################
######## ALTER
######################################
def analyze_alter(p):
    return None

#####################################
######## SELECT
######################################
def analyze_select(p):
    lp = list(p)
    return {'table_name': lp[3]}


#######################
######### OVERALL
#######################
def parse_and_analyze(s):
    #logging.debug(f"Parsing: {s}")
    p = parse(s)
    #logging.debug(f"Result: {p}")
    lp = list(p)
    if 'CREATE' in lp and 'ENTITY' in lp:
        return convert_entity_parse_results(p)
    elif 'CREATE RELATIONSHIP' in lp:
        return convert_parse_results_relationship(p)
    elif 'INSERT INTO' in lp:
        return analyze_insert(p)
    elif 'ALTER' in lp:
        return analyze_alter(p)
    elif 'SELECT' in lp:
        return analyze_select(p)
    else:
        assert False

#added new parse for insert stmt
"""
def new_parse(stmt):
    match = re.match(r"INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.*)\)", stmt)
    if match:
        relation = match.group(1)
        value_str = match.group(2)

        # Safely evaluate as Python tuple
        values = list(ast.literal_eval(f"({value_str})"))
        return {
            'table_name': relation,
            'values': values
        }
"""



INSERT_PATTERN = re.compile(
    r"^\s*INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)\s+"
    r"VALUES\s*\((.*)\)\s*;?\s*$",
    re.IGNORECASE | re.DOTALL,
    )

SQL_CONSTANT_PATTERN = re.compile(
    r"\b(NULL|TRUE|FALSE)\b",
    re.IGNORECASE,
)


def _translate_sql_constants(text):
    replacements = {
        "NULL": "None",
        "TRUE": "True",
        "FALSE": "False",
    }

    return SQL_CONSTANT_PATTERN.sub(
        lambda match: replacements[match.group(1).upper()],
        text,
    )


def _sql_values_to_python(value_sql):
    """Translate generated SQL values into safe Python literals."""

    translated = []
    outside_string = []
    position = 0

    while position < len(value_sql):
        if value_sql[position] != "'":
            outside_string.append(value_sql[position])
            position += 1
            continue

        translated.append(
            _translate_sql_constants("".join(outside_string))
        )
        outside_string.clear()

        position += 1
        string_value = []

        while position < len(value_sql):
            character = value_sql[position]

            if character != "'":
                string_value.append(character)
                position += 1
            elif (
                    position + 1 < len(value_sql)
                    and value_sql[position + 1] == "'"
            ):
                # SQL escape: O''Brien -> O'Brien
                string_value.append("'")
                position += 2
            else:
                position += 1
                break
        else:
            raise ValueError("unterminated SQL string literal")

        translated.append(repr("".join(string_value)))

    translated.append(
        _translate_sql_constants("".join(outside_string))
    )

    python_values = "".join(translated)

    try:
        # The trailing comma makes the outer value collection a tuple,
        # including INSERT statements containing only one value.
        parsed = ast.literal_eval(f"({python_values},)")
    except (SyntaxError, ValueError) as error:
        raise ValueError(
            f"could not parse INSERT values: {value_sql!r}"
        ) from error

    return list(parsed)


def new_parse(stmt):
    match = INSERT_PATTERN.match(stmt)

    if not match:
        raise ValueError(
            f"unsupported INSERT statement: {stmt[:160]!r}"
        )

    return {
        "table_name": match.group(1),
        "values": _sql_values_to_python(match.group(2)),
    }


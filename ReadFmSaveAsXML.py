import json
import xmltodict

fm_xml_file_path = "assets.xml"
output_json_file_path = "relationship-schema.json"

with open(fm_xml_file_path, 'r', encoding='utf-8') as xml_file:
    xml_dict = xmltodict.parse(xml_file.read())

try:
    add_actions = xml_dict.get('FMSaveAsXML', {}).get('Structure', {}).get('AddAction', {})
    relationships = add_actions.get('RelationshipCatalog', {}).get('Relationship', [])

    field_catalogs = add_actions.get('FieldsForTables', {}).get('FieldCatalog', [])

    if not isinstance(relationships, list):
        relationships = [relationships]

    if not isinstance(field_catalogs, list):
        field_catalogs = [field_catalogs]

    formatted_relationships = []
    for rel in relationships:
        predicate = rel.get('JoinPredicateList', {}).get('JoinPredicate', {})
        left_ref = predicate.get('LeftField', {}).get('FieldReference', [])
        right_ref = predicate.get('RightField', {}).get('FieldReference', [])

        is_left_field_unique = "False"
        left_table_name = left_ref.get('TableOccurrenceReference', {}).get('@name')
        left_field_name = left_ref.get('@name'),
        if isinstance(left_field_name, tuple):
             left_field_name = left_field_name[0]
        
        is_right_field_unique = "False"
        right_table_name = right_ref.get('TableOccurrenceReference', {}).get('@name')
        right_field_name = right_ref.get('@name'),
        if isinstance(right_field_name, tuple):
             right_field_name = right_field_name[0]

        for catalog in field_catalogs:
            fields = catalog.get('ObjectList', {}).get('Field', {})
            table = catalog.get('BaseTableReference', {})
            table_name = table.get('@name')
            if left_table_name == table_name:
                for field in fields:
                    if (left_field_name == field.get('@name')):
                        is_left_field_unique = field.get('Validation', {}).get('@unique')
                        break
            if right_table_name == table_name:
                for field in fields:
                    if (right_field_name == field.get('@name')):
                        is_right_field_unique = field.get('Validation', {}).get('@unique')
                        break
        rel_data = {
            # "Id": rel.get('@id'),
            "LeftTable": left_table_name,
            "LeftField":  left_field_name,
            "IsLeftFieldUnique":  is_left_field_unique,
            "RightTable": right_table_name,
            "RightField":  right_field_name,
            "IsRightFieldUnique":  is_right_field_unique,
        }
        formatted_relationships.append(rel_data)


    with open(output_json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(formatted_relationships, json_file, indent=4)

except Exception as e:
    print(f"Error parsing the xml file: {e}")

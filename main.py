import argparse
import json
import arcpy


"""
TODO: ADD SUPPORT FOR MORE COMPARISONS
TODO: ADD SUPPORT FOR TABLE AND FC COMPARISON
"""


def check_type(data_obj:str):

    '''
    Checks the type of data object being compared

    @input --> Str --> A geodatabase string path to either a featureclass or a table 
    
    @output --> Dict --> Dict with name of data object and the data type
    '''

    desc_obj = arcpy.Describe(data_obj)
    name = desc_obj.baseName # Get name
    # Check if featureType attribute exists, if so it is a fc
    if hasattr(desc_obj, 'featureType'):
        return {"data_name" : name, "data_type" : "Featureclass"}
    # Else assume it is a table
    else:
        return {"data_name" : name, "data_type" : "Table"}

def get_fields(data_obj: str, data_type: str, name: str):

    '''
    Gets the fields from a table or a feature class. Additionally, gets the name, the type, the length, the precision, the scale and the domain.

    @input data_obj --> Str --> A geodatabase string path to either a featureclass or a table 
    @input data_type --> Str --> String containing the type of the data
    @input name --> Str --> String containing the name of the data

    @output data_dict_rep --> List --> A list containing dictionaries for each field which contains name, type, length, precision, scale and domain of each field

    '''
    # Declares the dict that represents a feature class or a table
    data_dic_rep = {"name" : name, "type": data_type, 'fields': []}

    # Find fields and populate the field metadata
    fobjs = arcpy.ListFields(data_obj)
    for f in fobjs:
        field = {
            'name': f.baseName,
            'type': f.type,
            'length': f.length,
            'precision': f.precision,
            'scale': f.scale,
            'domain': f.domain
        }
        # Append field metadat
        data_dic_rep['fields'].append(field)
    return data_dic_rep # Return dict representation

def find_dict_from_value(dict_list: list, dict_key: str, dict_value: str):

    '''
    Generic function to search for an instance of a dict value in a list of dictionaries. Returns the dict that contains the desired value.
    
    @input dict_list --> List --> A list of dictionaries
    @input dict_key --> Str --> A string containing the dict key that is of interest
    @input dict_list --> Str --> A string containing the search value of interest

    @output --> Dict --> A dictionary containing the value that was searched for by the user

    '''

    return next((item for item in dict_list if item[dict_key] == dict_value), None)


def filter_unwanted_fields(parent_field, fields_to_ignore, ignore_cases):

    '''
    Logic to filter out fields that should not be compared in order to not crowd output file

    @input parent_field --> Str --> Name of the parent field
    @input fields_to_ignore --> List --> A list containing the specified fields to ignore
    @input ignore_cases --> Bool --> A boolean containing the desire to ignore cases or not

    @output --> Bool --> True specifies the field will be skipped, false specifies the process will continue

    '''

    if ignore_cases == True:
        fields_to_ignore = [x.lower() for x in fields_to_ignore]
        parent_field = parent_field.lower()
    if fields_to_ignore == parent_field:
        return True
    else:
        return False


def compare_values_for_each_field(parent, child, comp_file, fields_to_ignore, ignore_cases):

    '''
    Contains the main chunk of logic to compare the two datasets and exports the detected changes as an output text file

    @input parent --> Dict --> The dict representation of the parent dataset containing name and field info
    @input child --> Dict --> The dict representation of the child dataset containing name and field info
    @input comp_file --> Str --> A string containing the file path to where the comparison text file is written to
    @input fields_to_ignore --> List --> A list containing the specified fields to ignore
    @input ignore_cases --> Bool --> A boolean containing the desire to ignore cases or not
    '''

    # Assemble list of field names for the corresponding child data
    child_field_list = []
    for field in child["fields"]:
        child_field_list.append(field["name"])

    # Write changes to text file
    with open(comp_file, 'w') as compare_text:
        
        # Loop through all parent fields
        for field in parent["fields"]:
            
            # Checks for fields to be ignored
            if filter_unwanted_fields(field, fields_to_ignore, ignore_cases) == True:
                continue
            
            # Sets default flag booleans
            type_match = True
            length_match = True
            field_match = False

            # Stamp each new field in the output text file
            compare_text.write(field["name"] + "\n")
            compare_text.write("------------------------------------------------------\n")
            
            # Checks if parent field name is in child field name
            if field["name"] in child_field_list:
                print("Found field match: {}".format(field["name"]))
                field_match = True
                matching_child = find_dict_from_value(child["fields"], "name", field["name"]) # Find correspdonding child dict
                
                # Logic to check if the field types match
                if field["type"] == matching_child["type"]:
                    pass
                else:
                    type_match = False
                    type_d = {"parent" : field["type"], "child" : matching_child["type"]} 
                    compare_text.write("Type mismatch found in {}. The parent has a type of {} and the child has a type of {}\n".format(field["name"], field["type"], matching_child["type"]))

                # Logic to check if the field lengths match
                if field["length"] == matching_child["length"]:
                    pass
                else:
                    length_match = False
                    length_d = {"parent" : field["length"], "child" : matching_child["length"]}
                    compare_text.write("Length mismatch found in {}. The parent has a length of {} and the length has a type of {}\n".format(field["name"], field["length"], matching_child["length"]))
            
            # Logic if there is no field name match
            else:
                print("{} not found in child...".format(field["name"]))
                compare_text.write("{} not found in child\n".format(field["name"]))
            if type_match and length_match and field_match == True:
                compare_text.write("No issues detected\n")
            
            # Stamp the end of the field
            compare_text.write("------------------------------------------------------\n\n\n")

def main():

    # Parse config file
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, help="File path to the config file", required=True)
    parser.add_argument('--parent', type=str, help="File path to parent data", required=True)
    parser.add_argument('--child', type=str, help="File path to child data", required=True)
    args = parser.parse_args()
    parent_obj = args.parent
    child_obj = args.child
    print("Parsing arguments...")

    # Open config file and populate
    with open(args.config, "r") as config:
        print("Parsing config file...")
        config  = json.load(config)
        comp_file = config["output_loc"]
        fields_to_ignore = config["fields_to_ignore"]["ignore_list"]
        ignore_cases = config["fields_to_ignore"]["ignore_cases"]

    # Check field types
    parent_meta = check_type(parent_obj)
    child_meta = check_type(child_obj)

    # Get fields objects for each data obj
    parent_fields_info = get_fields(parent_obj, parent_meta["data_type"], parent_meta["data_name"])
    child_fields_info = get_fields(child_obj, child_meta["data_type"], child_meta["data_name"])

    # Compare the fields between the two
    compare_values_for_each_field(parent_fields_info, child_fields_info, comp_file, fields_to_ignore, ignore_cases)

if __name__ == "__main__":
    main()
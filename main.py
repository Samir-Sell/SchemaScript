import argparse
import json
import arcpy



def check_type(data_obj:str):
    desc_obj = arcpy.Describe(data_obj)
    name = desc_obj.baseName # Get name
    # Check if featureType attribute exists, if so it is a fc
    if hasattr(desc_obj, 'featureType'):
        return {"data_name" : name, "data_type" : "Featureclass"}
    # Else it is a table
    else:
        return {"data_name" : name, "data_type" : "Table"}


def get_fields(data_obj, data_type, name):
    data_dic_rep = {"name" : name, "type": data_type, 'fields': []}
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
        data_dic_rep['fields'].append(field)
    return data_dic_rep


def find_dict_from_value(dict_list, dict_key, dict_value):
    return next((item for item in dict_list if item[dict_key] == dict_value), None)



def compare_values_for_each_field(parent, child, comp_file):

    # Assemble list of field names
    child_field_list = []
    for field in child["fields"]:
        child_field_list.append(field["name"])

    with open(comp_file, 'w') as compare_text:
        
        for field in parent["fields"]:
            type_match = True
            length_match = True
            field_match = False
            compare_text.write(field["name"] + "\n")
            compare_text.write("------------------------------------------------------\n")
            if field["name"] in child_field_list:
                print("Found field match: {}".format(field["name"]))
                field_match = True
                matching_child = find_dict_from_value(child["fields"], "name", field["name"])
                if field["type"] == matching_child["type"]:
                    pass
                else:
                    type_match = False
                    type_d = {"parent" : field["type"], "child" : matching_child["type"]} 
                    compare_text.write("Type mismatch found in {}. The parent has a type of {} and the child has a type of {}\n".format(field["name"], field["type"], matching_child["type"]))

                if field["length"] == matching_child["length"]:
                    pass
                else:
                    length_match = False
                    length_d = {"parent" : field["length"], "child" : matching_child["length"]}
                    compare_text.write("Length mismatch found in {}. The parent has a length of {} and the length has a type of {}\n".format(field["name"], field["length"], matching_child["length"]))

            else:
                print("{} not found in child...".format(field["name"]))
                compare_text.write("{} not found in child\n".format(field["name"]))
            if type_match and length_match and field_match == True:
                compare_text.write("No issues detected\n")
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

    # Open config file
    with open(args.config, "r") as config:
        print("Parsing config file...")
        config  = json.load(config)
        comp_file = config["output_loc"]

    # Check field types
    parent_meta = check_type(parent_obj)
    child_meta = check_type(child_obj)

    # Get fields objects for each data obj
    parent_fields_info = get_fields(parent_obj, parent_meta["data_type"], parent_meta["data_name"])
    child_fields_info = get_fields(child_obj, child_meta["data_type"], child_meta["data_name"])


    compare_values_for_each_field(parent_fields_info, child_fields_info, comp_file)




if __name__ == "__main__":
    main()
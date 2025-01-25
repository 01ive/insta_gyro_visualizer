import logging
import sys
import os

def process_json_file(json_file):
    logging.info(f"Reading model from {json_file}")
    with open(json_file, 'r') as f:
        model_json = f.read()
    
    base_name = os.path.basename(json_file).split('.')[0]

    text = "const " + base_name + " = " + model_json + ";"

    js_file_name = json_file.split('.')[0] + '.js'
    logging.info("Writing model to {}".format(js_file_name))
    with open(js_file_name, 'w') as f:
        f.write(text)

def process_models(json_file_name):
    if not os.path.exists(json_file_name):
        logging.error(f"File {json_file_name} does not exist.")
        sys.exit(1)
    elif os.path.isdir(json_file_name):
        logging.info(f"Procesing all files in directory {json_file_name}")
        for file in os.listdir(json_file_name):
            if file.endswith('.json'):
                process_json_file(os.path.join(json_file_name, file))
    else:       
        process_json_file(json_file_name)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    json_file_name = sys.argv[1]

    process_models(json_file_name)
   